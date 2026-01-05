"""
Admin Reasons Module

Contains block reason and details management routes.
"""

from flask import request, jsonify
from flask_login import login_required, current_user

from app import db
from app.decorators import admin_required
from app.models import BlockReason, DetailsTemplate
from app.services.block_reason_service import BlockReasonService
from . import bp


@bp.route('/block-reasons', methods=['GET'])
@login_required
@admin_required
def list_block_reasons():
    """List all block reasons (admin only)."""
    try:
        reasons = BlockReasonService.get_all_block_reasons()
        
        reasons_data = []
        for reason in reasons:
            reason_data = {
                'id': reason.id,
                'name': reason.name,
                'color': '#007bff',  # Default color since model doesn't have this field
                'is_active': reason.is_active,
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
        
        if not name:
            return jsonify({'error': 'Name ist erforderlich'}), 400
        
        # Check if reason with same name exists
        existing = BlockReason.query.filter_by(name=name).first()
        if existing:
            return jsonify({'error': 'Ein Grund mit diesem Namen existiert bereits'}), 400
        
        # Create the reason using the service
        reason, error = BlockReasonService.create_block_reason(
            name=name,
            admin_id=current_user.id
        )
        
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
        
        name = data.get('name', '').strip() if data.get('name') else ''
        
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


@bp.route('/block-reasons/<int:reason_id>/details-templates', methods=['GET'])
@login_required
@admin_required
def list_details_templates(reason_id):
    """List details templates for a block reason (admin only)."""
    try:
        templates = BlockReasonService.get_details_templates(reason_id)
        
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


@bp.route('/block-reasons/<int:reason_id>/details-templates', methods=['POST'])
@login_required
@admin_required
def create_details_template(reason_id):
    """Create details template (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        template_name = data.get('template_name', '').strip() if data.get('template_name') else ''
        
        if not template_name:
            return jsonify({'error': 'Vorlagenname ist erforderlich'}), 400
        
        template, error = BlockReasonService.create_details_template(reason_id, template_name, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'id': template.id,
            'message': 'Details-Vorlage erfolgreich erstellt',
            'template': {
                'id': template.id,
                'template_name': template.template_name,
                'reason_id': template.reason_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/details-templates/<int:template_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_details_template(template_id):
    """Delete details template (admin only)."""
    try:
        success, error = BlockReasonService.delete_details_template(template_id, current_user.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Details-Vorlage erfolgreich gelöscht'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500