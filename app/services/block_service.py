"""Block service for court blocking."""
from app import db
from app.models import Block, Reservation, BlockReason, BlockSeries, BlockTemplate, BlockAuditLog
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class BlockService:
    """Service for managing court blocks."""
    
    @staticmethod
    def create_block(court_id, date, start_time, end_time, reason_id, sub_reason, admin_id):
        """
        Create a court block and cancel conflicting reservations.
        
        Args:
            court_id: ID of the court to block
            date: Date to block
            start_time: Start time of block
            end_time: End time of block
            reason_id: ID of the BlockReason
            sub_reason: Optional additional reason detail
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
            reason_id=reason_id,
            sub_reason=sub_reason,
            created_by_id=admin_id
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
                    'sub_reason': sub_reason,
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
        
        # Include sub-reason if provided
        if block.sub_reason:
            cancellation_reason = f"Platzsperre wegen {reason_text} - {block.sub_reason}"
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
    def create_recurring_block_series(court_ids, start_date, end_date, start_time, end_time, 
                                    recurrence_pattern, recurrence_days, reason_id, sub_reason, 
                                    admin_id, series_name):
        """
        Create a recurring block series with individual block instances.
        
        Args:
            court_ids: List of court IDs to block
            start_date: Start date for the series
            end_date: End date for the series
            start_time: Start time for blocks
            end_time: End time for blocks
            recurrence_pattern: 'daily', 'weekly', or 'monthly'
            recurrence_days: List of weekday numbers for weekly pattern (0=Monday, 6=Sunday)
            reason_id: ID of the BlockReason
            sub_reason: Optional additional reason detail
            admin_id: ID of administrator creating the series
            series_name: Name for the series
            
        Returns:
            tuple: (List of Block objects or None, error message or None)
        """
        from app.models import BlockSeries
        from datetime import timedelta
        import calendar
        
        try:
            # Validate inputs
            if end_date < start_date:
                return None, "End date must be after start date"
            
            if not court_ids:
                return None, "At least one court must be specified"
            
            if recurrence_pattern not in ['daily', 'weekly', 'monthly']:
                return None, "Invalid recurrence pattern"
            
            if recurrence_pattern == 'weekly' and not recurrence_days:
                return None, "Weekly recurrence requires specific days"
            
            # Create the BlockSeries record
            series = BlockSeries(
                name=series_name,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                recurrence_pattern=recurrence_pattern,
                recurrence_days=recurrence_days,
                reason_id=reason_id,
                sub_reason=sub_reason,
                created_by_id=admin_id
            )
            
            db.session.add(series)
            db.session.flush()  # Get the series ID
            
            # Generate individual block instances
            blocks = []
            current_date = start_date
            
            while current_date <= end_date:
                should_create_block = False
                
                if recurrence_pattern == 'daily':
                    should_create_block = True
                elif recurrence_pattern == 'weekly':
                    should_create_block = current_date.weekday() in recurrence_days
                elif recurrence_pattern == 'monthly':
                    # For monthly, create on the same day of month as start_date
                    should_create_block = current_date.day == start_date.day
                
                if should_create_block:
                    # Create blocks for all specified courts
                    for court_id in court_ids:
                        block = Block(
                            court_id=court_id,
                            date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            reason_id=reason_id,
                            sub_reason=sub_reason,
                            series_id=series.id,
                            created_by_id=admin_id
                        )
                        
                        db.session.add(block)
                        blocks.append(block)
                        
                        # Cancel conflicting reservations for this block
                        db.session.flush()  # Ensure block has an ID
                        BlockService.cancel_conflicting_reservations(block)
                
                # Move to next date based on pattern
                if recurrence_pattern in ['daily', 'weekly']:
                    current_date += timedelta(days=1)
                elif recurrence_pattern == 'monthly':
                    # Move to next month, handling month-end edge cases
                    try:
                        if current_date.month == 12:
                            next_year = current_date.year + 1
                            next_month = 1
                        else:
                            next_year = current_date.year
                            next_month = current_date.month + 1
                        
                        # Handle cases where target day doesn't exist in next month
                        target_day = start_date.day
                        max_day = calendar.monthrange(next_year, next_month)[1]
                        actual_day = min(target_day, max_day)
                        
                        current_date = current_date.replace(year=next_year, month=next_month, day=actual_day)
                    except ValueError:
                        # If we can't create the next date, break out of the loop
                        break
            
            # Commit all changes
            db.session.commit()
            
            # Log the operation
            BlockService.log_block_operation(
                operation='create',
                block_data={
                    'series_id': series.id,
                    'series_name': series_name,
                    'court_ids': court_ids,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'recurrence_pattern': recurrence_pattern,
                    'recurrence_days': recurrence_days,
                    'reason_id': reason_id,
                    'sub_reason': sub_reason,
                    'blocks_created': len(blocks)
                },
                admin_id=admin_id
            )
            
            logger.info(f"Recurring block series created: {len(blocks)} blocks for pattern {recurrence_pattern}")
            
            return blocks, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create recurring block series: {str(e)}")
            return None, f"Fehler beim Erstellen der wiederkehrenden Sperre: {str(e)}"
    
    @staticmethod
    def get_series_blocks(series_id):
        """
        Get all blocks belonging to a specific series.
        
        Args:
            series_id: ID of the BlockSeries
            
        Returns:
            list: List of Block objects in the series
        """
        return Block.query.filter_by(series_id=series_id).order_by(Block.date, Block.start_time).all()
    
    @staticmethod
    def update_entire_series(series_id, **updates):
        """
        Update all blocks in a series with new values.
        
        Args:
            series_id: ID of the BlockSeries to update
            **updates: Dictionary of fields to update (start_time, end_time, reason_id, sub_reason)
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            # Get the series
            series = BlockSeries.query.get(series_id)
            if not series:
                return False, "Series not found"
            
            # Get all blocks in the series
            blocks = BlockService.get_series_blocks(series_id)
            
            # Update the series record
            for field, value in updates.items():
                if hasattr(series, field):
                    setattr(series, field, value)
            
            # Update all blocks in the series
            for block in blocks:
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
                    'series_id': series_id,
                    'updates': updates,
                    'blocks_updated': len(blocks)
                },
                admin_id=updates.get('admin_id', series.created_by_id)  # Use provided admin_id or series creator
            )
            
            logger.info(f"Updated entire series {series_id}: {len(blocks)} blocks updated")
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update entire series {series_id}: {str(e)}")
            return False, f"Fehler beim Aktualisieren der Serie: {str(e)}"
    
    @staticmethod
    def update_future_series(series_id, from_date, **updates):
        """
        Update all future blocks in a series starting from a specific date.
        
        Args:
            series_id: ID of the BlockSeries to update
            from_date: Date from which to start updating (inclusive)
            **updates: Dictionary of fields to update
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            # Get the series
            series = BlockSeries.query.get(series_id)
            if not series:
                return False, "Series not found"
            
            # Get future blocks in the series
            future_blocks = Block.query.filter(
                Block.series_id == series_id,
                Block.date >= from_date
            ).all()
            
            # Update the series record if updating series-level fields
            series_fields = ['start_time', 'end_time', 'reason_id', 'sub_reason']
            for field in series_fields:
                if field in updates:
                    setattr(series, field, updates[field])
            
            # Update future blocks
            for block in future_blocks:
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
                    'series_id': series_id,
                    'from_date': from_date.isoformat(),
                    'updates': updates,
                    'blocks_updated': len(future_blocks)
                },
                admin_id=updates.get('admin_id', series.created_by_id)  # Use provided admin_id or series creator
            )
            
            logger.info(f"Updated future series {series_id} from {from_date}: {len(future_blocks)} blocks updated")
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update future series {series_id}: {str(e)}")
            return False, f"Fehler beim Aktualisieren der zukünftigen Serie: {str(e)}"
    
    @staticmethod
    def update_single_instance(block_id, **updates):
        """
        Update a single block instance, marking it as modified from the series pattern.
        
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
            
            # Mark as modified if it's part of a series
            if block.series_id:
                block.is_modified = True
            
            # If updating time or reason, cancel conflicting reservations
            if 'start_time' in updates or 'end_time' in updates or 'reason_id' in updates:
                BlockService.cancel_conflicting_reservations(block)
            
            db.session.commit()
            
            # Log the operation
            BlockService.log_block_operation(
                operation='update',
                block_data={
                    'block_id': block_id,
                    'updates': updates,
                    'was_series_member': block.series_id is not None,
                    'marked_modified': block.series_id is not None
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
    def delete_series_options(series_id, option, from_date=None):
        """
        Delete blocks from a series with different options.
        
        Args:
            series_id: ID of the BlockSeries
            option: 'single', 'future', or 'all'
            from_date: Required for 'single' and 'future' options
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            # Get the series
            series = BlockSeries.query.get(series_id)
            if not series:
                return False, "Series not found"
            
            if option == 'single':
                if not from_date:
                    return False, "Date required for single deletion"
                
                # Delete blocks for the specific date
                blocks_to_delete = Block.query.filter(
                    Block.series_id == series_id,
                    Block.date == from_date
                ).all()
                
                for block in blocks_to_delete:
                    db.session.delete(block)
                
                logger.info(f"Deleted single occurrence from series {series_id} on {from_date}")
                
            elif option == 'future':
                if not from_date:
                    return False, "Date required for future deletion"
                
                # Delete blocks from the specified date onwards
                blocks_to_delete = Block.query.filter(
                    Block.series_id == series_id,
                    Block.date >= from_date
                ).all()
                
                for block in blocks_to_delete:
                    db.session.delete(block)
                
                # Update series end_date to the day before from_date
                from datetime import timedelta
                series.end_date = from_date - timedelta(days=1)
                
                logger.info(f"Deleted future occurrences from series {series_id} from {from_date}")
                
            elif option == 'all':
                # Delete all blocks in the series
                blocks_to_delete = Block.query.filter_by(series_id=series_id).all()
                
                for block in blocks_to_delete:
                    db.session.delete(block)
                
                # Delete the series itself
                db.session.delete(series)
                
                logger.info(f"Deleted entire series {series_id}")
                
            else:
                return False, "Invalid deletion option. Must be 'single', 'future', or 'all'"
            
            db.session.commit()
            
            # Log the operation
            BlockService.log_block_operation(
                operation='delete',
                block_data={
                    'series_id': series_id,
                    'option': option,
                    'from_date': from_date.isoformat() if from_date else None,
                    'blocks_deleted': len(blocks_to_delete) if option != 'all' else 'all'
                },
                admin_id=series.created_by_id
            )
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete series {series_id} with option {option}: {str(e)}")
            return False, f"Fehler beim Löschen der Serie: {str(e)}"
    
    @staticmethod
    def create_multi_court_blocks(court_ids, date, start_time, end_time, reason_id, sub_reason, admin_id):
        """
        Create blocks for multiple courts simultaneously.
        
        Args:
            court_ids: List of court IDs to block
            date: Date to block
            start_time: Start time of blocks
            end_time: End time of blocks
            reason_id: ID of the BlockReason
            sub_reason: Optional additional reason detail
            admin_id: ID of administrator creating the blocks
            
        Returns:
            tuple: (List of Block objects or None, error message or None)
        """
        try:
            if not court_ids:
                return None, "At least one court must be specified"
            
            blocks = []
            
            # Create blocks for all specified courts
            for court_id in court_ids:
                block = Block(
                    court_id=court_id,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    reason_id=reason_id,
                    sub_reason=sub_reason,
                    created_by_id=admin_id
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
                    'sub_reason': sub_reason,
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
    def bulk_delete_blocks(block_ids, admin_id):
        """
        Delete multiple blocks in a single transaction.
        
        Args:
            block_ids: List of block IDs to delete
            admin_id: ID of administrator performing the deletion
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        try:
            if not block_ids:
                return False, "No blocks specified for deletion"
            
            # Get all blocks to delete
            blocks_to_delete = Block.query.filter(Block.id.in_(block_ids)).all()
            
            if len(blocks_to_delete) != len(block_ids):
                return False, "Some blocks not found"
            
            # Delete all blocks
            for block in blocks_to_delete:
                db.session.delete(block)
            
            db.session.commit()
            
            # Log the operation
            BlockService.log_block_operation(
                operation='bulk_delete',
                block_data={
                    'block_ids': block_ids,
                    'blocks_deleted': len(blocks_to_delete)
                },
                admin_id=admin_id
            )
            
            logger.info(f"Bulk deleted {len(blocks_to_delete)} blocks by admin {admin_id}")
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to bulk delete blocks: {str(e)}")
            return False, f"Fehler beim Löschen der Sperren: {str(e)}"
    
    @staticmethod
    def create_block_template(name, template_data, admin_id):
        """
        Create a reusable block template.
        
        Args:
            name: Name for the template
            template_data: Dictionary containing template configuration
            admin_id: ID of administrator creating the template
            
        Returns:
            tuple: (BlockTemplate object or None, error message or None)
        """
        from app.models import BlockTemplate
        
        try:
            # Validate required fields
            required_fields = ['court_selection', 'start_time', 'end_time', 'reason_id']
            for field in required_fields:
                if field not in template_data:
                    return None, f"Missing required field: {field}"
            
            # Create the template
            template = BlockTemplate(
                name=name,
                court_selection=template_data['court_selection'],
                start_time=template_data['start_time'],
                end_time=template_data['end_time'],
                reason_id=template_data['reason_id'],
                sub_reason=template_data.get('sub_reason'),
                recurrence_pattern=template_data.get('recurrence_pattern'),
                recurrence_days=template_data.get('recurrence_days'),
                created_by_id=admin_id
            )
            
            db.session.add(template)
            db.session.commit()
            
            logger.info(f"Block template created: {name}")
            
            return template, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create block template {name}: {str(e)}")
            return None, f"Fehler beim Erstellen der Vorlage: {str(e)}"
    
    @staticmethod
    def get_block_templates():
        """
        Get all available block templates.
        
        Returns:
            list: List of BlockTemplate objects
        """
        from app.models import BlockTemplate
        return BlockTemplate.query.order_by(BlockTemplate.name).all()
    
    @staticmethod
    def apply_block_template(template_id, date_overrides):
        """
        Apply a block template to create form data for block creation.
        
        Args:
            template_id: ID of the BlockTemplate to apply
            date_overrides: Dictionary with date-related overrides (start_date, end_date)
            
        Returns:
            dict: Pre-filled form data or None if template not found
        """
        from app.models import BlockTemplate
        
        template = BlockTemplate.query.get(template_id)
        if not template:
            return None
        
        # Build form data from template
        form_data = {
            'court_selection': template.court_selection,
            'start_time': template.start_time,
            'end_time': template.end_time,
            'reason_id': template.reason_id,
            'sub_reason': template.sub_reason,
            'recurrence_pattern': template.recurrence_pattern,
            'recurrence_days': template.recurrence_days
        }
        
        # Apply date overrides
        form_data.update(date_overrides)
        
        return form_data
    
    @staticmethod
    def delete_block_template(template_id, admin_id):
        """
        Delete a block template.
        
        Args:
            template_id: ID of the BlockTemplate to delete
            admin_id: ID of administrator performing the deletion
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        from app.models import BlockTemplate
        
        try:
            template = BlockTemplate.query.get(template_id)
            if not template:
                return False, "Template not found"
            
            db.session.delete(template)
            db.session.commit()
            
            logger.info(f"Block template deleted: {template.name} by admin {admin_id}")
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete block template {template_id}: {str(e)}")
            return False, f"Fehler beim Löschen der Vorlage: {str(e)}"
    
    @staticmethod
    def filter_blocks(date_range=None, court_ids=None, reason_ids=None, block_types=None):
        """
        Filter blocks based on multiple criteria.
        
        Args:
            date_range: Tuple of (start_date, end_date) or None
            court_ids: List of court IDs or None
            reason_ids: List of reason IDs or None
            block_types: List of block types ('single', 'series') or None
            
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
        
        # Filter by block types
        if block_types:
            if 'single' in block_types and 'series' not in block_types:
                query = query.filter(Block.series_id.is_(None))
            elif 'series' in block_types and 'single' not in block_types:
                query = query.filter(Block.series_id.isnot(None))
            # If both are specified or neither, no additional filter needed
        
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
            operation: Type of operation ('create', 'update', 'delete', 'bulk_delete')
            block_data: Dictionary containing operation details
            admin_id: ID of administrator performing the operation
        """
        from app.models import BlockAuditLog
        
        try:
            # Ensure admin_id is not None
            if admin_id is None:
                logger.warning("admin_id is None for block operation logging, skipping audit log")
                return
            
            audit_log = BlockAuditLog(
                operation=operation,
                block_id=block_data.get('block_id'),
                series_id=block_data.get('series_id'),
                operation_data=block_data,
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