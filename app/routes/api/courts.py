"""
API Courts Module

Court availability for authenticated users (web and mobile).
"""

from datetime import date, time, timedelta
from flask import request, jsonify, current_app
from flask_login import current_user, login_user
import jwt
from sqlalchemy.orm import joinedload

from app.models import Court, Reservation, Block, Member
from app.services.reservation_service import ReservationService
from app.services.block_service import BlockService
from app.services.validation_service import ValidationService
from app.decorators.auth import jwt_or_session_required
from app import limiter
from . import bp


def _handle_jwt_auth():
    """Check for JWT Bearer token or httpOnly cookie and log in user if valid.

    Priority:
    1. Authorization: Bearer <token> header (mobile apps)
    2. jwt_token cookie (web app)
    """
    token = None

    # First, check Authorization header (mobile apps)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    else:
        # Fall back to httpOnly cookie (web app)
        token = request.cookies.get('jwt_token')

    if not token:
        return

    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=[current_app.config['JWT_ALGORITHM']]
        )
        member = Member.query.get(payload['user_id'])
        if member and member.is_active:
            login_user(member, remember=False)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        pass


def _build_day_availability(courts, reservation_map, block_map, suspended_map, current_time):
    """Build sparse availability data for a single day.

    Args:
        courts: List of Court objects
        reservation_map: Dict of (court_id, hour) -> Reservation for this date
        block_map: Dict of (court_id, hour) -> Block for this date
        suspended_map: Dict of (court_id, hour) -> suspended Reservation for this date
        current_time: Current Berlin time

    Returns:
        List of court data dicts with occupied slots
    """
    courts_data = []
    for court in courts:
        court_data = {
            'court_id': court.id,
            'court_number': court.number,
            'occupied': []
        }

        for hour in range(8, 22):
            slot_time = time(hour, 0)
            key = (court.id, hour)

            if key in block_map:
                blocks_at_slot = block_map[key]
                # Separate temp and regular blocks
                temp_blocks = [b for b in blocks_at_slot if b.is_temporary_block]
                regular_blocks = [b for b in blocks_at_slot if not b.is_temporary_block]

                # Prioritize temp blocks (they suspend/overlay regular blocks)
                if temp_blocks:
                    block = temp_blocks[0]
                    block_details = {
                        'reason': block.reason_obj.name if block.reason_obj else 'Unbekannt',
                        'details': block.details if block.details else '',
                        'block_id': block.id,
                        'is_temporary': True
                    }

                    # Include underlying regular block info if exists
                    if regular_blocks:
                        underlying = regular_blocks[0]
                        block_details['underlying_block'] = {
                            'reason': underlying.reason_obj.name if underlying.reason_obj else 'Unbekannt',
                            'details': underlying.details if underlying.details else '',
                            'block_id': underlying.id
                        }

                    # Include suspended reservation info
                    if key in suspended_map and current_user.is_authenticated:
                        suspended_res = suspended_map[key]
                        block_details['suspended_reservation'] = {
                            'booked_for': f"{suspended_res.booked_for.firstname} {suspended_res.booked_for.lastname}",
                            'booked_for_id': suspended_res.booked_for_id,
                            'booked_for_has_profile_picture': suspended_res.booked_for.has_profile_picture,
                            'booked_for_profile_picture_version': suspended_res.booked_for.profile_picture_version,
                            'booked_by_id': suspended_res.booked_by_id,
                            'reservation_id': suspended_res.id,
                            'is_short_notice': suspended_res.is_short_notice,
                            'can_cancel': ValidationService.get_cancellation_eligibility(
                                suspended_res, current_user.id, current_time
                            )
                        }

                    court_data['occupied'].append({
                        'time': slot_time.strftime('%H:%M'),
                        'status': 'blocked_temporary',
                        'details': block_details
                    })
                else:
                    # No temp block, show regular block
                    block = regular_blocks[0] if regular_blocks else blocks_at_slot[0]
                    block_details = {
                        'reason': block.reason_obj.name if block.reason_obj else 'Unbekannt',
                        'details': block.details if block.details else '',
                        'block_id': block.id,
                        'is_temporary': False
                    }

                    court_data['occupied'].append({
                        'time': slot_time.strftime('%H:%M'),
                        'status': 'blocked',
                        'details': block_details
                    })
            elif key in reservation_map:
                reservation = reservation_map[key]
                slot_data = {
                    'time': slot_time.strftime('%H:%M'),
                    'status': 'short_notice' if reservation.is_short_notice else 'reserved',
                    'details': None
                }

                if current_user.is_authenticated:
                    slot_data['details'] = {
                        'booked_for': f"{reservation.booked_for.firstname} {reservation.booked_for.lastname}",
                        'booked_for_id': reservation.booked_for_id,
                        'booked_for_has_profile_picture': reservation.booked_for.has_profile_picture,
                        'booked_for_profile_picture_version': reservation.booked_for.profile_picture_version,
                        'booked_by': f"{reservation.booked_by.firstname} {reservation.booked_by.lastname}",
                        'booked_by_id': reservation.booked_by_id,
                        'booked_by_has_profile_picture': reservation.booked_by.has_profile_picture,
                        'booked_by_profile_picture_version': reservation.booked_by.profile_picture_version,
                        'reservation_id': reservation.id,
                        'is_short_notice': reservation.is_short_notice,
                        'can_cancel': ValidationService.get_cancellation_eligibility(
                            reservation, current_user.id, current_time
                        )
                    }
                else:
                    slot_data['status'] = 'reserved'
                    slot_data['details'] = None

                court_data['occupied'].append(slot_data)

        courts_data.append(court_data)

    return courts_data


