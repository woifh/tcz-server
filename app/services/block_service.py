"""Block service for court blocking."""
from datetime import date, datetime, time
from app import db
from app.models import Block, Reservation, BlockReason, BlockAuditLog
from app.services.email_service import EmailService
from app.constants.messages import ErrorMessages
import logging
import uuid

logger = logging.getLogger(__name__)


class BlockService:
    """Service for managing court blocks."""
    
    @staticmethod
    def _serialize_for_json(value):
        """Convert date/time objects (including nested structures) to JSON-safe strings."""
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, dict):
            return {k: BlockService._serialize_for_json(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [BlockService._serialize_for_json(v) for v in value]
        return value
    
    @staticmethod
    def create_block(court_id, date, start_time, end_time, reason_id, details, admin_id):
        """
        Create a court block and cancel conflicting reservations.
        
        Args:
            court_id: ID of the court to block
            date: Date to block
            start_time: Start time of block
            end_time: End time of block
            reason_id: ID of the BlockReason
            details: Optional additional reason detail
            admin_id: ID of administrator creating the block
            
        Returns:
            tuple: (Block object or None, error message or None)
        """
        # Generate a unique batch ID for this block
        batch_id = str(uuid.uuid4())
        
        # Create the block
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
        
        try:
            db.session.add(block)
            db.session.flush()  # Flush to get block ID but don't commit yet
            
            # Cancel conflicting reservations
            cancelled_reservations = BlockService.cancel_conflicting_reservations(block)
            
            # Commit everything together
            db.session.commit()
            
            # Log the operation
            BlockService.log_block_operation(
                operation='create',
                block_data={
                    'block_id': block.id,
                    'court_id': court_id,
                    'date': date.isoformat(),
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'reason_id': reason_id,
                    'details': details,
                    'cancelled_reservations': len(cancelled_reservations)
                },
                admin_id=admin_id
            )
            
            logger.info(f"Block created: Court {court_id}, Date {date}, "
                       f"Cancelled {len(cancelled_reservations)} reservations")
            
            return block, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create block: {str(e)}")
            return None, f"Fehler beim Erstellen der Sperre: {str(e)}"
    
    @staticmethod
    def get_blocks_by_date(date):
        """
        Get all blocks for a specific date.
        
        Args:
            date: Date to query
            
        Returns:
            list: List of Block objects
        """
        return Block.query.filter_by(date=date).order_by(Block.start_time).all()
    
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
            
            # Send email notifications with block reason
            try:
                EmailService.send_booking_cancelled(reservation, cancellation_reason)
            except Exception as e:
                logger.error(f"Failed to send cancellation email for reservation {reservation.id}: {str(e)}")
        
        return conflicting_reservations
    @staticmethod
    def update_single_instance(block_id, **updates):
        """
        Update a single block instance.

        Args:
            block_id: ID of the Block to update
            **updates: Dictionary of fields to update

        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            # Get the block
            block = Block.query.get(block_id)
            if not block:
                return False, "Block not found"
            
            # Update the block
            for field, value in updates.items():
                if hasattr(block, field):
                    setattr(block, field, value)

            # If updating time or reason, cancel conflicting reservations
            if 'start_time' in updates or 'end_time' in updates or 'reason_id' in updates:
                BlockService.cancel_conflicting_reservations(block)

            db.session.commit()

            # Log the operation
            BlockService.log_block_operation(
                operation='update',
                block_data={
                    'block_id': block_id,
                    'updates': updates
                },
                admin_id=updates.get('admin_id', block.created_by_id)  # Use provided admin_id or block creator
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
            
            # Flush to get block IDs
            db.session.flush()
            
            # Cancel conflicting reservations for all blocks
            all_cancelled_reservations = []
            for block in blocks:
                cancelled_reservations = BlockService.cancel_conflicting_reservations(block)
                all_cancelled_reservations.extend(cancelled_reservations)
            
            db.session.commit()
            
            # Log the operation
            BlockService.log_block_operation(
                operation='create',
                block_data={
                    'court_ids': court_ids,
                    'date': date.isoformat(),
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'reason_id': reason_id,
                    'details': details,
                    'blocks_created': len(blocks),
                    'reservations_cancelled': len(all_cancelled_reservations)
                },
                admin_id=admin_id
            )
            
            logger.info(f"Multi-court blocks created: {len(blocks)} blocks for {len(court_ids)} courts, "
                       f"cancelled {len(all_cancelled_reservations)} reservations")
            
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
            
            # Get court numbers for the response message
            court_numbers = [block.court.number for block in blocks_to_delete]
            
            # Delete all blocks in the batch
            for block in blocks_to_delete:
                db.session.delete(block)
            
            db.session.commit()
            
            # Log the operation
            BlockService.log_block_operation(
                operation='delete',
                block_data={
                    'batch_id': batch_id,
                    'blocks_deleted': len(blocks_to_delete),
                    'court_numbers': court_numbers
                },
                admin_id=admin_id
            )
            
            logger.info(f"Batch deleted: {batch_id}, {len(blocks_to_delete)} blocks by admin {admin_id}")
            
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
            admin_id: ID of administrator performing the operation
        """
        from app.models import BlockAuditLog
        
        try:
            # Ensure admin_id is not None
            if admin_id is None:
                logger.warning("admin_id is None for block operation logging, skipping audit log")
                return
            
            safe_operation_data = BlockService._serialize_for_json(block_data) if block_data else None
            
            audit_log = BlockAuditLog(
                operation=operation,
                block_id=block_data.get('block_id'),
                operation_data=safe_operation_data,
                admin_id=admin_id
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            logger.info(f"Block operation logged: {operation} by admin {admin_id}")
            
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
