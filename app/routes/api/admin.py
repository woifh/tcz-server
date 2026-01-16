"""
API Admin Module

Admin routes for member management, blocks, and settings.
Session-only authentication with admin/teamster role requirements.
These endpoints are NOT accessible via JWT/mobile app.
"""

from datetime import datetime
from flask import request, jsonify
from flask_login import current_user

from app import db
from app.models import Member, Block, Court, BlockReason
from app.services.member_service import MemberService
from app.services.block_service import BlockService
from app.services.settings_service import SettingsService
from app.decorators.auth import admin_required, teamster_or_admin_required
from app.constants.messages import ErrorMessages, SuccessMessages
from . import bp


# ----- Member Management Routes (Admin Only) -----

@bp.route('/admin/members/', methods=['GET'])
@admin_required
def list_members():
    """List all active members."""
    members, error = MemberService.get_all_members(include_inactive=False)
    if error:
        return jsonify({'error': error}), 500

    return jsonify({
        'members': [m.to_dict(include_admin_fields=True) for m in members]
    })


@bp.route('/admin/members/', methods=['POST'])
@admin_required
def create_member():
    """Create a new member."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    try:
        member, error = MemberService.create_member(
            firstname=data.get('firstname'),
            lastname=data.get('lastname'),
            email=data.get('email'),
            password=data.get('password'),
            role=data.get('role', 'member'),
            membership_type=data.get('membership_type', 'full'),
            street=data.get('street'),
            city=data.get('city'),
            zip_code=data.get('zip_code'),
            phone=data.get('phone'),
            admin_id=current_user.id,
            notifications_enabled=bool(data.get('notifications_enabled', True)),
            notify_own_bookings=bool(data.get('notify_own_bookings', True)),
            notify_other_bookings=bool(data.get('notify_other_bookings', True)),
            notify_court_blocked=bool(data.get('notify_court_blocked', True)),
            notify_booking_overridden=bool(data.get('notify_booking_overridden', True))
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': SuccessMessages.MEMBER_CREATED,
            'member': member.to_dict(include_admin_fields=True)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/admin/members/<id>', methods=['GET'])
@admin_required
def get_member(id):
    """Get member details."""
    member, error = MemberService.get_member(id)

    if error:
        return jsonify({'error': error}), 404

    return jsonify(member.to_dict(include_admin_fields=True))


@bp.route('/admin/members/<id>', methods=['PUT'])
@admin_required
def update_member(id):
    """Update a member."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    try:
        updates = {}
        allowed_fields = [
            'firstname', 'lastname', 'email', 'password', 'role',
            'membership_type', 'fee_paid', 'street', 'city', 'zip_code', 'phone',
            'notifications_enabled', 'notify_own_bookings', 'notify_other_bookings',
            'notify_court_blocked', 'notify_booking_overridden'
        ]

        for field in allowed_fields:
            if field in data:
                value = data[field]
                if field == 'fee_paid':
                    if isinstance(value, str):
                        updates[field] = value.lower() in ('true', '1', 'yes')
                    else:
                        updates[field] = bool(value)
                elif field.startswith('notif'):
                    updates[field] = bool(value)
                elif field == 'password' and value:
                    updates[field] = value
                elif field != 'password':
                    updates[field] = value

        member, error = MemberService.update_member(
            member_id=id,
            updates=updates,
            admin_id=current_user.id
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': SuccessMessages.MEMBER_UPDATED,
            'member': member.to_dict(include_admin_fields=True)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/admin/members/<id>', methods=['DELETE'])
@admin_required
def delete_member(id):
    """Delete a member."""
    force = request.args.get('force', 'false').lower() == 'true'

    try:
        success, error = MemberService.delete_member(
            member_id=id,
            admin_id=current_user.id,
            force=force
        )

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({'message': SuccessMessages.MEMBER_DELETED})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/admin/members/<id>/deactivate', methods=['POST'])
@admin_required
def deactivate_member(id):
    """Deactivate a member account."""
    try:
        success, error = MemberService.deactivate_member(
            member_id=id,
            admin_id=current_user.id
        )

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({'message': SuccessMessages.MEMBER_DEACTIVATED})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/admin/members/<id>/reactivate', methods=['POST'])
@admin_required
def reactivate_member(id):
    """Reactivate a member account."""
    try:
        success, error = MemberService.reactivate_member(
            member_id=id,
            admin_id=current_user.id
        )

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({'message': SuccessMessages.MEMBER_REACTIVATED})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----- Block Management Routes (Teamster or Admin) -----

@bp.route('/admin/blocks/', methods=['GET'])
@teamster_or_admin_required
def get_blocks():
    """Get blocks with optional filtering."""
    try:
        date_range_start = request.args.get('date_range_start')
        date_range_end = request.args.get('date_range_end')
        court_ids = request.args.getlist('court_ids', type=int)
        reason_ids = request.args.getlist('reason_ids', type=int)

        query = Block.query

        if date_range_start:
            start_date = datetime.strptime(date_range_start, '%Y-%m-%d').date()
            query = query.filter(Block.date >= start_date)

        if date_range_end:
            end_date = datetime.strptime(date_range_end, '%Y-%m-%d').date()
            query = query.filter(Block.date <= end_date)

        if court_ids:
            query = query.filter(Block.court_id.in_(court_ids))

        if reason_ids:
            query = query.filter(Block.reason_id.in_(reason_ids))

        blocks = query.order_by(Block.date.asc(), Block.start_time.asc()).all()

        return jsonify({
            'blocks': [b.to_dict() for b in blocks]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/admin/blocks/', methods=['POST'])
@teamster_or_admin_required
def create_blocks():
    """Create block(s) for one or multiple courts."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    try:
        # Get court_ids
        court_ids = data.get('court_ids', [])
        if isinstance(court_ids, str):
            court_ids = [int(x) for x in court_ids.split(',')]
        elif not court_ids and 'court_id' in data:
            court_ids = [int(data['court_id'])]

        if not court_ids:
            return jsonify({'error': 'court_ids erforderlich'}), 400

        court_ids = [int(x) for x in court_ids]
        date_str = data['date']
        start_time_str = data['start_time']
        end_time_str = data['end_time']
        reason_id = int(data['reason_id'])
        details = data.get('details', '').strip() or None

        # Validate teamsters can only use teamster-usable reasons
        if current_user.is_teamster() and not current_user.is_admin():
            reason = BlockReason.query.get(reason_id)
            if not reason:
                return jsonify({'error': 'Ungültiger Sperrungsgrund'}), 400
            if not reason.teamster_usable:
                return jsonify({'error': 'Sie haben keine Berechtigung, diesen Sperrungsgrund zu verwenden'}), 403

        block_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()

        from app.utils.timezone_utils import get_berlin_date_today
        today = get_berlin_date_today()
        if block_date < today:
            return jsonify({'error': 'Sperrungen können nicht für vergangene Tage erstellt werden'}), 400

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


@bp.route('/admin/blocks/<batch_id>', methods=['GET'])
@teamster_or_admin_required
def get_batch(batch_id):
    """Get all blocks in a batch."""
    try:
        blocks = Block.query.filter_by(batch_id=batch_id).all()

        if not blocks:
            return jsonify({'error': 'Batch nicht gefunden'}), 404

        first_block = blocks[0]
        reason = BlockReason.query.get(first_block.reason_id)

        return jsonify({
            'batch_id': batch_id,
            'date': first_block.date.isoformat(),
            'start_time': first_block.start_time.strftime('%H:%M'),
            'end_time': first_block.end_time.strftime('%H:%M'),
            'reason_id': first_block.reason_id,
            'reason_name': reason.name if reason else 'Unbekannt',
            'details': first_block.details,
            'court_ids': [b.court_id for b in blocks],
            'blocks': [b.to_dict() for b in blocks]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/admin/blocks/<batch_id>', methods=['PUT'])
@teamster_or_admin_required
def update_batch(batch_id):
    """Update all blocks in a batch."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    try:
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        new_end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        new_reason_id = int(data['reason_id'])
        new_details = data.get('details', '').strip() or None

        new_court_ids = data.get('court_ids', [])
        if isinstance(new_court_ids, str):
            new_court_ids = [int(x) for x in new_court_ids.split(',')]
        else:
            new_court_ids = [int(x) for x in new_court_ids]

        from app.utils.timezone_utils import get_berlin_date_today
        today = get_berlin_date_today()
        if new_date < today:
            return jsonify({'error': 'Sperrungen können nicht für vergangene Tage bearbeitet werden'}), 400

        if new_start_time >= new_end_time:
            return jsonify({'error': 'Endzeit muss nach Startzeit liegen'}), 400

        existing_blocks = Block.query.filter_by(batch_id=batch_id).all()
        if not existing_blocks:
            return jsonify({'error': 'Batch nicht gefunden'}), 404

        # Teamsters can only update their own batches
        if current_user.is_teamster() and not current_user.is_admin():
            if not all(block.created_by_id == current_user.id for block in existing_blocks):
                return jsonify({'error': 'Sie können nur Ihre eigenen Sperrungen bearbeiten'}), 403

        existing_court_ids = [block.court_id for block in existing_blocks]
        courts_to_keep = set(existing_court_ids) & set(new_court_ids)
        courts_to_delete = set(existing_court_ids) - set(new_court_ids)
        courts_to_add = set(new_court_ids) - set(existing_court_ids)

        # Delete blocks for removed courts
        for block in existing_blocks:
            if block.court_id in courts_to_delete:
                db.session.delete(block)

        # Update existing blocks (skip individual audit logs)
        for block in existing_blocks:
            if block.court_id in courts_to_keep:
                success, error = BlockService.update_single_instance(
                    block_id=block.id,
                    skip_audit_log=True,
                    date=new_date,
                    start_time=new_start_time,
                    end_time=new_end_time,
                    reason_id=new_reason_id,
                    details=new_details,
                    admin_id=current_user.id
                )
                if error:
                    db.session.rollback()
                    return jsonify({'error': f'Fehler beim Aktualisieren: {error}'}), 400

        # Create new blocks for added courts
        for court_id in courts_to_add:
            new_block = Block(
                court_id=court_id,
                date=new_date,
                start_time=new_start_time,
                end_time=new_end_time,
                reason_id=new_reason_id,
                details=new_details,
                created_by_id=current_user.id,
                batch_id=batch_id
            )
            db.session.add(new_block)
            db.session.flush()
            BlockService.cancel_conflicting_reservations(new_block)

        db.session.commit()

        # Get court numbers and reason name for batch-level audit log
        reason = BlockReason.query.get(new_reason_id)
        reason_name = reason.name if reason else None
        final_court_numbers = sorted([Court.query.get(cid).number for cid in new_court_ids if Court.query.get(cid)])

        # Log batch update once
        BlockService.log_block_operation(
            operation='update',
            block_data={
                'batch_id': batch_id,
                'date': new_date.isoformat(),
                'start_time': new_start_time.strftime('%H:%M'),
                'end_time': new_end_time.strftime('%H:%M'),
                'court_numbers': final_court_numbers,
                'reason_name': reason_name,
                'details': new_details
            },
            admin_id=current_user.id
        )

        total_blocks = len(courts_to_keep) + len(courts_to_add)
        return jsonify({'message': f'{total_blocks} Sperrungen erfolgreich aktualisiert'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/admin/blocks/<batch_id>', methods=['DELETE'])
@teamster_or_admin_required
def delete_batch(batch_id):
    """Delete all blocks in a batch."""
    try:
        blocks = Block.query.filter_by(batch_id=batch_id).all()

        if not blocks:
            return jsonify({'error': 'Batch nicht gefunden'}), 404

        # Teamsters can only delete their own batches
        if current_user.is_teamster() and not current_user.is_admin():
            if not all(block.created_by_id == current_user.id for block in blocks):
                return jsonify({'error': 'Sie können nur Ihre eigenen Sperrungen löschen'}), 403

        success, error = BlockService.delete_batch(batch_id, current_user.id)

        if success:
            return jsonify({'message': 'Batch erfolgreich gelöscht'})
        return jsonify({'error': error}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----- Settings Routes (Admin Only) -----

@bp.route('/admin/settings/payment-deadline', methods=['GET'])
@admin_required
def get_payment_deadline():
    """Get current payment deadline settings."""
    deadline = SettingsService.get_payment_deadline()
    days_until = SettingsService.days_until_deadline()
    unpaid_count = SettingsService.get_unpaid_member_count()

    return jsonify({
        'deadline': deadline.isoformat() if deadline else None,
        'days_until': days_until,
        'unpaid_count': unpaid_count,
        'is_past': SettingsService.is_past_payment_deadline()
    })


@bp.route('/admin/settings/payment-deadline', methods=['POST'])
@admin_required
def set_payment_deadline():
    """Set payment deadline."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    deadline_str = data.get('deadline')

    if not deadline_str:
        success, error = SettingsService.clear_payment_deadline(current_user.id)
        if success:
            return jsonify({'message': SuccessMessages.PAYMENT_DEADLINE_CLEARED})
        return jsonify({'error': error}), 400

    try:
        deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': ErrorMessages.PAYMENT_DEADLINE_INVALID_DATE}), 400

    success, error = SettingsService.set_payment_deadline(deadline_date, current_user.id)

    if success:
        return jsonify({
            'message': SuccessMessages.PAYMENT_DEADLINE_SET,
            'deadline': deadline_date.isoformat()
        })
    return jsonify({'error': error}), 400


@bp.route('/admin/settings/payment-deadline', methods=['DELETE'])
@admin_required
def clear_payment_deadline():
    """Clear payment deadline."""
    success, error = SettingsService.clear_payment_deadline(current_user.id)

    if success:
        return jsonify({'message': SuccessMessages.PAYMENT_DEADLINE_CLEARED})
    return jsonify({'error': error}), 400


# ----- Block Reasons Routes -----

@bp.route('/admin/block-reasons', methods=['GET'])
@teamster_or_admin_required
def list_block_reasons():
    """List block reasons based on user role."""
    from app.services.block_reason_service import BlockReasonService

    try:
        if current_user.is_admin():
            # Admins see all reasons including inactive
            reasons = BlockReasonService.get_all_block_reasons(include_inactive=True)
        else:
            reasons = BlockReasonService.get_reasons_for_user(current_user)

        reasons_data = [{
            'id': r.id,
            'name': r.name,
            'is_active': r.is_active,
            'teamster_usable': r.teamster_usable,
            'usage_count': BlockReasonService.get_reason_usage_count(r.id),
            'created_by': r.created_by.name,
            'created_at': r.created_at.isoformat()
        } for r in reasons]

        return jsonify({'reasons': reasons_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/admin/block-reasons', methods=['POST'])
@admin_required
def create_block_reason():
    """Create block reason (admin only)."""
    from app.services.block_reason_service import BlockReasonService

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    name = data.get('name', '').strip()
    teamster_usable = data.get('teamster_usable', False)

    if isinstance(teamster_usable, str):
        teamster_usable = teamster_usable.lower() in ('true', '1', 'yes')

    if not name:
        return jsonify({'error': 'Name ist erforderlich'}), 400

    existing = BlockReason.query.filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Ein Grund mit diesem Namen existiert bereits'}), 400

    reason, error = BlockReasonService.create_block_reason(
        name=name,
        admin_id=current_user.id,
        teamster_usable=teamster_usable
    )

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': 'Sperrungsgrund erfolgreich erstellt',
        'reason': {
            'id': reason.id,
            'name': reason.name,
            'is_active': reason.is_active,
            'teamster_usable': reason.teamster_usable
        }
    }), 201


@bp.route('/admin/block-reasons/<int:reason_id>', methods=['PUT'])
@admin_required
def update_block_reason(reason_id):
    """Update block reason (admin only)."""
    from app.services.block_reason_service import BlockReasonService

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    name = data.get('name', '').strip() if data.get('name') else None
    teamster_usable = data.get('teamster_usable')

    if teamster_usable is not None and isinstance(teamster_usable, str):
        teamster_usable = teamster_usable.lower() in ('true', '1', 'yes')

    if name is not None and not name:
        return jsonify({'error': 'Name ist erforderlich'}), 400

    success, error = BlockReasonService.update_block_reason(
        reason_id=reason_id,
        name=name,
        teamster_usable=teamster_usable,
        admin_id=current_user.id
    )

    if error:
        return jsonify({'error': error}), 400

    return jsonify({'message': 'Sperrungsgrund erfolgreich aktualisiert'})


@bp.route('/admin/block-reasons/<int:reason_id>', methods=['DELETE'])
@admin_required
def delete_block_reason(reason_id):
    """Delete block reason (admin only)."""
    from app.services.block_reason_service import BlockReasonService

    success, error_or_message = BlockReasonService.delete_block_reason(reason_id, current_user.id)

    if not success:
        return jsonify({'error': error_or_message}), 400

    if error_or_message:
        return jsonify({'message': error_or_message, 'deactivated': True})

    return jsonify({'message': 'Sperrungsgrund erfolgreich gelöscht'})


@bp.route('/admin/block-reasons/<int:reason_id>/reactivate', methods=['POST'])
@admin_required
def reactivate_block_reason(reason_id):
    """Reactivate an inactive block reason (admin only)."""
    from app.services.block_reason_service import BlockReasonService
    from app.models import BlockReason

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
    })


@bp.route('/admin/block-reasons/<int:reason_id>/permanent', methods=['DELETE'])
@admin_required
def permanently_delete_block_reason(reason_id):
    """Permanently delete a block reason (admin only)."""
    from app.services.block_reason_service import BlockReasonService
    from app.models import BlockReason

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
    })


# ----- Conflict Preview Route -----

@bp.route('/admin/blocks/conflict-preview', methods=['POST'])
@teamster_or_admin_required
def get_conflict_preview():
    """Preview conflicts before creating/updating blocks."""
    from app.models import Reservation

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    court_ids = data.get('court_ids', [])
    date_str = data.get('date')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    if not all([court_ids, date_str, start_time_str, end_time_str]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        from datetime import datetime
        block_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400

    conflicts = []
    for court_id in court_ids:
        conflicting_reservations = Reservation.query.filter(
            Reservation.court_id == court_id,
            Reservation.date == block_date,
            Reservation.status == 'active',
            Reservation.start_time >= start_time,
            Reservation.start_time < end_time
        ).all()

        for res in conflicting_reservations:
            conflicts.append({
                'id': res.id,
                'court_number': res.court.number if res.court else court_id,
                'date': res.date.isoformat(),
                'start_time': res.start_time.strftime('%H:%M'),
                'end_time': res.end_time.strftime('%H:%M'),
                'booked_for': res.booked_for.name if res.booked_for else 'Unknown',
                'booked_by': res.booked_by.name if res.booked_by else 'Unknown'
            })

    return jsonify({
        'conflicts': conflicts,
        'conflict_count': len(conflicts)
    })


# ----- Audit Log & Changelog Routes -----

@bp.route('/admin/blocks/audit-log', methods=['GET'])
@admin_required
def get_audit_log():
    """Get unified audit log."""
    from app.models import BlockAuditLog, MemberAuditLog, ReasonAuditLog, ReservationAuditLog, Court
    from app.routes.admin.audit import format_block_details, format_member_details, format_reason_details, format_reservation_details

    log_type = request.args.get('type')
    limit = min(int(request.args.get('limit', 100)), 500)

    logs = []

    if log_type in (None, 'block'):
        block_logs = BlockAuditLog.query.order_by(BlockAuditLog.timestamp.desc()).limit(limit).all()
        for log in block_logs:
            performer_role = log.admin.role if log.admin else 'system'
            logs.append({
                'timestamp': log.timestamp.isoformat(),
                'action': log.operation,
                'user': log.admin.name if log.admin else 'System',
                'details': format_block_details(log.operation, log.operation_data),
                'type': 'block',
                'performer_role': performer_role
            })

    if log_type in (None, 'member'):
        member_logs = MemberAuditLog.query.order_by(MemberAuditLog.timestamp.desc()).limit(limit).all()
        for log in member_logs:
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

    if log_type in (None, 'reason'):
        reason_logs = ReasonAuditLog.query.order_by(ReasonAuditLog.timestamp.desc()).limit(limit).all()
        for log in reason_logs:
            performer_role = log.performed_by.role if log.performed_by else 'system'
            logs.append({
                'timestamp': log.timestamp.isoformat(),
                'action': log.operation,
                'user': log.performed_by.name if log.performed_by else 'System',
                'details': format_reason_details(log.operation, log.operation_data, log.reason_id),
                'type': 'reason',
                'performer_role': performer_role
            })

    if log_type in (None, 'reservation'):
        reservation_logs = ReservationAuditLog.query.order_by(ReservationAuditLog.timestamp.desc()).limit(limit).all()
        for log in reservation_logs:
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

    # Sort by timestamp descending
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    logs = logs[:limit]

    return jsonify({'success': True, 'logs': logs})


@bp.route('/admin/changelog', methods=['GET'])
@admin_required
def get_changelog():
    """Get changelog entries."""
    from app.services.changelog_service import ChangelogService

    entries, error = ChangelogService.get_changelog_as_dict()

    if error:
        return jsonify({'success': False, 'error': error}), 500

    return jsonify({'success': True, 'entries': entries})
