"""Court and availability routes."""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from datetime import date, time
from app import limiter
from app.models import Court, Block
from app.services.reservation_service import ReservationService
from app.services.block_service import BlockService

bp = Blueprint('courts', __name__, url_prefix='/courts')


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
@login_required
@limiter.limit("500 per hour")  # Higher limit for frequently accessed availability data
def get_availability():
    """Get court availability grid for a specific date.
    
    Returns a grid with status (available/reserved/blocked) for each time slot.
    """
    date_str = request.args.get('date', date.today().isoformat())
    try:
        query_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Ungültiges Datumsformat'}), 400
    
    # Get all courts
    courts = Court.query.order_by(Court.number).all()
    
    # Get reservations for the date
    reservations = ReservationService.get_reservations_by_date(query_date)
    
    # Get blocks for the date
    blocks = BlockService.get_blocks_by_date(query_date)
    
    # Build availability grid
    # Time slots from 06:00 to 21:00 (16 slots)
    time_slots = []
    for hour in range(6, 22):
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
                        'reason': block.reason
                    }
                    break
            
            # Check if reserved (only if not blocked)
            if slot['status'] == 'available':
                for reservation in reservations:
                    if (reservation.court_id == court.id and 
                        reservation.start_time == slot_time and
                        reservation.status == 'active'):
                        slot['status'] = 'reserved'
                        slot['details'] = {
                            'booked_for': f"{reservation.booked_for.firstname} {reservation.booked_for.lastname}",
                            'booked_for_id': reservation.booked_for_id,
                            'booked_by': f"{reservation.booked_by.firstname} {reservation.booked_by.lastname}",
                            'booked_by_id': reservation.booked_by_id,
                            'reservation_id': reservation.id
                        }
                        break
            
            court_data['slots'].append(slot)
        
        grid.append(court_data)
    
    return jsonify({
        'date': date_str,
        'grid': grid
    })
