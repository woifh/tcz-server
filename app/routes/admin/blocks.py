"""
Admin Blocks Module

Contains block CRUD operations and basic block management routes.
"""

from datetime import datetime
from flask import request, jsonify
from flask_login import login_required, current_user

from app import db
from app.decorators import admin_required, teamster_or_admin_required
from app.models import Block, Court, BlockReason, Reservation
from app.services.block_service import BlockService
from app.services.reservation_service import ReservationService
from . import bp


@bp.route('/blocks', methods=['GET'])
@login_required
@teamster_or_admin_required
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
@teamster_or_admin_required
def create_blocks():
    """Create block(s) in a batch - handles single or multiple courts."""
    try:
        data = request.get_json() if request.is_json else request.form

        # Get court_ids (supports both single court_id and multiple court_ids)
        court_ids = None
        if 'court_ids' in data:
            court_ids = data.getlist('court_ids') if hasattr(data, 'getlist') else data.get('court_ids', [])
            if isinstance(court_ids, str):
                court_ids = [int(x) for x in court_ids.split(',')]
            else:
                court_ids = [int(x) for x in court_ids]
        elif 'court_id' in data:
            # Single court - convert to list for unified handling
            court_ids = [int(data['court_id'])]
        else:
            return jsonify({'error': 'court_id oder court_ids erforderlich'}), 400

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

        # Always use multi-court approach (works for single court too)
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

        return jsonify({
            'message': f'{len(blocks)} Sperrung{"en" if len(blocks) > 1 else ""} erfolgreich erstellt',
            'block_count': len(blocks),
            'batch_id': blocks[0].batch_id if blocks else None
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/<batch_id>', methods=['PUT'])
@login_required
@teamster_or_admin_required
def update_batch(batch_id):
    """Update all blocks in a batch, including court changes."""
    try:
        data = request.get_json() if request.is_json else request.form

        # Parse new data
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        new_end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        new_reason_id = int(data['reason_id'])
        new_details = data.get('details', '').strip() or None

        # Get new court IDs
        new_court_ids = data.get('court_ids', [])
        if isinstance(new_court_ids, str):
            new_court_ids = [int(x) for x in new_court_ids.split(',')]
        else:
            new_court_ids = [int(x) for x in new_court_ids]

        # Validate that the date is not in the past
        from app.utils.timezone_utils import get_berlin_date_today
        today = get_berlin_date_today()
        if new_date < today:
            return jsonify({'error': 'Sperrungen können nicht für vergangene Tage bearbeitet werden'}), 400

        # Validate time range
        if new_start_time >= new_end_time:
            return jsonify({'error': 'Endzeit muss nach Startzeit liegen'}), 400

        # Get all existing blocks in the batch
        existing_blocks = Block.query.filter_by(batch_id=batch_id).all()

        if not existing_blocks:
            return jsonify({'error': 'Batch nicht gefunden'}), 404

        # Teamsters can only update their own batches
        if current_user.is_teamster():
            if not all(block.created_by_id == current_user.id for block in existing_blocks):
                return jsonify({'error': 'Sie können nur Ihre eigenen Sperrungen bearbeiten'}), 403

        # Get existing court IDs
        existing_court_ids = [block.court_id for block in existing_blocks]

        # Determine which courts to keep, delete, and add
        courts_to_keep = set(existing_court_ids) & set(new_court_ids)
        courts_to_delete = set(existing_court_ids) - set(new_court_ids)
        courts_to_add = set(new_court_ids) - set(existing_court_ids)

        # Delete blocks for courts that are no longer selected
        for block in existing_blocks:
            if block.court_id in courts_to_delete:
                db.session.delete(block)

        # Update blocks for courts that remain selected
        for block in existing_blocks:
            if block.court_id in courts_to_keep:
                success, error = BlockService.update_single_instance(
                    block_id=block.id,
                    date=new_date,
                    start_time=new_start_time,
                    end_time=new_end_time,
                    reason_id=new_reason_id,
                    details=new_details,
                    admin_id=current_user.id
                )

                if error:
                    db.session.rollback()
                    return jsonify({'error': f'Fehler beim Aktualisieren von Block {block.id}: {error}'}), 400

        # Create new blocks for newly selected courts
        for court_id in courts_to_add:
            new_block = Block(
                court_id=court_id,
                date=new_date,
                start_time=new_start_time,
                end_time=new_end_time,
                reason_id=new_reason_id,
                details=new_details,
                created_by_id=current_user.id,
                batch_id=batch_id  # Use the same batch_id
            )
            db.session.add(new_block)
            db.session.flush()

            # Cancel conflicting reservations for new blocks
            BlockService.cancel_conflicting_reservations(new_block)

        # Commit all changes
        db.session.commit()

        # Log the operation
        BlockService.log_block_operation(
            operation='update',
            block_data={
                'batch_id': batch_id,
                'new_court_ids': new_court_ids,
                'existing_court_ids': existing_court_ids,
                'courts_kept': list(courts_to_keep),
                'courts_deleted': list(courts_to_delete),
                'courts_added': list(courts_to_add),
                'date': new_date.isoformat(),
                'start_time': new_start_time.isoformat(),
                'end_time': new_end_time.isoformat(),
                'reason_id': new_reason_id,
                'details': new_details
            },
            admin_id=current_user.id
        )

        total_blocks = len(courts_to_keep) + len(courts_to_add)
        return jsonify({'message': f'{total_blocks} Sperrungen erfolgreich aktualisiert'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/<batch_id>', methods=['DELETE'])
@login_required
@teamster_or_admin_required
def delete_batch(batch_id):
    """Delete all blocks in a batch."""
    try:
        # Get all blocks in the batch
        blocks = Block.query.filter_by(batch_id=batch_id).all()

        if not blocks:
            return jsonify({'success': False, 'error': 'Batch nicht gefunden'}), 404

        # Teamsters can only delete their own batches
        if current_user.is_teamster():
            if not all(block.created_by_id == current_user.id for block in blocks):
                return jsonify({'error': 'Sie können nur Ihre eigenen Sperrungen löschen'}), 403

        success, error = BlockService.delete_batch(batch_id, current_user.id)

        if success:
            return jsonify({'success': True, 'message': 'Batch erfolgreich gelöscht'}), 200
        else:
            return jsonify({'success': False, 'error': error}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/blocks/<batch_id>', methods=['GET'])
@login_required
@teamster_or_admin_required
def get_batch(batch_id):
    """Get all blocks in a batch."""
    try:
        # Get all blocks in the batch
        blocks = Block.query.filter_by(batch_id=batch_id).all()

        if not blocks:
            return jsonify({'error': 'Batch nicht gefunden'}), 404

        # Format all blocks in the batch
        blocks_data = []
        for block in blocks:
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

        # Return batch info with first block's common data and all court_ids
        first_block = blocks[0]
        return jsonify({
            'batch_id': batch_id,
            'date': first_block.date.isoformat(),
            'start_time': first_block.start_time.strftime('%H:%M'),
            'end_time': first_block.end_time.strftime('%H:%M'),
            'reason_id': first_block.reason_id,
            'reason_name': BlockReason.query.get(first_block.reason_id).name if first_block.reason_id else 'Unbekannt',
            'details': first_block.details,
            'court_ids': [b['court_id'] for b in blocks_data],
            'blocks': blocks_data
        }), 200

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