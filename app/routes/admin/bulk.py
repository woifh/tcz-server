"""
Admin Bulk Operations Module

Contains bulk operations, multi-court operations, and batch management routes.
"""

from datetime import datetime
from flask import request, jsonify
from flask_login import login_required, current_user

from app import db
from app.decorators import admin_required
from app.models import Block, Court, BlockReason, Reservation
from app.services.block_service import BlockService
from app.utils.timezone_utils import get_berlin_date_today
from . import bp


@bp.route('/blocks/batch/<batch_id>', methods=['PUT'])
@login_required
@admin_required
def update_batch(batch_id):
    """Update entire batch of blocks (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Get all blocks in the batch
        blocks = Block.query.filter_by(batch_id=batch_id).all()
        
        if not blocks:
            return jsonify({'error': 'Batch nicht gefunden'}), 404
        
        # Get the new data
        new_court_ids = data.get('court_ids', [])
        if isinstance(new_court_ids, str):
            new_court_ids = [int(x) for x in new_court_ids.split(',')]
        elif isinstance(new_court_ids, list):
            new_court_ids = [int(x) for x in new_court_ids]
        
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        new_end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        new_reason_id = int(data['reason_id'])
        new_details = data.get('details', '').strip() or None
        
        # Validate that the date is not in the past
        today = get_berlin_date_today()
        if new_date < today:
            return jsonify({'error': 'Sperrungen können nicht für vergangene Tage bearbeitet werden'}), 400
        
        # Validate time range
        if new_start_time >= new_end_time:
            return jsonify({'error': 'Endzeit muss nach Startzeit liegen'}), 400
        
        # Get current court IDs
        current_court_ids = [block.court_id for block in blocks]
        
        # Determine which blocks to delete, update, and create
        courts_to_delete = set(current_court_ids) - set(new_court_ids)
        courts_to_keep = set(current_court_ids) & set(new_court_ids)
        courts_to_add = set(new_court_ids) - set(current_court_ids)
        
        # Delete blocks for courts that are no longer selected
        for block in blocks:
            if block.court_id in courts_to_delete:
                db.session.delete(block)
        
        # Update existing blocks for courts that are kept
        for block in blocks:
            if block.court_id in courts_to_keep:
                block.date = new_date
                block.start_time = new_start_time
                block.end_time = new_end_time
                block.reason_id = new_reason_id
                block.details = new_details
        
        # Create new blocks for newly selected courts (with same batch_id)
        for court_id in courts_to_add:
            new_block = Block(
                court_id=court_id,
                date=new_date,
                start_time=new_start_time,
                end_time=new_end_time,
                reason_id=new_reason_id,
                details=new_details,
                batch_id=batch_id,  # Use the same batch_id
                created_by_id=current_user.id
            )
            db.session.add(new_block)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Batch erfolgreich aktualisiert',
            'batch_id': batch_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/batch/<batch_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_batch(batch_id):
    """Delete entire batch of blocks (admin only)."""
    try:
        success, error = BlockService.delete_batch(batch_id, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Batch erfolgreich gelöscht'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/multi-court-delete/<int:primary_block_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_multi_court_blocks(primary_block_id):
    """Delete multi-court blocks by primary block ID (admin only)."""
    try:
        # Get the primary block to find the batch_id
        primary_block = Block.query.get_or_404(primary_block_id)
        batch_id = primary_block.batch_id
        
        # Delete all blocks in the batch
        success, error = BlockService.delete_batch(batch_id, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Mehrplatz-Sperrungen erfolgreich gelöscht'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/multi-court-update/<int:primary_block_id>', methods=['PUT'])
@login_required
@admin_required
def update_multi_court_blocks(primary_block_id):
    """Update multi-court blocks by primary block ID (admin only)."""
    try:
        # Get the primary block to find the batch_id
        primary_block = Block.query.get_or_404(primary_block_id)
        batch_id = primary_block.batch_id
        
        data = request.get_json() if request.is_json else request.form
        
        # Get all blocks in the batch
        blocks = Block.query.filter_by(batch_id=batch_id).all()
        
        if not blocks:
            return jsonify({'error': 'Batch nicht gefunden'}), 404
        
        # Get the new data
        new_court_ids = data.get('court_ids', [])
        if isinstance(new_court_ids, str):
            new_court_ids = [int(x) for x in new_court_ids.split(',')]
        elif isinstance(new_court_ids, list):
            new_court_ids = [int(x) for x in new_court_ids]
        
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        new_end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        new_reason_id = int(data['reason_id'])
        new_details = data.get('details', '').strip() or None
        
        # Validate that the date is not in the past
        today = get_berlin_date_today()
        if new_date < today:
            return jsonify({'error': 'Sperrungen können nicht für vergangene Tage bearbeitet werden'}), 400
        
        # Validate time range
        if new_start_time >= new_end_time:
            return jsonify({'error': 'Endzeit muss nach Startzeit liegen'}), 400
        
        # Get current court IDs
        current_court_ids = [block.court_id for block in blocks]
        
        # Determine which blocks to delete, update, and create
        courts_to_delete = set(current_court_ids) - set(new_court_ids)
        courts_to_keep = set(current_court_ids) & set(new_court_ids)
        courts_to_add = set(new_court_ids) - set(current_court_ids)
        
        # Delete blocks for courts that are no longer selected
        for block in blocks:
            if block.court_id in courts_to_delete:
                db.session.delete(block)
        
        # Update existing blocks for courts that are kept
        for block in blocks:
            if block.court_id in courts_to_keep:
                block.date = new_date
                block.start_time = new_start_time
                block.end_time = new_end_time
                block.reason_id = new_reason_id
                block.details = new_details
        
        # Create new blocks for newly selected courts (with same batch_id)
        for court_id in courts_to_add:
            new_block = Block(
                court_id=court_id,
                date=new_date,
                start_time=new_start_time,
                end_time=new_end_time,
                reason_id=new_reason_id,
                details=new_details,
                batch_id=batch_id,  # Use the same batch_id
                created_by_id=current_user.id
            )
            db.session.add(new_block)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Mehrplatz-Sperrungen erfolgreich aktualisiert',
            'batch_id': batch_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/multi-court', methods=['POST'])
@login_required
@admin_required
def create_multi_court_blocks():
    """Create blocks for multiple courts simultaneously (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        court_ids = data.get('court_ids', [])
        if isinstance(court_ids, str):
            court_ids = [int(x) for x in court_ids.split(',')]
        elif isinstance(court_ids, list):
            court_ids = [int(x) for x in court_ids]
        
        date_str = data.get('date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        reason_id = int(data.get('reason_id'))
        details = data.get('details', '').strip() or None
        
        # Validate required fields
        if not all([court_ids, date_str, start_time_str, end_time_str, reason_id]):
            return jsonify({'error': 'Alle Pflichtfelder sind erforderlich'}), 400
        
        # Parse date and times
        block_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Validate that the date is not in the past
        today = get_berlin_date_today()
        if block_date < today:
            return jsonify({'error': 'Sperrungen können nicht für vergangene Tage erstellt werden'}), 400
        
        # Create multi-court blocks
        blocks, error = BlockService.create_multi_court_blocks(
            court_ids=court_ids,
            date=block_date,
            start_time=start_time,
            end_time=end_time,
            reason_id=reason_id,
            details=details,
            admin_id=current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        # Get the batch_id from the first created block
        batch_id = blocks[0].batch_id if blocks else None
        
        return jsonify({
            'message': f'Mehrplatz-Sperrungen erfolgreich erstellt: {len(blocks)} Plätze',
            'blocks_created': len(blocks),
            'batch_id': batch_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/bulk-delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete_blocks():
    """Bulk delete blocks (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        block_ids = data.get('block_ids', [])
        
        if not block_ids:
            return jsonify({'error': 'Keine Block-IDs angegeben'}), 400
        
        success, error = BlockService.bulk_delete_blocks(block_ids, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': f'{len(block_ids)} Sperrungen erfolgreich gelöscht'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/conflict-preview', methods=['POST'])
@login_required
@admin_required
def get_conflict_preview():
    """Get conflict preview for block creation/update."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        court_ids = data.get('court_ids', [])
        if isinstance(court_ids, str):
            court_ids = [int(x) for x in court_ids.split(',')]
        elif isinstance(court_ids, list):
            court_ids = [int(x) for x in court_ids]
        
        date_str = data.get('date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        
        # Parse date and times
        block_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        conflicts = []
        
        for court_id in court_ids:
            # Check for existing reservations
            existing_reservations = Reservation.query.filter(
                Reservation.court_id == court_id,
                Reservation.date == block_date,
                Reservation.start_time < end_time,
                Reservation.end_time > start_time
            ).all()
            
            # Check for existing blocks
            existing_blocks = Block.query.filter(
                Block.court_id == court_id,
                Block.date == block_date,
                Block.start_time < end_time,
                Block.end_time > start_time
            ).all()
            
            court_conflicts = {
                'court_id': court_id,
                'reservations': len(existing_reservations),
                'blocks': len(existing_blocks),
                'total_conflicts': len(existing_reservations) + len(existing_blocks)
            }
            
            conflicts.append(court_conflicts)
        
        return jsonify({
            'conflicts': conflicts,
            'total_affected_reservations': sum(c['reservations'] for c in conflicts),
            'total_affected_blocks': sum(c['blocks'] for c in conflicts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500