def _build_lookup_maps(query_date, reservations, blocks, suspended_reservations, current_time):
    """Build O(1) lookup maps for reservations, blocks, and suspended reservations.

    Args:
        query_date: The date being queried
        reservations: List of Reservation objects for this date
        blocks: List of Block objects for this date
        suspended_reservations: List of suspended Reservation objects for this date
        current_time: Current Berlin time

    Returns:
        Tuple of (reservation_map, block_map, suspended_map)
    """
    reservation_map = {}
    is_past_or_current_date = query_date <= current_time.date()
    for reservation in reservations:
        if reservation.status == 'active':
            if is_past_or_current_date:
                key = (reservation.court_id, reservation.start_time.hour)
                reservation_map[key] = reservation
            else:
                is_active = ReservationService.is_reservation_currently_active(
                    reservation, current_time
                )
                if is_active:
                    key = (reservation.court_id, reservation.start_time.hour)
                    reservation_map[key] = reservation

    # Store lists of blocks per slot to handle overlapping temp/regular blocks
    block_map = {}  # (court_id, hour) -> list of Block objects
    for block in blocks:
        for hour in range(block.start_time.hour, block.end_time.hour):
            key = (block.court_id, hour)
            if key not in block_map:
                block_map[key] = []
            block_map[key].append(block)

    suspended_map = {}
    for reservation in suspended_reservations:
        key = (reservation.court_id, reservation.start_time.hour)
        suspended_map[key] = reservation

    return reservation_map, block_map, suspended_map


@bp.route('/courts/availability', methods=['GET'])
def get_availability():
    """Get court availability for a specific date (sparse format).

    Returns only occupied slots (reservations and blocks) to minimize
    bandwidth. Available slots are implied by absence from the response.

    Query params:
        date: Date in YYYY-MM-DD format (default: today)
    """
    from app.utils.timezone_utils import get_current_berlin_time

    date_str = request.args.get('date', date.today().isoformat())
    try:
        query_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datumsformat'}), 400

    _handle_jwt_auth()

    current_time = get_current_berlin_time()
    courts = Court.query.order_by(Court.number).all()
    reservations = ReservationService.get_reservations_by_date(query_date)
    blocks = BlockService.get_blocks_by_date(query_date)
    suspended_reservations = Reservation.query.options(
        joinedload(Reservation.booked_for)
    ).filter(
        Reservation.date == query_date,
        Reservation.status == 'suspended'
    ).all()

    reservation_map, block_map, suspended_map = _build_lookup_maps(
        query_date, reservations, blocks, suspended_reservations, current_time
    )
    courts_data = _build_day_availability(
        courts, reservation_map, block_map, suspended_map, current_time
    )

    return jsonify({
        'date': date_str,
        'current_hour': current_time.hour,
        'courts': courts_data,
        'metadata': {
            'generated_at': current_time.isoformat(),
            'timezone': 'Europe/Berlin'
        }
    })


