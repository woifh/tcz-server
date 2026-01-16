"""
Admin Audit Module

Contains unified audit log functionality for admin operations.
"""

from datetime import datetime
from flask import request, jsonify
from flask_login import login_required, current_user

from app.decorators import admin_required
from app.models import BlockAuditLog, MemberAuditLog, ReasonAuditLog, ReservationAuditLog, Member, BlockReason, Court
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


def format_member_details(operation, data, member_id=None):
    """Format member audit log details into human-readable text."""
    if not data:
        return '-'

    firstname = data.get('firstname', '')
    lastname = data.get('lastname', '')
    name = f"{firstname} {lastname}".strip() or data.get('name', '')

    # If name not in operation_data, try to look up the member
    if not name and member_id:
        member = Member.query.get(member_id)
        if member:
            name = member.name

    name = name or 'Gelöschtes Mitglied'

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

    elif operation == 'add_favourite':
        member_name = data.get('member_name', '')
        favourite_name = data.get('favourite_name', '')
        return f"Favorit hinzugefügt: {member_name} → {favourite_name}"

    elif operation == 'remove_favourite':
        member_name = data.get('member_name', '')
        favourite_name = data.get('favourite_name', '')
        return f"Favorit entfernt: {member_name} → {favourite_name}"

    elif operation == 'csv_import':
        imported = data.get('imported', 0)
        skipped = data.get('skipped', 0)
        return f"CSV-Import: {imported} importiert, {skipped} übersprungen"

    elif operation == 'annual_fee_reset':
        members_reset = data.get('members_reset', 0)
        year = data.get('year', '')
        return f"Jährlicher Beitrags-Reset ({year}): {members_reset} Mitglieder zurückgesetzt"

    return '-'


def format_reason_details(operation, data, reason_id=None):
    """Format reason audit log details into human-readable text."""
    if not data:
        return '-'

    name = data.get('name', '')

    # If name not in operation_data, try to look up the reason
    if not name and reason_id:
        reason = BlockReason.query.get(reason_id)
        if reason:
            name = reason.name

    name = name or 'Gelöschter Grund'

    if operation == 'create':
        teamster_usable = data.get('teamster_usable', False)
        usable_text = 'für Mannschaftsführer freigegeben' if teamster_usable else 'nur für Admins'
        return f"Sperrungsgrund erstellt: {name} ({usable_text})"

    elif operation == 'update':
        changes = data.get('changes', {})
        if changes:
            change_texts = []
            for field, vals in changes.items():
                if isinstance(vals, dict) and 'old' in vals and 'new' in vals:
                    if field == 'name':
                        change_texts.append(f"Name: {vals['old']} → {vals['new']}")
                    elif field == 'teamster_usable':
                        old_text = 'Ja' if vals['old'] else 'Nein'
                        new_text = 'Ja' if vals['new'] else 'Nein'
                        change_texts.append(f"Mannschaftsführer: {old_text} → {new_text}")
            if change_texts:
                return f"Sperrungsgrund aktualisiert: {name} - {', '.join(change_texts)}"
        return f"Sperrungsgrund aktualisiert: {name}"

    elif operation == 'delete':
        return f"Sperrungsgrund gelöscht: {name}"

    elif operation == 'deactivate':
        future_blocks_deleted = data.get('future_blocks_deleted', 0)
        if future_blocks_deleted > 0:
            return f"Sperrungsgrund deaktiviert: {name} ({future_blocks_deleted} zukünftige Sperrungen gelöscht)"
        return f"Sperrungsgrund deaktiviert: {name}"

    elif operation == 'reactivate':
        return f"Sperrungsgrund reaktiviert: {name}"

    elif operation == 'permanent_delete':
        blocks_deleted = data.get('blocks_deleted', 0)
        if blocks_deleted > 0:
            return f"Sperrungsgrund endgültig gelöscht: {name} ({blocks_deleted} Sperrungen gelöscht)"
        return f"Sperrungsgrund endgültig gelöscht: {name}"

    return '-'


