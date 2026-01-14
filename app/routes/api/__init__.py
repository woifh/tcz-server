"""
API Routes Package

Mobile-first API endpoints with JWT authentication.
All routes return JSON and use Bearer token authentication.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.models import Reservation
from app.services.reservation_service import ReservationService
from app.decorators.auth import jwt_or_session_required
from app.utils.validators import (
    ValidationError,
    validate_date_format,
    validate_time_format,
    validate_integer,
    validate_uuid
)

# Create the main API blueprint
bp = Blueprint('api', __name__, url_prefix='/api')


# ----- Reservation Routes -----

@bp.route('/reservations/', methods=['GET'])
@jwt_or_session_required
def list_reservations():
    """List user's reservations.

    Query params:
        include_past: Include past reservations (default: false)
    """
    from app.utils.timezone_utils import get_current_berlin_time

    include_past = request.args.get('include_past', 'false').lower() == 'true'
    current_time = get_current_berlin_time()

    if include_past:
        all_reservations = Reservation.query.filter(
            (Reservation.booked_for_id == current_user.id) |
            (Reservation.booked_by_id == current_user.id),
            Reservation.status == 'active'
        ).order_by(Reservation.date.desc(), Reservation.start_time.desc()).all()
        reservations = all_reservations
    else:
        reservations = ReservationService.get_member_active_booking_sessions(
            current_user.id, include_short_notice=True, current_time=current_time,
            include_bookings_for_others=True
        )

    active_reservations = [r for r in reservations
                          if ReservationService.is_reservation_currently_active(r, current_time)]
    past_reservations = [r for r in reservations
                        if not ReservationService.is_reservation_currently_active(r, current_time)]

    my_active = [r for r in active_reservations if r.booked_for_id == current_user.id]
    regular_active = [r for r in my_active if not r.is_short_notice]
    short_notice_active = [r for r in my_active if r.is_short_notice]

    return jsonify({
        'current_time': current_time.isoformat(),
        'reservations': [r.to_dict() for r in reservations],
        'statistics': {
            'total_count': len(reservations),
            'active_count': len(active_reservations),
            'past_count': len(past_reservations),
            'regular_active_count': len(regular_active),
            'short_notice_active_count': len(short_notice_active)
        }
    })


@bp.route('/reservations/', methods=['POST'])
@jwt_or_session_required
def create_reservation():
    """Create a new reservation."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        try:
            court_id = validate_integer(data.get('court_id'), 'court_id', min_value=1, max_value=6)
            reservation_date = validate_date_format(data.get('date'), 'date')
            start_time = validate_time_format(data.get('start_time'), 'start_time')
            booked_for_id = validate_uuid(
                data.get('booked_for_id', current_user.id),
                'booked_for_id'
            )
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        booked_for_member = current_user if booked_for_id == current_user.id else None
        reservation, error = ReservationService.create_reservation(
            court_id=court_id,
            date=reservation_date,
            start_time=start_time,
            booked_for_id=booked_for_id,
            booked_by_id=current_user.id,
            booked_for_member=booked_for_member
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'Kurzfristige Buchung erfolgreich erstellt!' if reservation.is_short_notice else 'Buchung erfolgreich erstellt!',
            'reservation': reservation.to_dict()
        }), 201

    except Exception:
        return jsonify({'error': 'Ein Fehler ist aufgetreten'}), 500


@bp.route('/reservations/<int:id>', methods=['DELETE'])
@jwt_or_session_required
def delete_reservation(id):
    """Cancel a reservation."""
    try:
        reservation = Reservation.query.get_or_404(id)

        if (reservation.booked_for_id != current_user.id and
            reservation.booked_by_id != current_user.id):
            return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403

        success, error = ReservationService.cancel_reservation(id)

        if error:
            return jsonify({'error': error}), 400

        return jsonify({'message': 'Buchung erfolgreich storniert'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/reservations/status', methods=['GET'])
@jwt_or_session_required
def reservation_status():
    """Get reservation status and limits for current user."""
    from app.utils.timezone_utils import get_current_berlin_time

    current_time = get_current_berlin_time()

    active_regular = ReservationService.get_member_active_booking_sessions(
        current_user.id, include_short_notice=False, current_time=current_time
    )
    active_short_notice = ReservationService.get_member_active_short_notice_bookings(
        current_user.id, current_time=current_time
    )
    all_active = ReservationService.get_member_active_booking_sessions(
        current_user.id, include_short_notice=True, current_time=current_time
    )

    return jsonify({
        'current_time': current_time.isoformat(),
        'user_id': current_user.id,
        'limits': {
            'regular_reservations': {
                'limit': 2,
                'current': len(active_regular),
                'available': 2 - len(active_regular),
                'can_book': len(active_regular) < 2
            },
            'short_notice_bookings': {
                'limit': 1,
                'current': len(active_short_notice),
                'available': 1 - len(active_short_notice),
                'can_book': len(active_short_notice) < 1
            }
        },
        'active_reservations': {
            'total': len(all_active),
            'regular': len(active_regular),
            'short_notice': len(active_short_notice)
        }
    })


# Import sub-modules to register their routes
from . import members
from . import admin
from . import courts
