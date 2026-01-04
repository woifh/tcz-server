"""Court and availability routes."""
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import date, time
import logging
from app import db, limiter
from app.models import Court, Block
from app.services.reservation_service import ReservationService
from app.services.block_service import BlockService
from app.services.anonymous_filter_service import AnonymousDataFilter

bp = Blueprint('courts', __name__, url_prefix='/courts')

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
                    
                    # Debug logging
                    print(f"DEBUG: Block found - ID: {block.id}, Reason: {block.reason_obj.name if block.reason_obj else 'None'}, Details: '{block.details}'")
                    
                    slot['details'] = {
                        'reason': block.reason_obj.name if block.reason_obj else 'Unbekannt',
                        'details': block.details if block.details else 'NO_DETAILS',
                        'block_id': block.id,
                        'debug_test': 'FIELD_ADDED'
                    }
                    break
            
            # Check if reserved (only if not blocked)
            if slot['status'] == 'available':
                for reservation in reservations:
                    if (reservation.court_id == court.id and 
                        reservation.start_time == slot_time and
                        reservation.status == 'active'):
                        # Set status based on whether it's a short notice booking
                        slot['status'] = 'short_notice' if reservation.is_short_notice else 'reserved'
                        slot['details'] = {
                            'booked_for': f"{reservation.booked_for.firstname} {reservation.booked_for.lastname}",
                            'booked_for_id': reservation.booked_for_id,
                            'booked_by': f"{reservation.booked_by.firstname} {reservation.booked_by.lastname}",
                            'booked_by_id': reservation.booked_by_id,
                            'reservation_id': reservation.id,
                            'is_short_notice': reservation.is_short_notice
                        }
                        # Debug logging
                        print(f"DEBUG: Reservation {reservation.id} at {slot_time} - is_short_notice: {reservation.is_short_notice}, status: {slot['status']}")
                        break
            
            court_data['slots'].append(slot)
        
        grid.append(court_data)
    
    # Filter data based on authentication status
    filtered_grid = AnonymousDataFilter.filter_availability_data(grid, is_authenticated)
    
    return jsonify({
        'date': date_str,
        'grid': filtered_grid
    })
