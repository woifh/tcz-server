"""Admin routes for blocks and overrides."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from app import db
from app.models import Block, Reservation
from app.services.block_service import BlockService
from app.services.reservation_service import ReservationService
from app.services.email_service import EmailService

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            if request.is_json:
                return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403
            flash('Sie haben keine Berechtigung für diese Aktion', 'error')
            return redirect(url_for('dashboard.index')), 403
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
@admin_required
def admin_panel():
    """Admin panel."""
    return render_template('admin.html')


@bp.route('/blocks', methods=['GET'])
@login_required
@admin_required
def list_blocks():
    """List blocks for a specific date (admin only)."""
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': 'Datum ist erforderlich'}), 400
    
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        blocks = BlockService.get_blocks_by_date(query_date)
        
        return jsonify({
            'date': date_str,
            'blocks': [
                {
                    'id': block.id,
                    'court_id': block.court_id,
                    'court_number': block.court.number,
                    'start_time': block.start_time.strftime('%H:%M'),
                    'end_time': block.end_time.strftime('%H:%M'),
                    'reason': block.reason,
                    'created_by': block.created_by.name
                }
                for block in blocks
            ]
        })
    except ValueError:
        return jsonify({'error': 'Ungültiges Datumsformat'}), 400


@bp.route('/blocks', methods=['POST'])
@login_required
@admin_required
def create_block():
    """Create block (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        court_id = int(data.get('court_id'))
        date_str = data.get('date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        reason = data.get('reason')
        
        # Validate required fields
        if not all([court_id, date_str, start_time_str, end_time_str, reason]):
            return jsonify({'error': 'Alle Felder sind erforderlich'}), 400
        
        # Parse date and times
        block_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Create block
        block, error = BlockService.create_block(
            court_id=court_id,
            date=block_date,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
            admin_id=current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'id': block.id,
            'message': 'Sperrung erfolgreich erstellt',
            'block': {
                'id': block.id,
                'court_id': block.court_id,
                'date': block.date.isoformat(),
                'start_time': block.start_time.strftime('%H:%M'),
                'end_time': block.end_time.strftime('%H:%M'),
                'reason': block.reason
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_block(id):
    """Delete block (admin only)."""
    try:
        block = Block.query.get_or_404(id)
        
        db.session.delete(block)
        db.session.commit()
        
        return jsonify({'message': 'Sperrung erfolgreich gelöscht'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/reservations/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_reservation(id):
    """Admin delete reservation with reason (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        reason = data.get('reason', 'Administratorentscheidung')
        
        reservation = Reservation.query.get_or_404(id)
        
        # Store member info before deletion
        booked_for = reservation.booked_for
        booked_by = reservation.booked_by
        
        # Cancel the reservation with reason
        success, error = ReservationService.cancel_reservation(id, reason=reason)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Send admin override notifications
        EmailService.send_admin_override(
            reservation=reservation,
            reason=reason
        )
        
        return jsonify({
            'message': 'Buchung erfolgreich gelöscht',
            'reason': reason
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
