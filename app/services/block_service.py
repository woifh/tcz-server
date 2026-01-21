"""Block service for court blocking."""
from datetime import date, datetime, time
from sqlalchemy.orm import joinedload
from app import db
from app.models import Block, Reservation, BlockReason, BlockAuditLog
from app.services.email_service import EmailService
from app.constants.messages import ErrorMessages
from app.utils.serializers import serialize_for_json
import logging
import uuid

logger = logging.getLogger(__name__)


# Suspension fate constants
FATE_RESTORE = 'restore'
FATE_CANCEL = 'cancel'
FATE_TRANSFER = 'transfer'


class BlockService:
    """Service for managing court blocks."""
    
    @staticmethod
    def _serialize_for_json(value):
        """Convert date/time objects (including nested structures) to JSON-safe strings."""
        return serialize_for_json(value)

    @staticmethod
    def get_blocks_by_date(date):
        """
        Get all blocks for a specific date with eager loading of related objects.

        Args:
            date: Date to query

        Returns:
            list: List of Block objects with reason_obj and court preloaded
        """
        return Block.query.options(
            joinedload(Block.reason_obj),
            joinedload(Block.court)
        ).filter_by(date=date).order_by(Block.start_time).all()
    
    @staticmethod
    def cancel_conflicting_reservations(block):
        """
        Cancel all reservations that conflict with a block.
        
        Args:
            block: Block object
            
        Returns:
            list: List of cancelled Reservation objects
        """
        # Find all active reservations that overlap with the block
        conflicting_reservations = Reservation.query.filter(
            Reservation.court_id == block.court_id,
            Reservation.date == block.date,
            Reservation.status == 'active',
            Reservation.start_time >= block.start_time,
            Reservation.start_time < block.end_time
        ).all()
        
        # Get reason name from BlockReason relationship
        reason_name = block.reason_obj.name if block.reason_obj else 'Unknown'
        
        # German reason text mapping
        reason_map = {
            'Weather': 'Regen',
            'Maintenance': 'Wartung',
            'Tournament': 'Turnier',
            'Championship': 'Meisterschaft',
            'Tennis Course': 'Tenniskurs'
        }
        
        reason_text = reason_map.get(reason_name, reason_name)
        
        # Include details if provided
        if block.details:
            cancellation_reason = f"Platzsperre wegen {reason_text} - {block.details}"
        else:
            cancellation_reason = f"Platzsperre wegen {reason_text}"
        
        # Cancel each reservation and send notifications
        for reservation in conflicting_reservations:
            reservation.status = 'cancelled'
            reservation.reason = cancellation_reason

            # Log to ReservationAuditLog
            from app.services.reservation import ReservationService
            ReservationService.log_reservation_operation(
                operation='cancel',
                reservation_id=reservation.id,
                operation_data={
                    'court_id': reservation.court_id,
                    'date': str(reservation.date),
                    'start_time': str(reservation.start_time),
                    'reason': cancellation_reason,
                    'booked_for_id': reservation.booked_for_id,
                    'cancelled_by_admin': True,
                    'cancelled_by_block': True,
                    'block_id': block.id
                },
                performed_by_id=block.created_by_id
            )

            # Send email notifications with block reason
            try:
                EmailService.send_booking_cancelled(reservation, cancellation_reason)
            except Exception as e:
                logger.error(f"Failed to send cancellation email for reservation {reservation.id}: {str(e)}")

            # Send push notifications
            try:
                from app.services.push_notification_service import PushNotificationService
                PushNotificationService.send_booking_cancelled_push(reservation, cancellation_reason)
            except Exception as e:
                logger.error(f"Failed to send cancellation push for reservation {reservation.id}: {str(e)}")

        return conflicting_reservations

    @staticmethod
    def suspend_conflicting_reservations(block):
        """
        Suspend (not cancel) reservations that conflict with a temporary block.
        Suspended reservations can be restored when the block is removed.

        Args:
            block: Block object with a temporary reason

        Returns:
            list: List of suspended Reservation objects
        """
        # Find all active reservations that overlap with the block
        conflicting_reservations = Reservation.query.filter(
            Reservation.court_id == block.court_id,
            Reservation.date == block.date,
            Reservation.status == 'active',
            Reservation.start_time >= block.start_time,
            Reservation.start_time < block.end_time
        ).all()

        # Get reason name from BlockReason relationship
        reason_name = block.reason_obj.name if block.reason_obj else 'Unknown'

        # Include details if provided
        if block.details:
            suspension_reason = f"Vorübergehend gesperrt wegen {reason_name} - {block.details}"
        else:
            suspension_reason = f"Vorübergehend gesperrt wegen {reason_name}"

        # Suspend each reservation and send notifications
        for reservation in conflicting_reservations:
            reservation.status = 'suspended'
            reservation.reason = suspension_reason
            reservation.suspended_by_block_id = block.id

            # Log to ReservationAuditLog
            from app.services.reservation import ReservationService
            ReservationService.log_reservation_operation(
                operation='suspend',
                reservation_id=reservation.id,
                operation_data={
                    'court_id': reservation.court_id,
                    'date': str(reservation.date),
                    'start_time': str(reservation.start_time),
                    'reason': suspension_reason,
                    'booked_for_id': reservation.booked_for_id,
                    'suspended_by_block': True,
                    'block_id': block.id
                },
                performed_by_id=block.created_by_id
            )

            # Send email notification for suspension
            try:
                EmailService.send_booking_suspended(reservation, suspension_reason)
            except Exception as e:
                logger.error(f"Failed to send suspension email for reservation {reservation.id}: {str(e)}")

            # Send push notification for suspension
            try:
                from app.services.push_notification_service import PushNotificationService
                PushNotificationService.send_booking_suspended_push(reservation, suspension_reason)
            except Exception as e:
                logger.error(f"Failed to send suspension push for reservation {reservation.id}: {str(e)}")

        return conflicting_reservations

    @staticmethod
    def _determine_suspension_fate(reservation, block_being_removed):
        """
        Determine what happens to a suspended reservation when a block is removed.

        Args:
            reservation: The suspended Reservation object
            block_being_removed: The Block being deleted or modified

        Returns:
            tuple: (fate, context) where fate is FATE_RESTORE/FATE_CANCEL/FATE_TRANSFER
                   and context is None, reason string, or new block_id respectively
        """
        # Check if any OTHER blocks still cover this slot
        overlapping = Block.query.filter(
            Block.id != block_being_removed.id,
            Block.court_id == reservation.court_id,
            Block.date == reservation.date,
            Block.start_time <= reservation.start_time,
            Block.end_time > reservation.start_time
        ).all()

        if not overlapping:
            return (FATE_RESTORE, None)

        # Check for permanent blocks among overlapping
        permanent = next((b for b in overlapping if not b.is_temporary_block), None)
        if permanent:
            return (FATE_CANCEL, "Storniert wegen permanenter Platzsperre")

        # Transfer to another temporary block
        return (FATE_TRANSFER, overlapping[0].id)

    @staticmethod
    def _restore_reservation(reservation, block, admin_id):
        """Restore a suspended reservation to active status."""
        reservation.status = 'active'
        reservation.reason = None
        reservation.suspended_by_block_id = None

        from app.services.reservation import ReservationService
        ReservationService.log_reservation_operation(
            operation='restore',
            reservation_id=reservation.id,
            operation_data={
                'court_id': reservation.court_id,
                'date': str(reservation.date),
                'start_time': str(reservation.start_time),
                'booked_for_id': reservation.booked_for_id,
                'restored_after_block_removal': True,
                'block_id': block.id
            },
            performed_by_id=admin_id
        )

        try:
            EmailService.send_booking_restored(reservation)
        except Exception as e:
            logger.error(f"Failed to send restoration email for reservation {reservation.id}: {str(e)}")

        # Send push notification for restoration
        try:
            from app.services.push_notification_service import PushNotificationService
            PushNotificationService.send_booking_restored_push(reservation)
        except Exception as e:
            logger.error(f"Failed to send restoration push for reservation {reservation.id}: {str(e)}")

    @staticmethod
    def _cancel_suspended_reservation(reservation, reason, admin_id):
        """Cancel a suspended reservation (e.g., when a permanent block now covers it)."""
        reservation.status = 'cancelled'
        reservation.reason = reason
        reservation.suspended_by_block_id = None

        from app.services.reservation import ReservationService
        ReservationService.log_reservation_operation(
            operation='cancel',
            reservation_id=reservation.id,
            operation_data={
                'court_id': reservation.court_id,
                'date': str(reservation.date),
                'start_time': str(reservation.start_time),
                'reason': reason,
                'booked_for_id': reservation.booked_for_id,
                'cancelled_by_admin': True,
                'cancelled_by_block': True
            },
            performed_by_id=admin_id
        )

        try:
            EmailService.send_booking_cancelled(reservation, reason)
        except Exception as e:
            logger.error(f"Failed to send cancellation email for reservation {reservation.id}: {str(e)}")

        # Send push notification for cancellation
        try:
            from app.services.push_notification_service import PushNotificationService
            PushNotificationService.send_booking_cancelled_push(reservation, reason)
        except Exception as e:
            logger.error(f"Failed to send cancellation push for reservation {reservation.id}: {str(e)}")

    @staticmethod
    def _is_still_covered_by_block(reservation, block):
        """Check if a reservation is still covered by the given block."""
        return (
            reservation.court_id == block.court_id and
            reservation.date == block.date and
            reservation.start_time >= block.start_time and
            reservation.start_time < block.end_time
        )

    @staticmethod
    def handle_suspended_reservations(block, admin_id, check_still_covered=False):
        """
        Handle suspended reservations when a block is deleted or updated.

        For each suspended reservation:
        - If check_still_covered=True and still covered by block: skip
        - Otherwise determine fate: restore, cancel, or transfer to another block

        Args:
            block: Block object being removed or updated
            admin_id: ID of admin performing the operation
            check_still_covered: If True, skip reservations still covered by the block (for updates)

        Returns:
            list: List of restored Reservation objects
        """
        suspended = Reservation.query.filter(
            Reservation.suspended_by_block_id == block.id,
            Reservation.status == 'suspended'
        ).all()

        restored = []

        for reservation in suspended:
            # For updates: skip if still covered by the updated block
            if check_still_covered and BlockService._is_still_covered_by_block(reservation, block):
                continue

            fate, context = BlockService._determine_suspension_fate(reservation, block)

            if fate == FATE_RESTORE:
                BlockService._restore_reservation(reservation, block, admin_id)
                restored.append(reservation)
            elif fate == FATE_CANCEL:
                BlockService._cancel_suspended_reservation(reservation, context, admin_id)
            elif fate == FATE_TRANSFER:
                reservation.suspended_by_block_id = context

        return restored

    @staticmethod
    def update_single_instance(block_id, skip_audit_log=False, **updates):
        """
        Update a single block instance.

        Args:
            block_id: ID of the Block to update
            skip_audit_log: If True, skip audit logging (for batch operations that log separately)
            **updates: Dictionary of fields to update

        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            # Get the block
            block = Block.query.get(block_id)
            if not block:
                return False, "Block not found"

            # Store old temporary status BEFORE update to handle reason transitions
            old_is_temporary = block.is_temporary_block

            # Store old values to detect changes that affect coverage
            old_date = block.date
            old_start_time = block.start_time
            old_end_time = block.end_time
            old_court_id = block.court_id

            # Update the block
            for field, value in updates.items():
                if hasattr(block, field):
                    setattr(block, field, value)

            # Check NEW temporary status AFTER update (reason may have changed)
            new_is_temporary = block.is_temporary_block

            # Check if coverage changed (date, time, or court)
            coverage_changed = (
                ('date' in updates and updates['date'] != old_date) or
                ('start_time' in updates and updates['start_time'] != old_start_time) or
                ('end_time' in updates and updates['end_time'] != old_end_time) or
                ('court_id' in updates and updates['court_id'] != old_court_id)
            )

            # Check if reason changed
            reason_changed = 'reason_id' in updates

            # Handle reservation conflicts based on old/new temporary status
            admin_id = updates.get('admin_id', block.created_by_id)

            if coverage_changed or reason_changed:
                # If old block was temporary, restore suspended reservations that are no longer covered
                if old_is_temporary and coverage_changed:
                    BlockService.handle_suspended_reservations(block, admin_id, check_still_covered=True)

                # Handle new conflicts based on NEW temporary status
                if new_is_temporary:
                    BlockService.suspend_conflicting_reservations(block)
                else:
                    BlockService.cancel_conflicting_reservations(block)

            db.session.commit()

            # Log the operation (unless skipped for batch operations)
            if not skip_audit_log:
                court_number = block.court.number if block.court else None
                reason_name = block.reason_obj.name if block.reason_obj else None

                BlockService.log_block_operation(
                    operation='update',
                    block_data={
                        'block_id': block_id,
                        'date': block.date.isoformat() if block.date else None,
                        'start_time': block.start_time.strftime('%H:%M') if block.start_time else None,
                        'end_time': block.end_time.strftime('%H:%M') if block.end_time else None,
                        'court_numbers': [court_number] if court_number else [],
                        'reason_name': reason_name,
                        'details': block.details
                    },
                    admin_id=updates.get('admin_id', block.created_by_id)
                )

            logger.info(f"Updated single block instance {block_id}")
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update single block instance {block_id}: {str(e)}")
            return False, f"Fehler beim Aktualisieren der Blockinstanz: {str(e)}"
    @staticmethod
    def create_multi_court_blocks(court_ids, date, start_time, end_time, reason_id, details, admin_id):
        """
        Create blocks for multiple courts simultaneously.
        
        Args:
            court_ids: List of court IDs to block
            date: Date to block
            start_time: Start time of blocks
            end_time: End time of blocks
            reason_id: ID of the BlockReason
            details: Optional additional reason detail
            admin_id: ID of administrator creating the blocks
            
        Returns:
            tuple: (List of Block objects or None, error message or None)
        """
        try:
            if not court_ids:
                return None, ErrorMessages.BLOCK_NO_COURTS_SPECIFIED
            
            # Generate a unique batch ID for ALL blocks (single or multi-court)
            batch_id = str(uuid.uuid4())
            
            blocks = []
            
            # Create blocks for all specified courts
            for court_id in court_ids:
                block = Block(
                    court_id=court_id,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    reason_id=reason_id,
                    details=details,
                    created_by_id=admin_id,
                    batch_id=batch_id
                )
                
                db.session.add(block)
                blocks.append(block)
            
            # Flush to get block IDs and load reason relationships
            db.session.flush()

            # Get reason for audit log (use first block's property for is_temporary check)
            reason = BlockReason.query.get(reason_id)

            # Handle conflicting reservations based on block type
            all_affected_reservations = []
            for block in blocks:
                if block.is_temporary_block:
                    affected = BlockService.suspend_conflicting_reservations(block)
                else:
                    affected = BlockService.cancel_conflicting_reservations(block)
                all_affected_reservations.extend(affected)

            is_temporary = blocks[0].is_temporary_block if blocks else False

            db.session.commit()

            # Get reason name for audit log
            reason_name = reason.name if reason else None

            # Get court numbers for audit log
            from app.models import Court
            courts = Court.query.filter(Court.id.in_(court_ids)).all()
            court_numbers = sorted([c.number for c in courts])

            # Log the operation
            reservation_action = 'suspended' if is_temporary else 'cancelled'
            BlockService.log_block_operation(
                operation='create',
                block_data={
                    'court_ids': court_ids,
                    'court_numbers': court_numbers,
                    'date': date.isoformat(),
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'reason_id': reason_id,
                    'reason_name': reason_name,
                    'is_temporary': is_temporary,
                    'details': details,
                    'blocks_created': len(blocks),
                    f'reservations_{reservation_action}': len(all_affected_reservations)
                },
                admin_id=admin_id
            )

            logger.info(f"Multi-court blocks created: {len(blocks)} blocks for {len(court_ids)} courts, "
                       f"{reservation_action} {len(all_affected_reservations)} reservations")
            
            return blocks, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create multi-court blocks: {str(e)}")
            return None, f"Fehler beim Erstellen der Mehrplatz-Sperren: {str(e)}"
    
    @staticmethod
    def delete_batch(batch_id, admin_id):
        """
        Delete all blocks in a batch.
        
        Args:
            batch_id: The batch_id of blocks to delete
            admin_id: ID of administrator performing the deletion
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            if not batch_id:
                return False, "Batch ID is required"
            
            # Get all blocks with this batch_id
            blocks_to_delete = Block.query.filter_by(batch_id=batch_id).all()

            if not blocks_to_delete:
                return False, "No blocks found with this batch ID"

            # Capture details before deletion for audit log
            first_block = blocks_to_delete[0]
            court_numbers = sorted([block.court.number for block in blocks_to_delete])
            block_date = first_block.date.isoformat() if first_block.date else None
            start_time = first_block.start_time.strftime('%H:%M') if first_block.start_time else None
            end_time = first_block.end_time.strftime('%H:%M') if first_block.end_time else None
            reason_name = first_block.reason_obj.name if first_block.reason_obj else None
            is_temporary = first_block.is_temporary_block
            details = first_block.details

            # If temporary block, restore suspended reservations before deleting
            all_restored = []
            if is_temporary:
                for block in blocks_to_delete:
                    restored = BlockService.handle_suspended_reservations(block, admin_id)
                    all_restored.extend(restored)

            # Delete all blocks in the batch
            for block in blocks_to_delete:
                db.session.delete(block)

            db.session.commit()

            # Log the operation with full details
            log_data = {
                'batch_id': batch_id,
                'date': block_date,
                'start_time': start_time,
                'end_time': end_time,
                'court_numbers': court_numbers,
                'reason_name': reason_name,
                'is_temporary': is_temporary,
                'details': details
            }
            if is_temporary and all_restored:
                log_data['reservations_restored'] = len(all_restored)

            BlockService.log_block_operation(
                operation='delete',
                block_data=log_data,
                admin_id=admin_id
            )

            logger.info(f"Batch deleted: {batch_id}, {len(blocks_to_delete)} blocks by admin {admin_id}"
                       + (f", restored {len(all_restored)} reservations" if all_restored else ""))
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete batch {batch_id}: {str(e)}")
            return False, f"Fehler beim Löschen der Batch-Sperrung: {str(e)}"
    
    @staticmethod
    def filter_blocks(date_range=None, court_ids=None, reason_ids=None, block_types=None):
        """
        Filter blocks based on multiple criteria.
        
        Args:
            date_range: Tuple of (start_date, end_date) or None
            court_ids: List of court IDs or None
            reason_ids: List of reason IDs or None
            block_types: List of block types (deprecated, ignored) or None

        Returns:
            list: List of Block objects matching the criteria
        """
        query = Block.query

        # Filter by date range
        if date_range:
            start_date, end_date = date_range
            query = query.filter(Block.date >= start_date, Block.date <= end_date)

        # Filter by courts
        if court_ids:
            query = query.filter(Block.court_id.in_(court_ids))

        # Filter by reasons
        if reason_ids:
            query = query.filter(Block.reason_id.in_(reason_ids))

        # Note: block_types parameter is deprecated and ignored

        return query.order_by(Block.date, Block.start_time).all()
    
    @staticmethod
    def get_conflict_preview(court_ids, date, start_time, end_time):
        """
        Preview reservations that would be affected by creating blocks.
        
        Args:
            court_ids: List of court IDs
            date: Date for the blocks
            start_time: Start time of blocks
            end_time: End time of blocks
            
        Returns:
            list: List of Reservation objects that would be cancelled
        """
        if not court_ids:
            return []
        
        # Find all active reservations that would overlap with the proposed blocks
        conflicting_reservations = Reservation.query.filter(
            Reservation.court_id.in_(court_ids),
            Reservation.date == date,
            Reservation.status == 'active',
            Reservation.start_time >= start_time,
            Reservation.start_time < end_time
        ).all()
        
        return conflicting_reservations
    
    @staticmethod
    def log_block_operation(operation, block_data, admin_id):
        """
        Log a block operation for audit purposes.

        Args:
            operation: Type of operation ('create', 'update', 'delete')
            block_data: Dictionary containing operation details
            admin_id: ID of administrator/teamster performing the operation
        """
        from app.models import BlockAuditLog, Member

        try:
            # Ensure admin_id is not None
            if admin_id is None:
                logger.warning("admin_id is None for block operation logging, skipping audit log")
                return

            # Get user to include role information
            admin_user = Member.query.get(admin_id)

            # Add role to operation data for audit trail
            if block_data is None:
                block_data = {}
            if admin_user:
                block_data['admin_role'] = admin_user.role

            safe_operation_data = BlockService._serialize_for_json(block_data) if block_data else None

            audit_log = BlockAuditLog(
                operation=operation,
                block_id=block_data.get('block_id') if block_data else None,
                operation_data=safe_operation_data,
                admin_id=admin_id
            )

            db.session.add(audit_log)
            db.session.commit()

            logger.info(f"Block operation logged: {operation} by {admin_user.role if admin_user else 'unknown'} {admin_id}")

        except Exception as e:
            logger.error(f"Failed to log block operation: {str(e)}")
            # Don't fail the main operation if logging fails
    
    @staticmethod
    def get_audit_log(filters=None):
        """
        Get audit log entries with optional filtering.
        
        Args:
            filters: Dictionary with optional filters (admin_id, operation, date_range)
            
        Returns:
            list: List of BlockAuditLog objects
        """
        from app.models import BlockAuditLog
        
        query = BlockAuditLog.query
        
        if filters:
            # Filter by admin
            if 'admin_id' in filters:
                query = query.filter(BlockAuditLog.admin_id == filters['admin_id'])
            
            # Filter by operation type
            if 'operation' in filters:
                query = query.filter(BlockAuditLog.operation == filters['operation'])
            
            # Filter by date range
            if 'date_range' in filters:
                start_date, end_date = filters['date_range']
                query = query.filter(
                    BlockAuditLog.timestamp >= start_date,
                    BlockAuditLog.timestamp <= end_date
                )
        
        return query.order_by(BlockAuditLog.timestamp.desc()).all()
