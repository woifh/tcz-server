"""Block reason service for managing customizable block reasons."""
from app import db
from app.models import BlockReason, Block
from app.constants.messages import ErrorMessages
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


class BlockReasonService:
    """Service for managing customizable block reasons."""
    
    @staticmethod
    def create_block_reason(name: str, admin_id: int) -> Tuple[Optional[BlockReason], Optional[str]]:
        """
        Create a new block reason.
        
        Args:
            name: Name of the block reason
            admin_id: ID of the administrator creating the reason
            
        Returns:
            tuple: (BlockReason object or None, error message or None)
        """
        try:
            # Validate input
            if not name or not name.strip():
                return None, ErrorMessages.BLOCK_REASON_NAME_EMPTY
            
            name = name.strip()
            
            # Check if reason already exists
            existing_reason = BlockReason.query.filter_by(name=name).first()
            if existing_reason:
                return None, f"Sperrungsgrund '{name}' existiert bereits"
            
            # Create new reason
            reason = BlockReason(
                name=name,
                is_active=True,
                created_by_id=admin_id
            )
            
            db.session.add(reason)
            db.session.commit()
            
            logger.info(f"Block reason created: {name} by admin {admin_id}")
            return reason, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create block reason '{name}': {str(e)}")
            return None, f"Fehler beim Erstellen des Sperrungsgrundes: {str(e)}"
    
    @staticmethod
    def update_block_reason(reason_id: int, name: str, admin_id: int) -> Tuple[bool, Optional[str]]:
        """
        Update an existing block reason with historical preservation.
        
        Args:
            reason_id: ID of the reason to update
            name: New name for the reason
            admin_id: ID of the administrator updating the reason
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            # Validate input
            if not name or not name.strip():
                return False, "Sperrungsgrund-Name darf nicht leer sein"
            
            name = name.strip()
            
            # Find the reason to update
            reason = BlockReason.query.get(reason_id)
            if not reason:
                return False, "Sperrungsgrund nicht gefunden"
            
            # Check if new name conflicts with existing reason
            existing_reason = BlockReason.query.filter(
                BlockReason.name == name,
                BlockReason.id != reason_id
            ).first()
            if existing_reason:
                return False, f"Sperrungsgrund '{name}' existiert bereits"
            
            # Update the reason name
            old_name = reason.name
            reason.name = name
            
            db.session.commit()
            
            logger.info(f"Block reason updated: '{old_name}' -> '{name}' by admin {admin_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update block reason {reason_id}: {str(e)}")
            return False, f"Fehler beim Aktualisieren des Sperrungsgrundes: {str(e)}"
    
    @staticmethod
    def delete_block_reason(reason_id: int, admin_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a block reason with usage checking and historical preservation.
        
        Args:
            reason_id: ID of the reason to delete
            admin_id: ID of the administrator deleting the reason
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            # Find the reason to delete
            reason = BlockReason.query.get(reason_id)
            if not reason:
                return False, "Sperrungsgrund nicht gefunden"
            
            # Check usage count
            usage_count = BlockReasonService.get_reason_usage_count(reason_id)
            
            if usage_count > 0:
                # Reason is in use - delete future blocks and preserve historical data
                future_blocks_deleted = BlockReasonService.cleanup_future_blocks_with_reason(reason.name)
                
                # Mark reason as inactive instead of deleting
                reason.is_active = False
                db.session.commit()
                
                logger.info(f"Block reason '{reason.name}' marked inactive by admin {admin_id}, "
                           f"{future_blocks_deleted} future blocks deleted")
                
                return True, f"Sperrungsgrund wurde deaktiviert. {future_blocks_deleted} zukünftige Sperrungen wurden gelöscht. Historische Daten bleiben erhalten."
            else:
                # Reason is not in use - safe to delete completely
                reason_name = reason.name
                db.session.delete(reason)
                db.session.commit()
                
                logger.info(f"Block reason '{reason_name}' deleted by admin {admin_id}")
                return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete block reason {reason_id}: {str(e)}")
            return False, f"Fehler beim Löschen des Sperrungsgrundes: {str(e)}"
    
    @staticmethod
    def get_all_block_reasons() -> List[BlockReason]:
        """
        Get all active block reasons.
        
        Returns:
            list: List of active BlockReason objects
        """
        return BlockReason.query.filter_by(is_active=True).order_by(BlockReason.name).all()
    
    @staticmethod
    def get_reason_usage_count(reason_id: int) -> int:
        """
        Get the count of blocks using a specific reason.
        
        Args:
            reason_id: ID of the reason to check
            
        Returns:
            int: Number of blocks using this reason
        """
        return Block.query.filter_by(reason_id=reason_id).count()
    
    @staticmethod
    def initialize_default_reasons() -> None:
        """
        Initialize default block reasons if they don't exist.
        
        Creates the following default reasons:
        - Maintenance
        - Weather
        - Tournament
        - Championship
        - Tennis Course
        """
        default_reasons = [
            'Maintenance',
            'Weather',
            'Tournament',
            'Championship',
            'Tennis Course'
        ]
        
        try:
            # Get system admin (first admin user) or create a system user
            from app.models import Member
            system_admin = Member.query.filter_by(role='administrator').first()
            if not system_admin:
                # If no admin exists, we can't initialize reasons
                logger.warning("No administrator found to initialize default block reasons")
                return
            
            created_count = 0
            for reason_name in default_reasons:
                # Check if reason already exists
                existing_reason = BlockReason.query.filter_by(name=reason_name).first()
                if not existing_reason:
                    reason = BlockReason(
                        name=reason_name,
                        is_active=True,
                        created_by_id=system_admin.id
                    )
                    db.session.add(reason)
                    created_count += 1
            
            if created_count > 0:
                db.session.commit()
                logger.info(f"Initialized {created_count} default block reasons")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to initialize default block reasons: {str(e)}")
    
    @staticmethod
    def cleanup_future_blocks_with_reason(reason_name: str) -> int:
        """
        Delete all future blocks that use a specific reason name.
        Used when deleting a reason that is in use.
        
        Args:
            reason_name: Name of the reason to clean up
            
        Returns:
            int: Number of future blocks deleted
        """
        from datetime import date
        
        try:
            # Find the reason by name
            reason = BlockReason.query.filter_by(name=reason_name).first()
            if not reason:
                return 0
            
            # Find all future blocks with this reason
            today = date.today()
            future_blocks = Block.query.filter(
                Block.reason_id == reason.id,
                Block.date > today
            ).all()
            
            # Delete future blocks
            deleted_count = len(future_blocks)
            for block in future_blocks:
                db.session.delete(block)
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} future blocks with reason '{reason_name}'")
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup future blocks with reason '{reason_name}': {str(e)}")
            return 0
