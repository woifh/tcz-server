"""
Admin Audit Module

Contains audit log formatting helpers used by API routes.
The actual route handler is in app/routes/api/admin.py.
"""

from datetime import datetime

from app.models import Member, BlockReason, Court


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
                if field == 'password' and vals == 'changed':
                    change_texts.append("Passwort geändert")
                elif isinstance(vals, dict) and 'old' in vals and 'new' in vals:
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

    elif operation == 'payment_confirmation' or operation == 'payment_confirmation_request':
        member_name = data.get('member_name', name)
        return f"Zahlungsbestätigung angefordert: {member_name}"

    elif operation == 'payment_confirmation_reject':
        member_name = data.get('member_name', name)
        return f"Zahlungsbestätigung abgelehnt: {member_name}"

    elif operation == 'email_verification_sent':
        member_name = data.get('member_name', name)
        email = data.get('email', '')
        triggered_by = data.get('triggered_by', '')
        trigger_map = {
            'member_creation': 'Mitglied erstellt',
            'resend': 'Erneut gesendet',
            'admin_triggered': 'Durch Admin',
            'email_change': 'E-Mail geändert'
        }
        trigger_text = trigger_map.get(triggered_by, triggered_by)
        result = f"E-Mail-Bestätigung gesendet an: {member_name}"
        if email:
            result += f" ({email})"
        if trigger_text:
            result += f" - {trigger_text}"
        return result

    elif operation == 'email_verified':
        member_name = data.get('member_name', name)
        email = data.get('email', '')
        result = f"E-Mail bestätigt: {member_name}"
        if email:
            result += f" ({email})"
        return result

    elif operation == 'email_verification_reset':
        member_name = data.get('member_name', name)
        email = data.get('email', '')
        reason = data.get('reason', '')
        reason_map = {'email_changed': 'E-Mail-Adresse geändert'}
        reason_text = reason_map.get(reason, reason)
        result = f"E-Mail-Bestätigung zurückgesetzt: {member_name}"
        if email:
            result += f" ({email})"
        if reason_text:
            result += f" - {reason_text}"
        return result

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
