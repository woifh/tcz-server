"""
API Courts Module

Court availability for authenticated users (web and mobile).
"""

from datetime import date, time
from flask import request, jsonify
from flask_login import current_user

from app.models import Court
from app.services.reservation_service import ReservationService
from app.services.block_service import BlockService
from app.decorators.auth import jwt_or_session_required
from . import bp


def _is_slot_in_past(slot_time, query_date, current_time):
    """Check if a time slot is in the past."""
    today = current_time.date()
    if query_date < today:
        return True
    if query_date > today:
        return False
    return slot_time.hour < current_time.hour


def _can_cancel_slot(slot, current_user_id):
    """Check if user can cancel this slot."""
    if not current_user_id:
        return False

    status = slot.get('status')
    if status not in ('reserved', 'short_notice'):
        return False

    details = slot.get('details')
    if not details:
        return False

    # Short notice bookings cannot be cancelled
    if status == 'short_notice' or details.get('is_short_notice'):
        return False

    return (
        details.get('booked_for_id') == current_user_id or
        details.get('booked_by_id') == current_user_id
    )


def _compute_slot_class(slot, is_past, current_user_id=None):
    """Pre-compute CSS classes for a slot."""
    classes = 'border border-gray-300 px-2 py-4 text-center text-xs'
    status = slot['status']

    if status == 'available':
        if is_past:
            classes += ' bg-gray-200 text-gray-500'
        else:
            classes += ' bg-green-500 text-white cursor-pointer hover:opacity-80'
    elif status == 'short_notice':
        classes += ' bg-orange-500 text-white'
        if is_past:
            classes += ' opacity-75'
        elif _can_cancel_slot(slot, current_user_id):
            classes += ' cursor-pointer hover:opacity-80'
    elif status == 'reserved':
        details = slot.get('details')
        if details and details.get('is_short_notice'):
            classes += ' bg-orange-500 text-white'
        else:
            classes += ' bg-red-500 text-white'
        if is_past:
            classes += ' opacity-75'
        elif _can_cancel_slot(slot, current_user_id):
            classes += ' cursor-pointer hover:opacity-80'
    elif status == 'blocked':
        classes += ' bg-gray-400 text-white min-h-16'
        if is_past:
            classes += ' opacity-75'

    return classes


def _compute_slot_content(slot, is_past):
    """Pre-compute display content for a slot."""
    status = slot['status']

    if status == 'available':
        return 'Vergangen' if is_past else 'Frei'

    if status in ('short_notice', 'reserved'):
        details = slot.get('details')
        if details:
            booked_for = details.get('booked_for', '')
            booked_by = details.get('booked_by', '')
            booked_for_id = details.get('booked_for_id')
            booked_by_id = details.get('booked_by_id')

            if booked_for_id == booked_by_id:
                return booked_for
            return f'{booked_for}<br>(von {booked_by})'
        return 'Gebucht'

    if status == 'blocked':
        details = slot.get('details')
        if details and details.get('reason'):
            content = details['reason']
            extra = details.get('details', '').strip()
            if extra:
                content += f'<br><span style="font-size: 0.7em; opacity: 0.9;">{extra}</span>'
            return content
        return 'Gesperrt'

    return ''


@bp.route('/courts/availability', methods=['GET'])
@jwt_or_session_required
def get_availability():
    """Get court availability grid for a specific date.

    Query params:
        date: Date in YYYY-MM-DD format (default: today)
    """
    from app.utils.timezone_utils import get_current_berlin_time

    date_str = request.args.get('date', date.today().isoformat())
    try:
        query_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datumsformat'}), 400

    current_time = get_current_berlin_time()
    courts = Court.query.order_by(Court.number).all()
    reservations = ReservationService.get_reservations_by_date(query_date)
    blocks = BlockService.get_blocks_by_date(query_date)

    # Build time slots (08:00 to 22:00)
    time_slots = [time(hour, 0) for hour in range(8, 22)]

    grid = []
    for court in courts:
        court_data = {
            'court_id': court.id,
            'court_number': court.number,
            'slots': []
        }

        for slot_time in time_slots:
            slot = {
                'time': slot_time.strftime('%H:%M'),
                'status': 'available',
                'details': None
            }

            # Check if blocked
            for block in blocks:
                if (block.court_id == court.id and
                    block.start_time <= slot_time < block.end_time):
                    slot['status'] = 'blocked'
                    slot['details'] = {
                        'reason': block.reason_obj.name if block.reason_obj else 'Unbekannt',
                        'details': block.details if block.details else '',
                        'block_id': block.id
                    }
                    break

            # Check if reserved (only if not blocked)
            if slot['status'] == 'available':
                for reservation in reservations:
                    if (reservation.court_id == court.id and
                        reservation.start_time == slot_time and
                        reservation.status == 'active'):

                        is_active = ReservationService.is_reservation_currently_active(
                            reservation, current_time
                        )

                        if is_active:
                            slot['status'] = 'short_notice' if reservation.is_short_notice else 'reserved'
                            slot['details'] = {
                                'booked_for': f"{reservation.booked_for.firstname} {reservation.booked_for.lastname}",
                                'booked_for_id': reservation.booked_for_id,
                                'booked_by': f"{reservation.booked_by.firstname} {reservation.booked_by.lastname}",
                                'booked_by_id': reservation.booked_by_id,
                                'reservation_id': reservation.id,
                                'is_short_notice': reservation.is_short_notice
                            }
                        break

            court_data['slots'].append(slot)

        grid.append(court_data)

    # Pre-compute CSS classes and content for each slot
    current_user_id = current_user.id
    for court_data in grid:
        for slot in court_data['slots']:
            slot_time_obj = time.fromisoformat(slot['time'])
            is_past = _is_slot_in_past(slot_time_obj, query_date, current_time)

            slot['cssClass'] = _compute_slot_class(slot, is_past, current_user_id)
            slot['content'] = _compute_slot_content(slot, is_past)
            slot['isPast'] = is_past
            slot['canCancel'] = not is_past and _can_cancel_slot(slot, current_user_id)

    return jsonify({
        'date': date_str,
        'grid': grid,
        'metadata': {
            'generated_at': current_time.isoformat(),
            'timezone': 'Europe/Berlin'
        }
    })
