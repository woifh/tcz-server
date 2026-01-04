"""
Admin Blocks Module

Contains block CRUD operations and basic block management routes.
"""

from datetime import datetime
from flask import request, jsonify
from flask_login import login_required, current_user

from app import db
from app.decorators import admin_required
from app.models import Block, Court, BlockReason, Reservation
from app.services.block_service import BlockService
from app.services.reservation_service import ReservationService
from . import bp


@bp.route('/blocks', methods=['GET'])
@login_required
@admin_required
def get_blocks():
    """Get blocks with optional filtering."""
    try:
        # Get filter parameters
        date_range_start = request.args.get('date_range_start')
        date_range_end = request.args.get('date_range_end')
        court_ids = request.args.getlist('court_ids', type=int)
        reason_ids = request.args.getlist('reason_ids', type=int)
        block_types = request.args.getlist('block_types')
        
        # Also support singular parameters for backward compatibility
        court_id = request.args.get('court_id')
        reason_id = request.args.get('reason_id')
        
        # Build query
        query = Block.query
        
        # Apply filters
        if date_range_start:
            start_date = datetime.strptime(date_range_start, '%Y-%m-%d').date()
            query = query.filter(Block.date >= start_date)
            
        if date_range_end:
            end_date = datetime.strptime(date_range_end, '%Y-%m-%d').date()
            query = query.filter(Block.date <= end_date)
            
        # Handle court filtering (plural or singular)
        if court_ids:
            query = query.filter(Block.court_id.in_(court_ids))
        elif court_id:
            query = query.filter(Block.court_id == int(court_id))
            
        # Handle reason filtering (plural or singular)
        if reason_ids:
            query = query.filter(Block.reason_id.in_(reason_ids))
        elif reason_id:
            query = query.filter(Block.reason_id == int(reason_id))
        
        # Handle block types filtering (if needed in the future)
        # block_types parameter is available but not currently used
        
        # Execute query and get results
        blocks = query.order_by(Block.date.asc(), Block.start_time.asc()).all()
        
        # Format blocks for JSON response
        blocks_data = []
        for block in blocks:
            # Get court and reason information
            court = Court.query.get(block.court_id)
            reason = BlockReason.query.get(block.reason_id)
            
            block_data = {
                'id': block.id,
                'batch_id': block.batch_id,
                'court_id': block.court_id,
                'court_number': court.number if court else block.court_id,
                'date': block.date.isoformat(),
                'start_time': block.start_time.strftime('%H:%M'),
                'end_time': block.end_time.strftime('%H:%M'),
                'reason_id': block.reason_id,
                'reason_name': reason.name if reason else 'Unbekannt',
                'details': block.details,
                'created_at': block.created_at.isoformat() if block.created_at else None,
                'created_by_id': block.created_by_id
            }
            blocks_data.append(block_data)
        
        return jsonify({'blocks': blocks_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks', methods=['POST'])
@login_required
@admin_required
def create_block():
    """Create a single block."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        court_id = int(data['court_id'])
        date_str = data['date']
        start_time_str = data['start_time']
        end_time_str = data['end_time']
        reason_id = int(data['reason_id'])
        details = data.get('details', '').strip() or None
        
        # Parse date and times
        block_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Validate that the date is not in the past
        from app.utils.timezone_utils import get_berlin_date_today
        today = get_berlin_date_today()
        if block_date < today:
            return jsonify({'error': 'Sperrungen können nicht für vergangene Tage erstellt werden'}), 400
        
        # Create block
        block, error = BlockService.create_block(
            court_id=court_id,
            date=block_date,
            start_time=start_time,
            end_time=end_time,
            reason_id=reason_id,
            details=details,
            admin_id=current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Sperrung erfolgreich erstellt',
            'block_id': block.id,
            'batch_id': block.batch_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_block(id):
    """Update a single block."""
    try:
        block = Block.query.get_or_404(id)
        data = request.get_json() if request.is_json else request.form
        
        # Parse new data
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        new_end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        new_reason_id = int(data['reason_id'])
        new_details = data.get('details', '').strip() or None
        
        # Validate that the date is not in the past
        from app.utils.timezone_utils import get_berlin_date_today
        today = get_berlin_date_today()
        if new_date < today:
            return jsonify({'error': 'Sperrungen können nicht für vergangene Tage bearbeitet werden'}), 400
        
        # Validate time range
        if new_start_time >= new_end_time:
            return jsonify({'error': 'Endzeit muss nach Startzeit liegen'}), 400
        
        # Update block
        success, error = BlockService.update_single_instance(
            block_id=id,
            date=new_date,
            start_time=new_start_time,
            end_time=new_end_time,
            reason_id=new_reason_id,
            details=new_details,
            admin_id=current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Sperrung erfolgreich aktualisiert'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_block(id):
    """Delete a single block."""
    try:
        block = Block.query.get_or_404(id)
        
        # Log the operation before deletion
        BlockService.log_block_operation(
            operation='delete',
            block_data={
                'block_id': block.id,
                'court_id': block.court_id,
                'date': block.date.isoformat(),
                'start_time': block.start_time.isoformat(),
                'end_time': block.end_time.isoformat(),
                'reason_id': block.reason_id,
                'details': block.details
            },
            admin_id=current_user.id
        )
        
        db.session.delete(block)
        db.session.commit()
        
        return jsonify({'message': 'Sperrung erfolgreich gelöscht'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/<int:id>', methods=['GET'])
@login_required
@admin_required
def get_block(id):
    """Get a single block."""
    try:
        block = Block.query.get_or_404(id)
        
        # Get court and reason information
        court = Court.query.get(block.court_id)
        reason = BlockReason.query.get(block.reason_id)
        
        block_data = {
            'id': block.id,
            'batch_id': block.batch_id,
            'court_id': block.court_id,
            'court_number': court.number if court else block.court_id,
            'date': block.date.isoformat(),
            'start_time': block.start_time.strftime('%H:%M'),
            'end_time': block.end_time.strftime('%H:%M'),
            'reason_id': block.reason_id,
            'reason_name': reason.name if reason else 'Unbekannt',
            'details': block.details,
            'created_at': block.created_at.isoformat() if block.created_at else None,
            'created_by_id': block.created_by_id
        }
        
        return jsonify({'block': block_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/reservations/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_reservation(id):
    """Delete a reservation (admin only)."""
    try:
        success, error = ReservationService.delete_reservation(id, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Reservierung erfolgreich gelöscht'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500