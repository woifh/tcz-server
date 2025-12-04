"""Block service for court blocking."""
from app import db
from app.models import Block, Reservation
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class BlockService:
    """Service for managing court blocks."""
    
    @staticmethod
    def create_block(court_id, date, start_time, end_time, reason, admin_id):
        """
        Create a court block and cancel conflicting reservations.
        
        Args:
            court_id: ID of the court to block
            date: Date to block
            start_time: Start time of block
            end_time: End time of block
            reason: Reason for block (rain, maintenance, tournament, championship)
            admin_id: ID of administrator creating the block
            
        Returns:
            tuple: (Block object or None, error message or None)
        """
        # Create the block
        block = Block(
            court_id=court_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
            created_by_id=admin_id
        )
        
        try:
            db.session.add(block)
            db.session.flush()  # Flush to get block ID but don't commit yet
            
            # Cancel conflicting reservations
            cancelled_reservations = BlockService.cancel_conflicting_reservations(block)
            
            # Commit everything together
            db.session.commit()
            
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
        
        # German reason text mapping
        reason_map = {
            'rain': 'Regen',
            'maintenance': 'Wartung',
            'tournament': 'Turnier',
            'championship': 'Meisterschaft'
        }
        
        reason_text = reason_map.get(block.reason, block.reason)
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
