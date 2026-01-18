"""Court and availability routes."""
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import date, time, datetime
import logging
from app import db, limiter
from app.models import Court, Block
from app.services.reservation_service import ReservationService
from app.services.block_service import BlockService
from app.services.anonymous_filter_service import AnonymousDataFilter

bp = Blueprint('courts', __name__, url_prefix='/courts')


def _is_slot_in_past(slot_time, query_date, current_time):
    """Check if a time slot is in the past."""
    today = current_time.date()

    if query_date < today:
        return True
    if query_date > today:
        return False

    # Same day - compare hours
    return slot_time.hour < current_time.hour


def _compute_slot_class(slot, is_past, is_authenticated, current_user_id=None):
    """Pre-compute CSS classes for a slot."""
    classes = 'border border-gray-300 px-2 py-4 text-center text-xs'
    status = slot['status']

    if status == 'available':
        if is_past:
            classes += ' bg-gray-200 text-gray-500'
        else:
            classes += ' bg-white text-gray-700'
            if is_authenticated:
                classes += ' cursor-pointer hover:bg-gray-50'
    elif status == 'short_notice':
        classes += ' bg-orange-400 text-white'
        if is_past:
            classes += ' opacity-60'
        elif is_authenticated and _can_cancel_slot(slot, current_user_id):
            classes += ' cursor-pointer hover:opacity-80'
    elif status == 'reserved':
        details = slot.get('details')
        if details and details.get('is_short_notice'):
            classes += ' bg-orange-400 text-white'
        else:
            classes += ' bg-red-500 text-white'
        if is_past:
            classes += ' opacity-60'
        elif is_authenticated and _can_cancel_slot(slot, current_user_id):
            classes += ' cursor-pointer hover:opacity-80'
    elif status == 'blocked':
        classes += ' bg-gray-400 text-white min-h-16'
        if is_past:
            classes += ' opacity-60'

    return classes


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

    # User can cancel if they booked it or it's booked for them
    return (
        details.get('booked_for_id') == current_user_id or
        details.get('booked_by_id') == current_user_id
    )


def _compute_slot_content(slot, is_past, is_authenticated):
    """Pre-compute display content for a slot."""
    status = slot['status']

    if status == 'available':
        return '' if is_past else 'Frei'

    if status in ('short_notice', 'reserved'):
        details = slot.get('details')
        if details and is_authenticated:
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

# Set up logging for anonymous access patterns
anonymous_logger = logging.getLogger('anonymous_access')
anonymous_logger.setLevel(logging.INFO)

def is_anonymous_user():
    """Check if the current user is anonymous (not authenticated)."""
    return not current_user.is_authenticated

def log_anonymous_access(endpoint, ip_address, user_agent=None):
    """Log anonymous user access patterns for monitoring."""
    anonymous_logger.info(
        f"Anonymous access - Endpoint: {endpoint}, IP: {ip_address}, "
        f"User-Agent: {user_agent or 'Unknown'}"
    )

@bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors for anonymous users."""
    if is_anonymous_user():
        anonymous_logger.warning(
            f"Rate limit exceeded for anonymous user - IP: {request.remote_addr}, "
            f"Endpoint: {request.endpoint}, User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
        return jsonify({
            'error': 'Zu viele Anfragen. Bitte versuchen Sie es später erneut.',
            'retry_after': e.retry_after
        }), 429
    return jsonify({'error': 'Rate limit exceeded'}), 429


@bp.route('/', methods=['GET'])
@login_required
def list_courts():
    """List all courts."""
    courts = Court.query.order_by(Court.number).all()
    return jsonify({
        'courts': [
            {
                'id': court.id,
                'number': court.number,
                'status': court.status
            }
            for court in courts
        ]
    })


@bp.route('/availability', methods=['GET'])
@limiter.limit("100 per hour", key_func=lambda: request.remote_addr if is_anonymous_user() else None)
def get_availability():
    """Get court availability grid for a specific date.
    
    Returns a grid with status (available/reserved/blocked) for each time slot.
    Supports both authenticated and anonymous users with appropriate data filtering.
    Rate limiting is applied specifically to anonymous users to prevent abuse.
    Uses time-based active booking session logic for real-time availability updates.
    """
    # Log anonymous access for monitoring
    if is_anonymous_user():
        log_anonymous_access(
            endpoint='/courts/availability',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
    
    date_str = request.args.get('date', date.today().isoformat())
    try:
        query_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datumsformat'}), 400
    
    # Detect authentication status
    is_authenticated = current_user.is_authenticated
    
    # Get current time for real-time availability calculations
    from app.utils.timezone_utils import get_current_berlin_time
    current_time = get_current_berlin_time()
    
    # Get all courts
    courts = Court.query.order_by(Court.number).all()
    
    # Get reservations for the date
    reservations = ReservationService.get_reservations_by_date(query_date)
    
    # Get blocks for the date
    blocks = BlockService.get_blocks_by_date(query_date)
    
    # Build availability grid
    # Time slots from 08:00 to 22:00 (14 slots: 08:00-09:00, 09:00-10:00, ..., 21:00-22:00)
    time_slots = []
    for hour in range(8, 22):
        time_slots.append(time(hour, 0))
    
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
                        
                        # Use time-based logic to determine if reservation is still active
                        is_reservation_active = ReservationService.is_reservation_currently_active(reservation, current_time)
                        
                        # Only show as reserved if the reservation is still active
                        if is_reservation_active:
                            # Set status based on whether it's a short notice booking
                            slot['status'] = 'short_notice' if reservation.is_short_notice else 'reserved'
                            slot['details'] = {
                                'booked_for': f"{reservation.booked_for.firstname} {reservation.booked_for.lastname}",
                                'booked_for_id': reservation.booked_for_id,
                                'booked_by': f"{reservation.booked_by.firstname} {reservation.booked_by.lastname}",
                                'booked_by_id': reservation.booked_by_id,
                                'reservation_id': reservation.id,
                                'is_short_notice': reservation.is_short_notice,
                                'is_active': is_reservation_active,
                                'booking_status': 'active'
                            }
                        else:
                            # Reservation has ended, slot becomes available
                            slot['status'] = 'available'
                        break
            
            court_data['slots'].append(slot)
        
        grid.append(court_data)
    
    # Filter data based on authentication status
    filtered_grid = AnonymousDataFilter.filter_availability_data(grid, is_authenticated)

    # Pre-compute CSS classes and display content for each slot
    # This eliminates 252 JS function calls per render (84 cells × 3 calls each)
    current_user_id = current_user.id if is_authenticated else None
    for court_data in filtered_grid:
        for slot in court_data['slots']:
            slot_time = time.fromisoformat(slot['time'])
            is_past = _is_slot_in_past(slot_time, query_date, current_time)

            slot['cssClass'] = _compute_slot_class(
                slot, is_past, is_authenticated, current_user_id
            )
            slot['content'] = _compute_slot_content(slot, is_past, is_authenticated)
            slot['isPast'] = is_past
            slot['canCancel'] = (
                is_authenticated and
                not is_past and
                _can_cancel_slot(slot, current_user_id)
            )

    # Add metadata about real-time updates
    response_data = {
        'date': date_str,
        'grid': filtered_grid,
        'metadata': {
            'generated_at': current_time.isoformat(),
            'uses_realtime_logic': True,
            'timezone': 'Europe/Berlin',
            'precomputed_rendering': True
        }
    }

    return jsonify(response_data)


@bp.route('/availability/realtime', methods=['GET'])
@limiter.limit("200 per hour", key_func=lambda: request.remote_addr if is_anonymous_user() else None)
def get_realtime_availability():
    """Get real-time court availability information using active booking session logic.
    
    This endpoint provides up-to-date availability information that considers
    whether reservations are currently active based on the current time.
    Useful for dashboard displays and booking interfaces that need real-time updates.
    """
    # Log anonymous access for monitoring
    if is_anonymous_user():
        log_anonymous_access(
            endpoint='/courts/availability/realtime',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
    
    date_str = request.args.get('date', date.today().isoformat())
    try:
        query_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datumsformat'}), 400
    
    # Get current time for real-time calculations
    from app.utils.timezone_utils import get_current_berlin_time
    current_time = get_current_berlin_time()
    
    # Get all courts
    courts = Court.query.order_by(Court.number).all()
    
    # Get reservations for the date
    reservations = ReservationService.get_reservations_by_date(query_date)
    
    # Calculate availability statistics using active booking session logic
    total_slots = len(courts) * 14  # 6 courts * 14 time slots (08:00-22:00)
    active_reservations = 0
    past_reservations = 0
    short_notice_active = 0
    
    for reservation in reservations:
        if reservation.status == 'active':
            is_active = ReservationService.is_reservation_currently_active(reservation, current_time)
            if is_active:
                active_reservations += 1
                if reservation.is_short_notice:
                    short_notice_active += 1
            else:
                past_reservations += 1
    
    # Get blocks for the date
    blocks = BlockService.get_blocks_by_date(query_date)
    blocked_slots = len(blocks)  # Simplified count
    
    available_slots = total_slots - active_reservations - blocked_slots
    
    return jsonify({
        'date': date_str,
        'current_time': current_time.isoformat(),
        'availability_summary': {
            'total_slots': total_slots,
            'available_slots': available_slots,
            'active_reservations': active_reservations,
            'past_reservations': past_reservations,
            'short_notice_active': short_notice_active,
            'blocked_slots': blocked_slots,
            'availability_percentage': round((available_slots / total_slots) * 100, 1)
        },
        'courts': [
            {
                'id': court.id,
                'number': court.number,
                'status': court.status
            }
            for court in courts
        ],
        'metadata': {
            'uses_realtime_logic': True,
            'timezone': 'Europe/Berlin',
            'generated_at': current_time.isoformat()
        }
    })
