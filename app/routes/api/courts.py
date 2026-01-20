"""
API Courts Module

Court availability for authenticated users (web and mobile).
"""

from datetime import date, time
from flask import request, jsonify, current_app
from flask_login import current_user, login_user
import jwt

from app.models import Court, Reservation
from app.services.reservation_service import ReservationService
from app.services.block_service import BlockService
from app.services.validation_service import ValidationService
from app.decorators.auth import jwt_or_session_required
from . import bp


@bp.route('/courts/availability', methods=['GET'])
def get_availability():
    """Get court availability for a specific date (sparse format).

    Returns only occupied slots (reservations and blocks) to minimize
    bandwidth. Available slots are implied by absence from the response.
    Client computes CSS classes and content from status/details.

    This endpoint is publicly accessible for viewing availability.
    Authenticated users see additional details like member names.

    Query params:
        date: Date in YYYY-MM-DD format (default: today)

    Response format:
        {
            "date": "YYYY-MM-DD",
            "current_hour": 10,
            "courts": [
                {
                    "court_id": 1,
                    "court_number": 1,
                    "occupied": [
                        {"time": "09:00", "status": "reserved", "details": {...}}
                    ]
                }
            ]
        }
    """
    from app.utils.timezone_utils import get_current_berlin_time

    date_str = request.args.get('date', date.today().isoformat())
    try:
        query_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datumsformat'}), 400

    # Check for JWT Bearer token authentication (for mobile app)
    # This allows mobile users to see member names in availability view
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            from app.models import Member
            member = Member.query.get(payload['user_id'])
            if member and member.is_active:
                login_user(member, remember=False)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass  # Invalid/expired token - continue as anonymous

    current_time = get_current_berlin_time()
    courts = Court.query.order_by(Court.number).all()
    reservations = ReservationService.get_reservations_by_date(query_date)
    blocks = BlockService.get_blocks_by_date(query_date)

    # Build lookup maps for O(1) access
    # Key: (court_id, hour) -> reservation or block
    reservation_map = {}
    is_past_or_current_date = query_date <= current_time.date()
    for reservation in reservations:
        if reservation.status == 'active':
            # For past and current dates, show all reservations (including past time slots)
            # For future dates, only show currently active ones
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

    block_map = {}
    for block in blocks:
        # Blocks can span multiple hours
        for hour in range(block.start_time.hour, block.end_time.hour):
            key = (block.court_id, hour)
            block_map[key] = block

    # Build suspended reservation map for temporary blocks
    # Key: (court_id, hour) -> suspended reservation
    suspended_map = {}
    from sqlalchemy.orm import joinedload
    suspended_reservations = Reservation.query.options(
        joinedload(Reservation.booked_for)
    ).filter(
        Reservation.date == query_date,
        Reservation.status == 'suspended'
    ).all()
    for reservation in suspended_reservations:
        key = (reservation.court_id, reservation.start_time.hour)
        suspended_map[key] = reservation

    # Build sparse response - only include occupied slots
    courts_data = []
    for court in courts:
        court_data = {
            'court_id': court.id,
            'court_number': court.number,
            'occupied': []
        }

        # Check each hour slot (8-21)
        for hour in range(8, 22):
            slot_time = time(hour, 0)
            key = (court.id, hour)

            # Check for block first (blocks take priority)
            if key in block_map:
                block = block_map[key]
                block_details = {
                    'reason': block.reason_obj.name if block.reason_obj else 'Unbekannt',
                    'details': block.details if block.details else '',
                    'block_id': block.id,
                    'is_temporary': block.is_temporary_block
                }

                # For temporary blocks, include suspended reservation info if exists
                if block.is_temporary_block and key in suspended_map and current_user.is_authenticated:
                    suspended_res = suspended_map[key]
                    block_details['suspended_reservation'] = {
                        'booked_for': f"{suspended_res.booked_for.firstname} {suspended_res.booked_for.lastname}",
                        'booked_for_id': suspended_res.booked_for_id,
                        'booked_by_id': suspended_res.booked_by_id,
                        'reservation_id': suspended_res.id,
                        'is_short_notice': suspended_res.is_short_notice,
                        'can_cancel': ValidationService.get_cancellation_eligibility(
                            suspended_res, current_user.id, current_time
                        )
                    }

                court_data['occupied'].append({
                    'time': slot_time.strftime('%H:%M'),
                    'status': 'blocked_temporary' if block.is_temporary_block else 'blocked',
                    'details': block_details
                })
            # Check for reservation
            elif key in reservation_map:
                reservation = reservation_map[key]
                slot_data = {
                    'time': slot_time.strftime('%H:%M'),
                    'status': 'short_notice' if reservation.is_short_notice else 'reserved',
                    'details': None
                }

                # Only include member details for authenticated users
                if current_user.is_authenticated:
                    slot_data['details'] = {
                        'booked_for': f"{reservation.booked_for.firstname} {reservation.booked_for.lastname}",
                        'booked_for_id': reservation.booked_for_id,
                        'booked_by': f"{reservation.booked_by.firstname} {reservation.booked_by.lastname}",
                        'booked_by_id': reservation.booked_by_id,
                        'reservation_id': reservation.id,
                        'is_short_notice': reservation.is_short_notice,
                        'can_cancel': ValidationService.get_cancellation_eligibility(
                            reservation, current_user.id, current_time
                        )
                    }
                else:
                    # Anonymous users see slot is reserved but without member names
                    # Normalize short_notice to 'reserved' for anonymous users
                    slot_data['status'] = 'reserved'
                    slot_data['details'] = None

                court_data['occupied'].append(slot_data)

        courts_data.append(court_data)

    return jsonify({
        'date': date_str,
        'current_hour': current_time.hour,
        'courts': courts_data,
        'metadata': {
            'generated_at': current_time.isoformat(),
            'timezone': 'Europe/Berlin'
        }
    })