@bp.route('/courts/availability/range', methods=['GET'])
@limiter.limit("60 per minute")
def get_availability_range():
    """Get court availability for a date range (sparse format).

    Fetches multiple days in a single request for client-side caching.

    Query params:
        start: Start date in YYYY-MM-DD format (required)
        days: Number of days to fetch, 1-30 (required)

    Response format:
        {
            "range": {"start": "2026-01-20", "end": "2026-01-26", "days_requested": 7},
            "days": {
                "2026-01-20": {"current_hour": 10, "courts": [...]},
                "2026-01-21": {"current_hour": null, "courts": [...]}
            },
            "metadata": {...}
        }
    """
    from app.utils.timezone_utils import get_current_berlin_time

    start_str = request.args.get('start')
    days_str = request.args.get('days')

    if not start_str or not days_str:
        return jsonify({'error': 'Parameter start und days sind erforderlich'}), 400

    try:
        start_date = date.fromisoformat(start_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datumsformat für start'}), 400

    try:
        num_days = int(days_str)
        if num_days < 1 or num_days > 30:
            raise ValueError()
    except ValueError:
        return jsonify({'error': 'days muss eine Zahl zwischen 1 und 30 sein'}), 400

    _handle_jwt_auth()

    current_time = get_current_berlin_time()
    end_date = start_date + timedelta(days=num_days - 1)

    courts = Court.query.order_by(Court.number).all()

    # Batch fetch all data for the date range
    reservations = Reservation.query.options(
        joinedload(Reservation.booked_for),
        joinedload(Reservation.booked_by),
        joinedload(Reservation.court)
    ).filter(
        Reservation.date.between(start_date, end_date),
        Reservation.status == 'active'
    ).all()

    blocks = Block.query.options(
        joinedload(Block.reason_obj),
        joinedload(Block.court)
    ).filter(
        Block.date.between(start_date, end_date)
    ).all()

    suspended_reservations = Reservation.query.options(
        joinedload(Reservation.booked_for)
    ).filter(
        Reservation.date.between(start_date, end_date),
        Reservation.status == 'suspended'
    ).all()

    # Group data by date
    reservations_by_date = {}
    for res in reservations:
        reservations_by_date.setdefault(res.date, []).append(res)

    blocks_by_date = {}
    for block in blocks:
        blocks_by_date.setdefault(block.date, []).append(block)

    suspended_by_date = {}
    for res in suspended_reservations:
        suspended_by_date.setdefault(res.date, []).append(res)

    # Build response for each day
    days_data = {}
    current_date = start_date
    today = current_time.date()

    while current_date <= end_date:
        date_reservations = reservations_by_date.get(current_date, [])
        date_blocks = blocks_by_date.get(current_date, [])
        date_suspended = suspended_by_date.get(current_date, [])

        reservation_map, block_map, suspended_map = _build_lookup_maps(
            current_date, date_reservations, date_blocks, date_suspended, current_time
        )
        courts_data = _build_day_availability(
            courts, reservation_map, block_map, suspended_map, current_time
        )

        days_data[current_date.isoformat()] = {
            'current_hour': current_time.hour if current_date == today else None,
            'courts': courts_data
        }

        current_date += timedelta(days=1)

    return jsonify({
        'range': {
            'start': start_str,
            'end': end_date.isoformat(),
            'days_requested': num_days
        },
        'days': days_data,
        'metadata': {
            'generated_at': current_time.isoformat(),
            'timezone': 'Europe/Berlin',
            'cache_hint_seconds': 30
        }
    })
