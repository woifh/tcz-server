"""
Admin Views Module

Contains main admin pages and navigation routes.
"""

from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user

from app.decorators import admin_required
from app.models import Block, BlockReason, Member
from app.services.block_service import BlockService
from app.services.block_reason_service import BlockReasonService
from . import bp


@bp.route('/')
@login_required
@admin_required
def index():
    """Admin panel overview - redirect to overview page."""
    return redirect(url_for('admin.overview'))


@bp.route('/overview')
@login_required
@admin_required
def overview():
    """Admin overview page."""
    return render_template('admin.html')


@bp.route('/court-blocking')
@login_required
@admin_required
def court_blocking():
    """Court blocking management page."""
    return render_template('admin/court_blocking.html')


@bp.route('/court-blocking/<batch_id>')
@login_required
@admin_required
def edit_court_blocking(batch_id):
    """Edit court blocking page."""
    try:
        # Get all blocks in the batch
        blocks = Block.query.filter_by(batch_id=batch_id).all()
        
        if not blocks:
            return render_template('admin/court_blocking.html', 
                                 error="Sperrung nicht gefunden")
        
        # Use the first block as the representative for the batch
        first_block = blocks[0]
        
        # Collect all court IDs for this batch
        court_ids = [block.court_id for block in blocks]
        
        # Create edit data structure
        edit_block_data = {
            'id': first_block.id,
            'batch_id': batch_id,
            'court_ids': court_ids,
            'date': first_block.date,
            'start_time': first_block.start_time,
            'end_time': first_block.end_time,
            'reason_id': first_block.reason_id,
            'details': first_block.details,
            'related_block_ids': [block.id for block in blocks]
        }
        
        return render_template('admin/court_blocking.html', 
                             edit_block_data=edit_block_data)
        
    except Exception as e:
        return render_template('admin/court_blocking.html', 
                             error=f"Fehler beim Laden der Sperrung: {str(e)}")


@bp.route('/court-blocking/<int:block_id>')
@login_required
@admin_required
def edit_single_block(block_id):
    """Edit single block page (legacy route)."""
    try:
        block = Block.query.get_or_404(block_id)
        # Redirect to batch edit using batch_id
        return redirect(url_for('admin.edit_court_blocking', batch_id=block.batch_id))
    except Exception as e:
        return render_template('admin/court_blocking.html', 
                             error=f"Fehler beim Laden der Sperrung: {str(e)}")


@bp.route('/calendar')
@login_required
@admin_required
def calendar():
    """Admin calendar view."""
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
    """Block templates management page."""
    return render_template('admin/templates.html')


@bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    """Audit log viewing page."""
    return render_template('admin/audit_log.html')


@bp.route('/reasons')
@login_required
@admin_required
def reasons():
    """Block reasons management page."""
    return render_template('admin/reasons.html')