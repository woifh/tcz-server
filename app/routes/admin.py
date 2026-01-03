"""Admin routes for blocks and overrides."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date
import uuid
from app import db
from app.models import Block, Reservation, BlockReason, BlockSeries, BlockTemplate, SubReasonTemplate
from app.services.block_service import BlockService
from app.services.block_reason_service import BlockReasonService
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
    """Admin panel overview - redirect to overview page."""
    return redirect(url_for('admin.overview'))


@bp.route('/overview')
@login_required
@admin_required
def overview():
    """Admin overview page."""
    return render_template('admin/overview.html')


@bp.route('/court-blocking')
@login_required
@admin_required
def court_blocking():
    """Court blocking management page."""
    return render_template('admin/court_blocking.html')


@bp.route('/court-blocking/<batch_id>')
@login_required
@admin_required
def court_blocking_edit_batch(batch_id):
    """Court blocking edit page using batch_id."""
    try:
        # Remove 'batch_' prefix if present to get the actual UUID
        actual_batch_id = batch_id.replace('batch_', '') if batch_id.startswith('batch_') else batch_id
        
        # Get all blocks with this batch_id
        blocks = Block.query.filter_by(batch_id=actual_batch_id).all()
        
        if not blocks:
            flash('Sperrung nicht gefunden', 'error')
            return redirect(url_for('admin.court_blocking'))
        
        # Use the first block as the primary block for data
        primary_block = blocks[0]
        
        # Extract court IDs from all blocks in the batch
        court_ids = [block.court_id for block in blocks]
        
        # Create a combined block data structure
        edit_block_data = {
            'id': primary_block.id,
            'batch_id': actual_batch_id,  # Use the batch_id from the URL, not from the database
            'court_ids': court_ids,
            'date': primary_block.date,
            'start_time': primary_block.start_time,
            'end_time': primary_block.end_time,
            'reason_id': primary_block.reason_id,
            'sub_reason': primary_block.sub_reason,
            'created_by': primary_block.created_by,
            'created_at': primary_block.created_at,
            'related_block_ids': [block.id for block in blocks]
        }
        
        print(f"DEBUG: edit_block_data = {edit_block_data}")  # Debug log
        print(f"DEBUG: batch_id type = {type(edit_block_data['batch_id'])}")  # Debug log
        print(f"DEBUG: batch_id value = '{edit_block_data['batch_id']}'")  # Debug log
        print(f"DEBUG: batch_id repr = {repr(edit_block_data['batch_id'])}")  # Debug log
        
        return render_template('admin/court_blocking.html', edit_block_data=edit_block_data)
    except Exception as e:
        flash(f'Fehler beim Laden der Sperrung: {str(e)}', 'error')
        return redirect(url_for('admin.court_blocking'))


@bp.route('/court-blocking/<int:block_id>')
@login_required
@admin_required
def court_blocking_edit(block_id):
    """Court blocking edit page (legacy - redirects to batch-based edit)."""
    try:
        # Get the block and redirect to batch-based edit
        block = Block.query.get_or_404(block_id)
        
        # All blocks now have batch_id, so redirect to batch edit
        return redirect(url_for('admin.court_blocking_edit_batch', batch_id=f'batch_{block.batch_id}'))
            
    except Exception as e:
        flash(f'Fehler beim Laden der Sperrung: {str(e)}', 'error')
        return redirect(url_for('admin.court_blocking'))


@bp.route('/calendar')
@login_required
@admin_required
def calendar():
    """Calendar view page."""
    return render_template('admin/calendar.html')


@bp.route('/recurring-series')
@login_required
@admin_required
def recurring_series():
    """Recurring series management page."""
    return render_template('admin/recurring_series.html')


@bp.route('/templates')
@login_required
@admin_required
def templates():
    """Templates management page."""
    return render_template('admin/templates.html')


@bp.route('/reasons')
@login_required
@admin_required
def reasons():
    """Reasons management page."""
    return render_template('admin/reasons.html')


@bp.route('/blocks', methods=['GET'])
@login_required
@admin_required
def list_blocks():
    """List blocks with enhanced filtering (admin only)."""
    date_str = request.args.get('date')
    date_range_start = request.args.get('date_range_start')
    date_range_end = request.args.get('date_range_end')
    court_ids = request.args.getlist('court_ids', type=int)
    reason_ids = request.args.getlist('reason_ids', type=int)
    block_types = request.args.getlist('block_types')
    
    try:
        # Handle single date or date range
        if date_str:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            blocks = BlockService.get_blocks_by_date(query_date)
        else:
            # Use enhanced filtering
            date_range = None
            if date_range_start and date_range_end:
                start_date = datetime.strptime(date_range_start, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_range_end, '%Y-%m-%d').date()
                date_range = (start_date, end_date)
            
            blocks = BlockService.filter_blocks(
                date_range=date_range,
                court_ids=court_ids if court_ids else None,
                reason_ids=reason_ids if reason_ids else None,
                block_types=block_types if block_types else None
            )
        
        return jsonify({
            'blocks': [
                {
                    'id': block.id,
                    'court_id': block.court_id,
                    'court_number': block.court.number,
                    'date': block.date.isoformat(),
                    'start_time': block.start_time.strftime('%H:%M'),
                    'end_time': block.end_time.strftime('%H:%M'),
                    'reason_id': block.reason_id,
                    'reason_name': block.reason_obj.name if block.reason_obj else 'Unknown',
                    'sub_reason': block.sub_reason,
                    'batch_id': block.batch_id,
                    'series_id': block.series_id,
                    'is_modified': block.is_modified,
                    'created_by': block.created_by.name,
                    'created_at': block.created_at.isoformat()
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
    """Create block with enhanced reason system (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        court_id = int(data.get('court_id'))
        date_str = data.get('date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        reason_id = int(data.get('reason_id'))
        sub_reason = data.get('sub_reason', '').strip() or None
        
        # Validate required fields
        if not all([court_id, date_str, start_time_str, end_time_str, reason_id]):
            return jsonify({'error': 'Alle Pflichtfelder sind erforderlich'}), 400
        
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
            reason_id=reason_id,
            sub_reason=sub_reason,
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
                'reason_id': block.reason_id,
                'reason_name': block.reason_obj.name,
                'sub_reason': block.sub_reason
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


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
        new_sub_reason = data.get('sub_reason', '').strip() or None
        
        # Validate that the date is not in the past
        today = datetime.now().date()
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
                block.sub_reason = new_sub_reason
        
        # Create new blocks for newly selected courts (with same batch_id)
        for court_id in courts_to_add:
            new_block = Block(
                court_id=court_id,
                date=new_date,
                start_time=new_start_time,
                end_time=new_end_time,
                reason_id=new_reason_id,
                sub_reason=new_sub_reason,
                batch_id=batch_id,  # Use the same batch_id
                created_by_id=current_user.id
            )
            db.session.add(new_block)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Batch-Sperrung erfolgreich aktualisiert: {len(new_court_ids)} Plätze',
            'courts_updated': len(courts_to_keep),
            'courts_added': len(courts_to_add),
            'courts_removed': len(courts_to_delete)
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
        
        # Get the deleted blocks info for response
        return jsonify({
            'message': 'Batch-Sperrung erfolgreich gelöscht'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/multi-court-delete/<int:primary_block_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_multi_court_blocks(primary_block_id):
    """Delete multi-court blocks (admin only)."""
    try:
        # Get the primary block to find all related blocks
        primary_block = Block.query.get_or_404(primary_block_id)
        
        # Find all related blocks (same date, time, reason, created_at - indicating they were created together)
        related_blocks = Block.query.filter(
            Block.date == primary_block.date,
            Block.start_time == primary_block.start_time,
            Block.end_time == primary_block.end_time,
            Block.reason_id == primary_block.reason_id,
            Block.sub_reason == primary_block.sub_reason,
            Block.created_at == primary_block.created_at
        ).all()
        
        # Get court numbers for the response message
        court_numbers = [block.court.number for block in related_blocks]
        
        # Delete all related blocks
        for block in related_blocks:
            db.session.delete(block)
        
        db.session.commit()
        
        if len(related_blocks) == 1:
            message = f'Sperrung für Platz {court_numbers[0]} erfolgreich gelöscht'
        else:
            courts_text = ', '.join(map(str, sorted(court_numbers)))
            message = f'Sperrung für Plätze {courts_text} erfolgreich gelöscht'
        
        return jsonify({
            'message': message,
            'deleted_blocks': len(related_blocks),
            'court_numbers': court_numbers
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_block(id):
    """Update block (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        block = Block.query.get_or_404(id)
        
        # Update fields if provided
        if 'date' in data:
            block.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        if 'start_time' in data:
            block.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        
        if 'end_time' in data:
            block.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        if 'reason_id' in data:
            block.reason_id = int(data['reason_id'])
        
        if 'sub_reason' in data:
            block.sub_reason = data['sub_reason'].strip() or None
        
        # Validate time range
        if block.start_time >= block.end_time:
            return jsonify({'error': 'Endzeit muss nach Startzeit liegen'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Sperrung erfolgreich aktualisiert',
            'block': {
                'id': block.id,
                'court_id': block.court_id,
                'court_number': block.court.number,
                'date': block.date.isoformat(),
                'start_time': block.start_time.strftime('%H:%M'),
                'end_time': block.end_time.strftime('%H:%M'),
                'reason_id': block.reason_id,
                'reason_name': block.reason_obj.name if block.reason_obj else 'Unknown',
                'sub_reason': block.sub_reason
            }
        }), 200
        
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


@bp.route('/blocks/<int:id>', methods=['GET'])
@login_required
@admin_required
def get_block(id):
    """Get single block details (admin only)."""
    try:
        block = Block.query.get_or_404(id)
        
        return jsonify({
            'block': {
                'id': block.id,
                'court_id': block.court_id,
                'court_number': block.court.number,
                'date': block.date.isoformat(),
                'start_time': block.start_time.strftime('%H:%M'),
                'end_time': block.end_time.strftime('%H:%M'),
                'reason_id': block.reason_id,
                'reason_name': block.reason_obj.name if block.reason_obj else 'Unknown',
                'sub_reason': block.sub_reason,
                'series_id': block.series_id,
                'is_modified': block.is_modified,
                'created_by': block.created_by.name,
                'created_at': block.created_at.isoformat()
            }
        }), 200
        
    except Exception as e:
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


# Recurring Block Series Routes

@bp.route('/blocks/series', methods=['GET'])
@login_required
@admin_required
def list_recurring_series():
    """List all recurring block series (admin only)."""
    try:
        series = BlockSeries.query.all()
        
        return jsonify({
            'series': [
                {
                    'id': serie.id,
                    'name': serie.name,
                    'start_date': serie.start_date.isoformat(),
                    'end_date': serie.end_date.isoformat(),
                    'start_time': serie.start_time.strftime('%H:%M'),
                    'end_time': serie.end_time.strftime('%H:%M'),
                    'recurrence_pattern': serie.recurrence_pattern,
                    'recurrence_days': serie.recurrence_days,
                    'reason_id': serie.reason_id,
                    'reason_name': serie.reason_obj.name if serie.reason_obj else 'Unknown',
                    'sub_reason': serie.sub_reason,
                    'court_selection': [1, 2, 3, 4, 5, 6],  # This would come from blocks
                    'total_instances': len(serie.blocks),
                    'active_instances': len([b for b in serie.blocks if b.date >= date.today()]),
                    'is_active': len([b for b in serie.blocks if b.date >= date.today()]) > 0,
                    'created_by': serie.created_by.name,
                    'created_at': serie.created_at.isoformat()
                }
                for serie in series
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/series', methods=['POST'])
@login_required
@admin_required
def create_recurring_series():
    """Create recurring block series (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        court_ids = data.get('court_ids', [])
        if isinstance(court_ids, str):
            court_ids = [int(x) for x in court_ids.split(',')]
        elif isinstance(court_ids, list):
            court_ids = [int(x) for x in court_ids]
        
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        recurrence_pattern = data.get('recurrence_pattern')
        recurrence_days = data.get('recurrence_days', [])
        reason_id = int(data.get('reason_id'))
        sub_reason = data.get('sub_reason', '').strip() or None
        series_name = data.get('series_name', '').strip()
        
        # Validate required fields
        if not all([court_ids, start_date_str, end_date_str, start_time_str, end_time_str, recurrence_pattern, reason_id, series_name]):
            return jsonify({'error': 'Alle Pflichtfelder sind erforderlich'}), 400
        
        # Parse dates and times
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Create recurring series
        blocks, error = BlockService.create_recurring_block_series(
            court_ids=court_ids,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            recurrence_pattern=recurrence_pattern,
            recurrence_days=recurrence_days,
            reason_id=reason_id,
            sub_reason=sub_reason,
            admin_id=current_user.id,
            series_name=series_name
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': f'Wiederkehrende Serie erfolgreich erstellt: {len(blocks)} Sperrungen',
            'series_name': series_name,
            'blocks_created': len(blocks)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/series/<int:series_id>', methods=['PUT'])
@login_required
@admin_required
def update_entire_series(series_id):
    """Update entire recurring series (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        updates = {}
        if 'start_time' in data:
            updates['start_time'] = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            updates['end_time'] = datetime.strptime(data['end_time'], '%H:%M').time()
        if 'reason_id' in data:
            updates['reason_id'] = int(data['reason_id'])
        if 'sub_reason' in data:
            updates['sub_reason'] = data['sub_reason'].strip() or None
        
        updates['admin_id'] = current_user.id
        
        success, error = BlockService.update_entire_series(series_id, **updates)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Gesamte Serie erfolgreich aktualisiert'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/series/<int:series_id>/future', methods=['PUT'])
@login_required
@admin_required
def update_future_series(series_id):
    """Update future instances of recurring series (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        from_date_str = data.get('from_date')
        if not from_date_str:
            return jsonify({'error': 'from_date ist erforderlich'}), 400
        
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        
        updates = {}
        if 'start_time' in data:
            updates['start_time'] = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            updates['end_time'] = datetime.strptime(data['end_time'], '%H:%M').time()
        if 'reason_id' in data:
            updates['reason_id'] = int(data['reason_id'])
        if 'sub_reason' in data:
            updates['sub_reason'] = data['sub_reason'].strip() or None
        
        updates['admin_id'] = current_user.id
        
        success, error = BlockService.update_future_series(series_id, from_date, **updates)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Zukünftige Instanzen erfolgreich aktualisiert'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/series/<int:series_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_series(series_id):
    """Delete recurring series with options (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        option = data.get('option', 'all')  # 'single', 'future', or 'all'
        from_date = None
        
        if option in ['single', 'future']:
            from_date_str = data.get('from_date')
            if not from_date_str:
                return jsonify({'error': 'from_date ist für diese Option erforderlich'}), 400
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        
        success, error = BlockService.delete_series_options(series_id, option, from_date)
        
        if error:
            return jsonify({'error': error}), 400
        
        messages = {
            'single': 'Einzelne Instanz erfolgreich gelöscht',
            'future': 'Zukünftige Instanzen erfolgreich gelöscht',
            'all': 'Gesamte Serie erfolgreich gelöscht'
        }
        
        return jsonify({'message': messages.get(option, 'Serie erfolgreich gelöscht')}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Multi-Court and Bulk Operations Routes

@bp.route('/blocks/multi-court-update/<int:primary_block_id>', methods=['PUT'])
@login_required
@admin_required
def update_multi_court_blocks(primary_block_id):
    """Update multi-court blocks (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Get the primary block to find all related blocks
        primary_block = Block.query.get_or_404(primary_block_id)
        
        # Find all related blocks (same date, time, reason, created_at)
        related_blocks = Block.query.filter(
            Block.date == primary_block.date,
            Block.start_time == primary_block.start_time,
            Block.end_time == primary_block.end_time,
            Block.reason_id == primary_block.reason_id,
            Block.sub_reason == primary_block.sub_reason,
            Block.created_at == primary_block.created_at
        ).all()
        
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
        new_sub_reason = data.get('sub_reason', '').strip() or None
        
        # Validate time range
        if new_start_time >= new_end_time:
            return jsonify({'error': 'Endzeit muss nach Startzeit liegen'}), 400
        
        # Get current court IDs
        current_court_ids = [block.court_id for block in related_blocks]
        
        # Determine which blocks to delete, update, and create
        courts_to_delete = set(current_court_ids) - set(new_court_ids)
        courts_to_keep = set(current_court_ids) & set(new_court_ids)
        courts_to_add = set(new_court_ids) - set(current_court_ids)
        
        # Delete blocks for courts that are no longer selected
        for block in related_blocks:
            if block.court_id in courts_to_delete:
                db.session.delete(block)
        
        # Update existing blocks for courts that are kept
        for block in related_blocks:
            if block.court_id in courts_to_keep:
                block.date = new_date
                block.start_time = new_start_time
                block.end_time = new_end_time
                block.reason_id = new_reason_id
                block.sub_reason = new_sub_reason
        
        # Create new blocks for newly selected courts
        for court_id in courts_to_add:
            new_block = Block(
                court_id=court_id,
                date=new_date,
                start_time=new_start_time,
                end_time=new_end_time,
                reason_id=new_reason_id,
                sub_reason=new_sub_reason,
                created_by_id=current_user.id
            )
            db.session.add(new_block)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Mehrplatz-Sperrung erfolgreich aktualisiert: {len(new_court_ids)} Plätze',
            'courts_updated': len(courts_to_keep),
            'courts_added': len(courts_to_add),
            'courts_removed': len(courts_to_delete)
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
        sub_reason = data.get('sub_reason', '').strip() or None
        
        # Validate required fields
        if not all([court_ids, date_str, start_time_str, end_time_str, reason_id]):
            return jsonify({'error': 'Alle Pflichtfelder sind erforderlich'}), 400
        
        # Parse date and times
        block_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Validate that the date is not in the past
        today = datetime.now().date()
        if block_date < today:
            return jsonify({'error': 'Sperrungen können nicht für vergangene Tage erstellt werden'}), 400
        
        # Create multi-court blocks
        blocks, error = BlockService.create_multi_court_blocks(
            court_ids=court_ids,
            date=block_date,
            start_time=start_time,
            end_time=end_time,
            reason_id=reason_id,
            sub_reason=sub_reason,
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
    """Bulk delete selected blocks (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        block_ids = data.get('block_ids', [])
        if isinstance(block_ids, str):
            block_ids = [int(x) for x in block_ids.split(',')]
        elif isinstance(block_ids, list):
            block_ids = [int(x) for x in block_ids]
        
        if not block_ids:
            return jsonify({'error': 'Keine Sperrungen zum Löschen ausgewählt'}), 400
        
        success, error = BlockService.bulk_delete_blocks(block_ids, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': f'Erfolgreich {len(block_ids)} Sperrungen gelöscht'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
        return jsonify({'error': str(e)}), 500


@bp.route('/blocks/conflict-preview', methods=['POST'])
@login_required
@admin_required
def get_conflict_preview():
    """Preview reservations that would be affected by creating blocks (admin only)."""
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
        
        # Validate required fields
        if not all([court_ids, date_str, start_time_str, end_time_str]):
            return jsonify({'error': 'Alle Felder sind erforderlich'}), 400
        
        # Parse date and times
        block_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Get conflict preview
        conflicting_reservations = BlockService.get_conflict_preview(
            court_ids=court_ids,
            date=block_date,
            start_time=start_time,
            end_time=end_time
        )
        
        return jsonify({
            'conflicts': [
                {
                    'id': reservation.id,
                    'court_id': reservation.court_id,
                    'court_number': reservation.court.number,
                    'date': reservation.date.isoformat(),
                    'start_time': reservation.start_time.strftime('%H:%M'),
                    'end_time': reservation.end_time.strftime('%H:%M'),
                    'booked_for': reservation.booked_for.name,
                    'booked_by': reservation.booked_by.name
                }
                for reservation in conflicting_reservations
            ],
            'conflict_count': len(conflicting_reservations)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Block Template Routes

@bp.route('/block-templates', methods=['GET'])
@login_required
@admin_required
def list_block_templates():
    """List all block templates (admin only)."""
    try:
        templates = BlockService.get_block_templates()
        
        return jsonify({
            'templates': [
                {
                    'id': template.id,
                    'name': template.name,
                    'court_selection': template.court_selection,
                    'start_time': template.start_time.strftime('%H:%M'),
                    'end_time': template.end_time.strftime('%H:%M'),
                    'reason_id': template.reason_id,
                    'reason_name': template.reason_obj.name if template.reason_obj else 'Unknown',
                    'sub_reason': template.sub_reason,
                    'recurrence_pattern': template.recurrence_pattern,
                    'recurrence_days': template.recurrence_days,
                    'created_by': template.created_by.name,
                    'created_at': template.created_at.isoformat()
                }
                for template in templates
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/block-templates', methods=['POST'])
@login_required
@admin_required
def create_block_template():
    """Create block template (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name', '').strip()
        court_selection = data.get('court_selection', [])
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        reason_id = int(data.get('reason_id'))
        sub_reason = data.get('sub_reason', '').strip() or None
        recurrence_pattern = data.get('recurrence_pattern', '').strip() or None
        recurrence_days = data.get('recurrence_days', [])
        
        # Validate required fields
        if not all([name, court_selection, start_time_str, end_time_str, reason_id]):
            return jsonify({'error': 'Alle Pflichtfelder sind erforderlich'}), 400
        
        # Parse times
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Prepare template data
        template_data = {
            'court_selection': court_selection,
            'start_time': start_time,
            'end_time': end_time,
            'reason_id': reason_id,
            'sub_reason': sub_reason,
            'recurrence_pattern': recurrence_pattern,
            'recurrence_days': recurrence_days
        }
        
        # Create template
        template, error = BlockService.create_block_template(name, template_data, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'id': template.id,
            'message': 'Vorlage erfolgreich erstellt',
            'template': {
                'id': template.id,
                'name': template.name,
                'court_selection': template.court_selection,
                'start_time': template.start_time.strftime('%H:%M'),
                'end_time': template.end_time.strftime('%H:%M'),
                'reason_id': template.reason_id,
                'sub_reason': template.sub_reason,
                'recurrence_pattern': template.recurrence_pattern,
                'recurrence_days': template.recurrence_days
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/block-templates/<int:template_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_block_template(template_id):
    """Delete block template (admin only)."""
    try:
        success, error = BlockService.delete_block_template(template_id, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Vorlage erfolgreich gelöscht'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/block-templates/<int:template_id>/apply', methods=['POST'])
@login_required
@admin_required
def apply_block_template(template_id):
    """Apply block template with date overrides (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        date_overrides = {}
        if 'start_date' in data:
            date_overrides['start_date'] = data['start_date']
        if 'end_date' in data:
            date_overrides['end_date'] = data['end_date']
        
        form_data = BlockService.apply_block_template(template_id, date_overrides)
        
        if form_data is None:
            return jsonify({'error': 'Vorlage nicht gefunden'}), 404
        
        return jsonify({
            'message': 'Vorlage erfolgreich angewendet',
            'form_data': form_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Block Reason Management Routes

@bp.route('/block-reasons', methods=['GET'])
@login_required
@admin_required
def list_block_reasons():
    """List all block reasons (admin only)."""
    try:
        reasons = BlockReasonService.get_all_block_reasons()
        
        return jsonify({
            'reasons': [
                {
                    'id': reason.id,
                    'name': reason.name,
                    'is_active': reason.is_active,
                    'usage_count': BlockReasonService.get_reason_usage_count(reason.id),
                    'created_by': reason.created_by.name,
                    'created_at': reason.created_at.isoformat()
                }
                for reason in reasons
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/block-reasons', methods=['POST'])
@login_required
@admin_required
def create_block_reason():
    """Create block reason (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'error': 'Name ist erforderlich'}), 400
        
        reason, error = BlockReasonService.create_block_reason(name, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'id': reason.id,
            'message': 'Sperrungsgrund erfolgreich erstellt',
            'reason': {
                'id': reason.id,
                'name': reason.name,
                'is_active': reason.is_active
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/block-reasons/<int:reason_id>', methods=['PUT'])
@login_required
@admin_required
def update_block_reason(reason_id):
    """Update block reason (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'error': 'Name ist erforderlich'}), 400
        
        success, error = BlockReasonService.update_block_reason(reason_id, name, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Sperrungsgrund erfolgreich aktualisiert'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/block-reasons/<int:reason_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_block_reason(reason_id):
    """Delete block reason with usage check (admin only)."""
    try:
        success, error_or_message = BlockReasonService.delete_block_reason(reason_id, current_user.id)
        
        if not success:
            return jsonify({'error': error_or_message}), 400
        
        # If there's a message, it means the reason was deactivated instead of deleted
        if error_or_message:
            return jsonify({'message': error_or_message, 'deactivated': True}), 200
        else:
            return jsonify({'message': 'Sperrungsgrund erfolgreich gelöscht', 'deleted': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/block-reasons/<int:reason_id>/usage', methods=['GET'])
@login_required
@admin_required
def get_reason_usage(reason_id):
    """Get usage count for a block reason (admin only)."""
    try:
        usage_count = BlockReasonService.get_reason_usage_count(reason_id)
        
        return jsonify({
            'reason_id': reason_id,
            'usage_count': usage_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Sub-Reason Template Routes

@bp.route('/block-reasons/<int:reason_id>/sub-reason-templates', methods=['GET'])
@login_required
@admin_required
def list_sub_reason_templates(reason_id):
    """List sub-reason templates for a block reason (admin only)."""
    try:
        templates = BlockReasonService.get_sub_reason_templates(reason_id)
        
        return jsonify({
            'reason_id': reason_id,
            'templates': [
                {
                    'id': template.id,
                    'template_name': template.template_name,
                    'created_by': template.created_by.name,
                    'created_at': template.created_at.isoformat()
                }
                for template in templates
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/block-reasons/<int:reason_id>/sub-reason-templates', methods=['POST'])
@login_required
@admin_required
def create_sub_reason_template(reason_id):
    """Create sub-reason template (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        template_name = data.get('template_name', '').strip()
        
        if not template_name:
            return jsonify({'error': 'Vorlagenname ist erforderlich'}), 400
        
        template, error = BlockReasonService.create_sub_reason_template(reason_id, template_name, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'id': template.id,
            'message': 'Untergrund-Vorlage erfolgreich erstellt',
            'template': {
                'id': template.id,
                'template_name': template.template_name,
                'reason_id': template.reason_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/sub-reason-templates/<int:template_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_sub_reason_template(template_id):
    """Delete sub-reason template (admin only)."""
    try:
        success, error = BlockReasonService.delete_sub_reason_template(template_id, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Untergrund-Vorlage erfolgreich gelöscht'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Audit Log Routes

@bp.route('/blocks/audit-log', methods=['GET'])
@login_required
@admin_required
def get_audit_log():
    """Get block operation audit log (admin only)."""
    try:
        filters = {}
        
        # Optional filters
        if request.args.get('admin_id'):
            filters['admin_id'] = int(request.args.get('admin_id'))
        
        if request.args.get('operation'):
            filters['operation'] = request.args.get('operation')
        
        if request.args.get('date_range_start') and request.args.get('date_range_end'):
            start_date = datetime.strptime(request.args.get('date_range_start'), '%Y-%m-%d')
            end_date = datetime.strptime(request.args.get('date_range_end'), '%Y-%m-%d')
            filters['date_range'] = (start_date, end_date)
        
        audit_logs = BlockService.get_audit_log(filters if filters else None)
        
        return jsonify({
            'audit_logs': [
                {
                    'id': log.id,
                    'operation': log.operation,
                    'block_id': log.block_id,
                    'series_id': log.series_id,
                    'operation_data': log.operation_data,
                    'admin_name': log.admin.name,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in audit_logs
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500