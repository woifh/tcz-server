"""
Admin Audit Module

Contains unified audit log functionality for admin operations.
"""

from datetime import datetime
from flask import request, jsonify
from flask_login import login_required, current_user

from app.decorators import admin_required
from app.models import BlockAuditLog, MemberAuditLog
from app import db
from . import bp


def format_block_details(operation, data):
    """Format block audit log details into human-readable text."""
    if not data:
        return '-'

    if operation == 'create':
        court_ids = data.get('court_ids', [])
        date = data.get('date', '')
        start = data.get('start_time', '')
        end = data.get('end_time', '')
        reason = data.get('reason_name', data.get('reason_id', ''))
        details = data.get('details', '')

        # Format date from ISO to German format
        if date:
            try:
                date_obj = datetime.fromisoformat(date)
                date = date_obj.strftime('%d.%m.%Y')
            except (ValueError, TypeError):
                pass

        # Format time (remove seconds if present)
        if start and len(start) > 5:
            start = start[:5]
        if end and len(end) > 5:
            end = end[:5]

        if len(court_ids) == 1:
            courts_text = f"Platz {court_ids[0]}"
        elif len(court_ids) > 1:
            courts_text = f"Plätze {', '.join(map(str, court_ids))}"
        else:
            courts_text = "Platz"

        result = f"{courts_text} gesperrt am {date} {start}-{end}"
        if reason:
            result += f" ({reason})"
        if details:
            result += f" - {details}"
        return result

    elif operation == 'update':
        updates = data.get('updates', {})
        if updates:
            changes = []
            for key, value in updates.items():
                if key == 'date':
                    changes.append(f"Datum: {value}")
                elif key == 'start_time':
                    changes.append(f"Start: {value}")
                elif key == 'end_time':
                    changes.append(f"Ende: {value}")
                elif key == 'reason_id':
                    changes.append(f"Grund geändert")
                elif key == 'details':
                    changes.append(f"Details: {value}")
            return f"Sperrung aktualisiert: {', '.join(changes)}" if changes else "Sperrung aktualisiert"
        return "Sperrung aktualisiert"

    elif operation == 'delete':
        court_numbers = data.get('court_numbers', [])
        date = data.get('date', '')
        batch_id = data.get('batch_id', '')
        blocks_deleted = data.get('blocks_deleted', 0)

        if date:
            try:
                date_obj = datetime.fromisoformat(date)
                date = date_obj.strftime('%d.%m.%Y')
            except (ValueError, TypeError):
                pass

        if court_numbers:
            if len(court_numbers) == 1:
                return f"Sperrung gelöscht: Platz {court_numbers[0]} am {date}"
            else:
                return f"Sperrung gelöscht: Plätze {', '.join(map(str, court_numbers))} am {date}"
        elif blocks_deleted:
            return f"{blocks_deleted} Sperrung(en) gelöscht"
        return "Sperrung gelöscht"

    return '-'


def format_member_details(operation, data):
    """Format member audit log details into human-readable text."""
    if not data:
        return '-'

    firstname = data.get('firstname', '')
    lastname = data.get('lastname', '')
    name = f"{firstname} {lastname}".strip() or data.get('name', 'Unbekannt')

    if operation == 'create':
        email = data.get('email', '')
        role = data.get('role', '')
        role_text = {
            'administrator': 'Administrator',
            'teamster': 'Mannschaftsführer',
            'member': 'Mitglied'
        }.get(role, role)
        result = f"Mitglied erstellt: {name}"
        if role_text:
            result += f" ({role_text})"
        return result

    elif operation == 'update':
        changes = data.get('changes', {})
        if changes:
            change_texts = []
            for field, vals in changes.items():
                if isinstance(vals, dict) and 'old' in vals and 'new' in vals:
                    change_texts.append(f"{field}: {vals['old']} → {vals['new']}")
            if change_texts:
                return f"Mitglied aktualisiert: {name} - {', '.join(change_texts)}"
        return f"Mitglied aktualisiert: {name}"

    elif operation == 'delete':
        return f"Mitglied gelöscht: {name}"

    elif operation == 'role_change':
        changes = data.get('changes', {})
        role_change = changes.get('role', {})
        if isinstance(role_change, dict):
            old_role = role_change.get('old', '')
            new_role = role_change.get('new', '')
            role_map = {
                'administrator': 'Administrator',
                'teamster': 'Mannschaftsführer',
                'member': 'Mitglied'
            }
            return f"Rolle geändert: {name} ({role_map.get(old_role, old_role)} → {role_map.get(new_role, new_role)})"
        return f"Rolle geändert: {name}"

    elif operation == 'membership_change':
        changes = data.get('changes', {})
        membership_change = changes.get('membership_type', {})
        if isinstance(membership_change, dict):
            old_type = membership_change.get('old', '')
            new_type = membership_change.get('new', '')
            type_map = {
                'full': 'Vollmitglied',
                'supporting': 'Fördermitglied'
            }
            return f"Mitgliedschaft geändert: {name} ({type_map.get(old_type, old_type)} → {type_map.get(new_type, new_type)})"
        return f"Mitgliedschaft geändert: {name}"

    elif operation == 'payment_update':
        changes = data.get('changes', {})
        fee_change = changes.get('fee_paid', {})
        if isinstance(fee_change, dict):
            new_status = fee_change.get('new', False)
            status_text = "bezahlt" if new_status else "offen"
            return f"Beitragsstatus geändert: {name} → {status_text}"
        return f"Beitragsstatus geändert: {name}"

    elif operation == 'deactivate':
        return f"Mitglied deaktiviert: {name}"

    elif operation == 'reactivate':
        return f"Mitglied reaktiviert: {name}"

    return '-'


@bp.route('/blocks/audit-log', methods=['GET'])
@login_required
@admin_required
def get_audit_log():
    """Get unified audit log combining block and member operations (admin only)."""
    try:
        # Get filter parameters
        log_type = request.args.get('type')  # 'block', 'member', or None for all
        limit = min(int(request.args.get('limit', 100)), 500)  # Max 500 entries

        logs = []

        # Query BlockAuditLog if not filtered to members only
        if log_type != 'member':
            block_logs = BlockAuditLog.query.order_by(BlockAuditLog.timestamp.desc()).limit(limit).all()
            for log in block_logs:
                logs.append({
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.operation,
                    'user': log.admin.name if log.admin else 'System',
                    'details': format_block_details(log.operation, log.operation_data),
                    'type': 'block'
                })

        # Query MemberAuditLog if not filtered to blocks only
        if log_type != 'block':
            member_logs = MemberAuditLog.query.order_by(MemberAuditLog.timestamp.desc()).limit(limit).all()
            for log in member_logs:
                logs.append({
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.operation,
                    'user': log.performed_by.name if log.performed_by else 'System',
                    'details': format_member_details(log.operation, log.operation_data),
                    'type': 'member'
                })

        # Sort combined logs by timestamp descending
        logs.sort(key=lambda x: x['timestamp'], reverse=True)

        # Apply limit to combined result
        logs = logs[:limit]

        return jsonify({
            'success': True,
            'logs': logs
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
