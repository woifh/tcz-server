"""
Admin Views Module

Contains main admin pages and navigation routes.
"""

from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user

from app.decorators import admin_required, teamster_or_admin_required
from app.models import Block, BlockReason, Member
from app.services.block_service import BlockService
from app.services.block_reason_service import BlockReasonService
from app.services.member_service import MemberService
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
@teamster_or_admin_required
def court_blocking():
    """Court blocking management page."""
    return render_template('admin/court_blocking.html')


@bp.route('/court-blocking/<batch_id>')
@login_required
@teamster_or_admin_required
def edit_court_blocking(batch_id):
    """Edit court blocking page."""
    try:
        # Get all blocks in the batch
        blocks = Block.query.filter_by(batch_id=batch_id).all()

        if not blocks:
            return render_template('admin/court_blocking.html',
                                 error="Sperrung nicht gefunden")

        # Check ownership for teamsters
        if current_user.is_teamster():
            if not all(block.created_by_id == current_user.id for block in blocks):
                return render_template('admin/court_blocking.html',
                                     error="Sie können nur Ihre eigenen Sperrungen bearbeiten")

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


@bp.route('/changelog')
@login_required
@admin_required
def changelog():
    """Changelog viewing page."""
    return render_template('admin/changelog.html')


@bp.route('/api/changelog')
@login_required
@admin_required
def get_changelog_api():
    """API endpoint for changelog data."""
    from app.services.changelog_service import ChangelogService

    entries, error = ChangelogService.get_changelog_as_dict()

    if error:
        return jsonify({
            'success': False,
            'error': error
        }), 500

    return jsonify({
        'success': True,
        'entries': entries
    })


@bp.route('/settings/payment-deadline', methods=['GET'])
@login_required
@admin_required
def get_payment_deadline():
    """Get current payment deadline settings."""
    from app.services.settings_service import SettingsService

    deadline = SettingsService.get_payment_deadline()
    days_until = SettingsService.days_until_deadline()
    unpaid_count = SettingsService.get_unpaid_member_count()

    return jsonify({
        'deadline': deadline.isoformat() if deadline else None,
        'days_until': days_until,
        'unpaid_count': unpaid_count,
        'is_past': SettingsService.is_past_payment_deadline()
    })


@bp.route('/settings/payment-deadline', methods=['POST'])
@login_required
@admin_required
def set_payment_deadline():
    """Set or clear payment deadline."""
    from datetime import datetime
    from app.services.settings_service import SettingsService
    from app.constants.messages import ErrorMessages, SuccessMessages

    data = request.get_json() if request.is_json else request.form

    deadline_str = data.get('deadline')

    # If no deadline provided, clear it
    if not deadline_str:
        success, error = SettingsService.clear_payment_deadline(current_user.id)
        if success:
            return jsonify({'message': SuccessMessages.PAYMENT_DEADLINE_CLEARED}), 200
        return jsonify({'error': error}), 400

    # Parse and set the deadline
    try:
        deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': ErrorMessages.PAYMENT_DEADLINE_INVALID_DATE}), 400

    success, error = SettingsService.set_payment_deadline(deadline_date, current_user.id)

    if success:
        return jsonify({
            'message': SuccessMessages.PAYMENT_DEADLINE_SET,
            'deadline': deadline_date.isoformat()
        }), 200

    return jsonify({'error': error}), 400


@bp.route('/settings/payment-deadline', methods=['DELETE'])
@login_required
@admin_required
def clear_payment_deadline():
    """Clear payment deadline."""
    from app.services.settings_service import SettingsService
    from app.constants.messages import SuccessMessages

    success, error = SettingsService.clear_payment_deadline(current_user.id)

    if success:
        return jsonify({'message': SuccessMessages.PAYMENT_DEADLINE_CLEARED}), 200

    return jsonify({'error': error}), 400


@bp.route('/import-members', methods=['POST'])
@login_required
@admin_required
def import_members():
    """Import members from CSV file."""
    from app.constants.messages import ErrorMessages, SuccessMessages

    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': ErrorMessages.CSV_NO_FILE}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': ErrorMessages.CSV_NO_FILE}), 400

    try:
        # Read file content
        csv_content = file.read().decode('utf-8')

        if not csv_content.strip():
            return jsonify({'error': ErrorMessages.CSV_EMPTY_FILE}), 400

        # Import members
        results, error = MemberService.import_members_from_csv(csv_content, current_user.id)

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': SuccessMessages.CSV_IMPORT_SUCCESS,
            'imported': results['imported'],
            'skipped': results['skipped'],
            'errors': results['errors']
        }), 200

    except UnicodeDecodeError:
        return jsonify({'error': 'Datei konnte nicht gelesen werden. Bitte stellen Sie sicher, dass die Datei UTF-8 kodiert ist.'}), 400
    except Exception as e:
        return jsonify({'error': f'{ErrorMessages.CSV_IMPORT_FAILED}: {str(e)}'}), 500


@bp.route('/member')
@login_required
@admin_required
def member_create():
    """Member create page."""
    return render_template('admin/member.html')


@bp.route('/member/<member_id>')
@login_required
@admin_required
def member_edit(member_id):
    """Member edit page."""
    # Just pass the member_id; data will be fetched via API
    return render_template('admin/member.html', member_id=member_id)