"""
Admin Reasons Module

Contains block reason and details management routes.
"""

from flask import request, jsonify
from flask_login import login_required, current_user

from app import db
from app.decorators import admin_required, teamster_or_admin_required
from app.models import BlockReason, ReasonAuditLog
from app.services.block_reason_service import BlockReasonService
from . import bp


def log_reason_operation(operation, reason_id, operation_data, performed_by_id):
    """Log a reason operation for audit purposes."""
    try:
        audit_log = ReasonAuditLog(
            operation=operation,
            reason_id=reason_id,
            operation_data=operation_data,
            performed_by_id=performed_by_id
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        # Don't let audit logging failure affect the main operation
        db.session.rollback()
        print(f"Failed to log reason operation: {e}")


@bp.route('/block-reasons', methods=['GET'])
@login_required
@teamster_or_admin_required
def list_block_reasons():
    """
    List block reasons based on user role.
    - Admins see all reasons (including inactive) with full details
    - Teamsters see only active teamster-usable reasons
    """
    try:
        # Get reasons based on user role
        if current_user.is_admin():
            # Admins see all reasons including inactive
            reasons = BlockReasonService.get_all_block_reasons(include_inactive=True)
        else:
            # Teamsters only see active teamster-usable reasons
            reasons = BlockReasonService.get_reasons_for_user(current_user)

        reasons_data = []
        for reason in reasons:
            reason_data = {
                'id': reason.id,
                'name': reason.name,
                'color': '#007bff',  # Default color since model doesn't have this field
                'is_active': reason.is_active,
                'teamster_usable': reason.teamster_usable,
                'usage_count': BlockReasonService.get_reason_usage_count(reason.id),
                'created_by': reason.created_by.name,
                'created_at': reason.created_at.isoformat()
            }
            reasons_data.append(reason_data)

        return jsonify({'reasons': reasons_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/block-reasons', methods=['POST'])
@login_required
@admin_required
def create_block_reason():
    """Create block reason (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form

        name = data.get('name', '').strip() if data.get('name') else ''
        teamster_usable = data.get('teamster_usable', False)

        # Convert string 'true'/'false' to boolean if needed
        if isinstance(teamster_usable, str):
            teamster_usable = teamster_usable.lower() in ('true', '1', 'yes')

        if not name:
            return jsonify({'error': 'Name ist erforderlich'}), 400

        # Check if reason with same name exists
        existing = BlockReason.query.filter_by(name=name).first()
        if existing:
            return jsonify({'error': 'Ein Grund mit diesem Namen existiert bereits'}), 400

        # Create the reason using the service
        reason, error = BlockReasonService.create_block_reason(
            name=name,
            admin_id=current_user.id,
            teamster_usable=teamster_usable
        )

        if error:
            return jsonify({'error': error}), 400

        # Log the operation
        log_reason_operation(
            operation='create',
            reason_id=reason.id,
            operation_data={
                'name': reason.name,
                'teamster_usable': reason.teamster_usable
            },
            performed_by_id=current_user.id
        )

        return jsonify({
            'id': reason.id,
            'message': 'Sperrungsgrund erfolgreich erstellt',
            'reason': {
                'id': reason.id,
                'name': reason.name,
                'is_active': reason.is_active,
                'teamster_usable': reason.teamster_usable
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

        name = data.get('name', '').strip() if data.get('name') else None
        teamster_usable = data.get('teamster_usable')

        # Convert string 'true'/'false' to boolean if provided
        if teamster_usable is not None and isinstance(teamster_usable, str):
            teamster_usable = teamster_usable.lower() in ('true', '1', 'yes')

        # Validate name if provided
        if name is not None and not name:
            return jsonify({'error': 'Name ist erforderlich'}), 400

        # Get old values for audit log
        reason = BlockReason.query.get(reason_id)
        old_values = {
            'name': reason.name if reason else None,
            'teamster_usable': reason.teamster_usable if reason else None
        } if reason else {}

        # Update the reason
        success, error = BlockReasonService.update_block_reason(
            reason_id=reason_id,
            name=name,
            teamster_usable=teamster_usable,
            admin_id=current_user.id
        )

        if error:
            return jsonify({'error': error}), 400

        # Log the operation with changes
        changes = {}
        if name is not None and name != old_values.get('name'):
            changes['name'] = {'old': old_values.get('name'), 'new': name}
        if teamster_usable is not None and teamster_usable != old_values.get('teamster_usable'):
            changes['teamster_usable'] = {'old': old_values.get('teamster_usable'), 'new': teamster_usable}

        if changes:
            log_reason_operation(
                operation='update',
                reason_id=reason_id,
                operation_data={'changes': changes, 'name': name or old_values.get('name')},
                performed_by_id=current_user.id
            )

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
        # Get reason name before deletion for audit log
        reason = BlockReason.query.get(reason_id)
        reason_name = reason.name if reason else 'Unbekannt'

        success, error_or_message = BlockReasonService.delete_block_reason(reason_id, current_user.id)

        if not success:
            return jsonify({'error': error_or_message}), 400

        # If there's a message, it means the reason was deactivated instead of deleted
        if error_or_message:
            # Log deactivation
            log_reason_operation(
                operation='deactivate',
                reason_id=reason_id,
                operation_data={'name': reason_name},
                performed_by_id=current_user.id
            )
            return jsonify({'message': error_or_message, 'deactivated': True}), 200
        else:
            # Log deletion
            log_reason_operation(
                operation='delete',
                reason_id=reason_id,
                operation_data={'name': reason_name},
                performed_by_id=current_user.id
            )
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


@bp.route('/block-reasons/<int:reason_id>/reactivate', methods=['POST'])
@login_required
@admin_required
def reactivate_block_reason(reason_id):
    """Reactivate an inactive block reason (admin only)."""
    try:
        reason = BlockReason.query.get(reason_id)
        if not reason:
            return jsonify({'error': 'Sperrungsgrund nicht gefunden'}), 404

        success, error = BlockReasonService.reactivate_block_reason(reason_id, current_user.id)

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'Sperrungsgrund erfolgreich reaktiviert',
            'reason': {
                'id': reason.id,
                'name': reason.name,
                'is_active': True,
                'teamster_usable': reason.teamster_usable
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/block-reasons/<int:reason_id>/permanent', methods=['DELETE'])
@login_required
@admin_required
def permanently_delete_block_reason(reason_id):
    """Permanently delete a block reason (admin only)."""
    try:
        reason = BlockReason.query.get(reason_id)
        if not reason:
            return jsonify({'error': 'Sperrungsgrund nicht gefunden'}), 404

        reason_name = reason.name
        success, error = BlockReasonService.permanently_delete_block_reason(reason_id, current_user.id)

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': f"Sperrungsgrund '{reason_name}' wurde endgültig gelöscht",
            'deleted': True
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