def format_reservation_details(operation, data, reservation_id):
    """Format reservation audit log details into human-readable text."""
    if not data:
        return f"Buchung {reservation_id}"

    date = data.get('date', '')
    start_time = data.get('start_time', '')
    court_id = data.get('court_id')

    # Format date from ISO to German format
    if date:
        try:
            dt = datetime.fromisoformat(date)
            date = dt.strftime('%d.%m.%Y')
        except (ValueError, TypeError):
            pass

    # Format time
    if start_time:
        try:
            if isinstance(start_time, str) and ':' in start_time:
                start_time = start_time[:5]  # Get HH:MM
        except (ValueError, TypeError):
            pass

    # Get court name (Court model has 'number' attribute, not 'name')
    court_name = f"Platz {court_id}"
    if court_id:
        court = Court.query.get(court_id)
        if court:
            court_name = f"Platz {court.number}"

    # Get member name for booked_for
    booked_for_id = data.get('booked_for_id')
    booked_for_name = ''
    if booked_for_id:
        member = Member.query.get(booked_for_id)
        if member:
            booked_for_name = f" für {member.name}"

    if operation == 'create':
        short_notice = " (kurzfristig)" if data.get('is_short_notice') else ""
        return f"Buchung erstellt: {court_name}, {date} {start_time}{booked_for_name}{short_notice}"

    if operation == 'cancel':
        reason = data.get('reason', '')
        cancelled_by_admin = data.get('cancelled_by_admin', False)
        cancelled_by_block = data.get('cancelled_by_block', False)
        if cancelled_by_block:
            admin_text = " (durch Sperrung)"
        elif cancelled_by_admin:
            admin_text = " (durch Admin)"
        else:
            admin_text = ""
        reason_text = f" - {reason}" if reason else ""
        return f"Buchung storniert: {court_name}, {date} {start_time}{booked_for_name}{admin_text}{reason_text}"

    return f"Buchung {reservation_id}"


@bp.route('/blocks/audit-log', methods=['GET'])
@login_required
@admin_required
def get_audit_log():
    """Get unified audit log combining block, member, reason, and reservation operations (admin only)."""
    try:
        # Get filter parameters
        log_type = request.args.get('type')  # 'block', 'member', 'reason', 'reservation', or None for all
        limit = min(int(request.args.get('limit', 100)), 500)  # Max 500 entries

        logs = []

        # Query BlockAuditLog if not filtered to other types only
        if log_type in (None, 'block'):
            block_logs = BlockAuditLog.query.order_by(BlockAuditLog.timestamp.desc()).limit(limit).all()
            for log in block_logs:
                # Block logs are always admin actions
                performer_role = log.admin.role if log.admin else 'system'
                logs.append({
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.operation,
                    'user': log.admin.name if log.admin else 'System',
                    'details': format_block_details(log.operation, log.operation_data),
                    'type': 'block',
                    'performer_role': performer_role
                })

        # Query MemberAuditLog if not filtered to other types only
        if log_type in (None, 'member'):
            member_logs = MemberAuditLog.query.order_by(MemberAuditLog.timestamp.desc()).limit(limit).all()
            for log in member_logs:
                # Get performer role from operation_data or from the performer
                performer_role = 'system'
                if log.operation_data and 'performer_role' in log.operation_data:
                    performer_role = log.operation_data['performer_role']
                elif log.performed_by:
                    performer_role = log.performed_by.role
                logs.append({
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.operation,
                    'user': log.performed_by.name if log.performed_by else 'System',
                    'details': format_member_details(log.operation, log.operation_data, log.member_id),
                    'type': 'member',
                    'performer_role': performer_role
                })

        # Query ReasonAuditLog if not filtered to other types only
        if log_type in (None, 'reason'):
            reason_logs = ReasonAuditLog.query.order_by(ReasonAuditLog.timestamp.desc()).limit(limit).all()
            for log in reason_logs:
                # Reason logs are always admin actions
                performer_role = log.performed_by.role if log.performed_by else 'system'
                logs.append({
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.operation,
                    'user': log.performed_by.name if log.performed_by else 'System',
                    'details': format_reason_details(log.operation, log.operation_data, log.reason_id),
                    'type': 'reason',
                    'performer_role': performer_role
                })

        # Query ReservationAuditLog if not filtered to other types only
        if log_type in (None, 'reservation'):
            reservation_logs = ReservationAuditLog.query.order_by(ReservationAuditLog.timestamp.desc()).limit(limit).all()
            for log in reservation_logs:
                # Get performer role from operation_data or from the performer
                performer_role = 'member'
                if log.operation_data and 'performer_role' in log.operation_data:
                    performer_role = log.operation_data['performer_role']
                elif log.performed_by:
                    performer_role = log.performed_by.role
                logs.append({
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.operation,
                    'user': log.performed_by.name if log.performed_by else 'System',
                    'details': format_reservation_details(log.operation, log.operation_data, log.reservation_id),
                    'type': 'reservation',
                    'performer_role': performer_role
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
