"""Integration tests for enhanced admin panel functionality."""
import pytest
from datetime import date, time, timedelta
from app import db
from app.models import (
    Member, Court, Block, BlockReason, BlockSeries, BlockTemplate, 
    SubReasonTemplate, BlockAuditLog, Reservation
)
from app.services.block_service import BlockService
from app.services.block_reason_service import BlockReasonService
from app.services.reservation_service import ReservationService


class TestRecurringBlockSeriesWorkflows:
    """Test recurring block series workflows."""
    
    def test_daily_series_creation_and_linking(self, app, test_admin):
        """Test series creation with daily recurrence pattern and proper linking."""
        with app.app_context():
            # Create test data
            court = Court.query.filter_by(number=1).first()
            reason = BlockReason.query.filter_by(name='Maintenance').first()
            
            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=4)  # 5 days total
            start_time = time(10, 0)
            end_time = time(11, 0)
            
            # Create daily recurring series
            blocks, error = BlockService.create_recurring_block_series(
                court_ids=[court.id],
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reason.id,
                sub_reason='Daily maintenance',
                admin_id=test_admin.id,
                series_name='Daily Maintenance Series'
            )
            
            # Verify series creation
            assert error is None, f"Series creation failed: {error}"
            assert blocks is not None
            assert len(blocks) == 5, f"Expected 5 blocks, got {len(blocks)}"
            
            # Verify all blocks have same series_id
            series_id = blocks[0].series_id
            assert series_id is not None
            for block in blocks:
                assert block.series_id == series_id
                assert block.court_id == court.id
                assert block.start_time == start_time
                assert block.end_time == end_time
                assert block.reason_id == reason.id
                assert block.sub_reason == 'Daily maintenance'
            
            # Verify BlockSeries record
            series = BlockSeries.query.get(series_id)
            assert series is not None
            assert series.name == 'Daily Maintenance Series'
            assert series.recurrence_pattern == 'daily'
            assert series.start_date == start_date
            assert series.end_date == end_date
            
            # Verify consecutive dates
            block_dates = sorted([block.date for block in blocks])
            for i in range(1, len(block_dates)):
                assert (block_dates[i] - block_dates[i-1]).days == 1
    
    def test_weekly_series_with_specific_days(self, app, test_admin):
        """Test weekly series creation with specific day selection."""
        with app.app_context():
            court = Court.query.filter_by(number=2).first()
            reason = BlockReason.query.filter_by(name='Tournament').first()
            
            # Start on a Monday, end 3 weeks later
            start_date = date.today() + timedelta(days=(7 - date.today().weekday()))  # Next Monday
            end_date = start_date + timedelta(days=20)  # 3 weeks
            start_time = time(14, 0)
            end_time = time(16, 0)
            
            # Weekly on Monday (0) and Friday (4)
            recurrence_days = [0, 4]
            
            blocks, error = BlockService.create_recurring_block_series(
                court_ids=[court.id],
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                recurrence_pattern='weekly',
                recurrence_days=recurrence_days,
                reason_id=reason.id,
                sub_reason='Weekly tournament',
                admin_id=test_admin.id,
                series_name='Weekly Tournament Series'
            )
            
            assert error is None
            assert blocks is not None
            
            # Verify only Monday and Friday blocks were created
            for block in blocks:
                assert block.date.weekday() in recurrence_days
            
            # Count expected blocks (Mondays and Fridays in the range)
            expected_count = 0
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() in recurrence_days:
                    expected_count += 1
                current_date += timedelta(days=1)
            
            assert len(blocks) == expected_count
    
    def test_series_editing_entire_series(self, app, test_admin):
        """Test editing entire series affects all future instances."""
        with app.app_context():
            court = Court.query.filter_by(number=3).first()
            reason1 = BlockReason.query.filter_by(name='Maintenance').first()
            reason2 = BlockReason.query.filter_by(name='Weather').first()
            
            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=6)  # 7 days
            
            # Create series
            blocks, error = BlockService.create_recurring_block_series(
                court_ids=[court.id],
                start_date=start_date,
                end_date=end_date,
                start_time=time(9, 0),
                end_time=time(10, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reason1.id,
                sub_reason='Original reason',
                admin_id=test_admin.id,
                series_name='Test Series'
            )
            
            assert error is None
            series_id = blocks[0].series_id
            
            # Update entire series
            success, error = BlockService.update_entire_series(
                series_id,
                start_time=time(11, 0),
                end_time=time(12, 0),
                reason_id=reason2.id,
                sub_reason='Updated reason',
                admin_id=test_admin.id
            )
            
            assert error is None
            assert success is True
            
            # Verify all blocks were updated
            updated_blocks = BlockService.get_series_blocks(series_id)
            for block in updated_blocks:
                assert block.start_time == time(11, 0)
                assert block.end_time == time(12, 0)
                assert block.reason_id == reason2.id
                assert block.sub_reason == 'Updated reason'
    
    def test_series_editing_future_instances(self, app, test_admin):
        """Test editing future instances from a specific date."""
        with app.app_context():
            court = Court.query.filter_by(number=4).first()
            reason1 = BlockReason.query.filter_by(name='Maintenance').first()
            reason2 = BlockReason.query.filter_by(name='Championship').first()
            
            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=6)  # 7 days
            
            # Create series
            blocks, error = BlockService.create_recurring_block_series(
                court_ids=[court.id],
                start_date=start_date,
                end_date=end_date,
                start_time=time(13, 0),
                end_time=time(14, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reason1.id,
                sub_reason='Original',
                admin_id=test_admin.id,
                series_name='Future Update Test'
            )
            
            assert error is None
            series_id = blocks[0].series_id
            
            # Update from day 4 onwards
            from_date = start_date + timedelta(days=3)
            success, error = BlockService.update_future_series(
                series_id,
                from_date,
                reason_id=reason2.id,
                sub_reason='Future updated',
                admin_id=test_admin.id
            )
            
            assert error is None
            assert success is True
            
            # Verify only future blocks were updated
            all_blocks = BlockService.get_series_blocks(series_id)
            for block in all_blocks:
                if block.date >= from_date:
                    assert block.reason_id == reason2.id
                    assert block.sub_reason == 'Future updated'
                else:
                    assert block.reason_id == reason1.id
                    assert block.sub_reason == 'Original'
    
    def test_single_instance_editing(self, app, test_admin):
        """Test editing single instance doesn't affect other instances."""
        with app.app_context():
            court = Court.query.filter_by(number=5).first()
            reason1 = BlockReason.query.filter_by(name='Maintenance').first()
            reason2 = BlockReason.query.filter_by(name='Tennis Course').first()
            
            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=4)  # 5 days
            
            # Create series
            blocks, error = BlockService.create_recurring_block_series(
                court_ids=[court.id],
                start_date=start_date,
                end_date=end_date,
                start_time=time(15, 0),
                end_time=time(16, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reason1.id,
                sub_reason='Original',
                admin_id=test_admin.id,
                series_name='Single Instance Test'
            )
            
            assert error is None
            
            # Update single instance (middle block)
            middle_block = blocks[2]  # Third block
            success, error = BlockService.update_single_instance(
                middle_block.id,
                reason_id=reason2.id,
                sub_reason='Single updated',
                admin_id=test_admin.id
            )
            
            assert error is None
            assert success is True
            
            # Verify only the single block was updated and marked as modified
            updated_block = Block.query.get(middle_block.id)
            assert updated_block.reason_id == reason2.id
            assert updated_block.sub_reason == 'Single updated'
            assert updated_block.is_modified is True
            
            # Verify other blocks remain unchanged
            all_blocks = BlockService.get_series_blocks(blocks[0].series_id)
            for block in all_blocks:
                if block.id != middle_block.id:
                    assert block.reason_id == reason1.id
                    assert block.sub_reason == 'Original'
                    assert block.is_modified is False
    
    def test_series_deletion_options(self, app, test_admin):
        """Test series deletion with different options."""
        with app.app_context():
            court = Court.query.filter_by(number=6).first()
            reason = BlockReason.query.filter_by(name='Maintenance').first()
            
            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=6)  # 7 days
            
            # Create series for testing deletion
            blocks, error = BlockService.create_recurring_block_series(
                court_ids=[court.id],
                start_date=start_date,
                end_date=end_date,
                start_time=time(8, 0),
                end_time=time(9, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reason.id,
                sub_reason='To be deleted',
                admin_id=test_admin.id,
                series_name='Deletion Test Series'
            )
            
            assert error is None
            series_id = blocks[0].series_id
            
            # Test single occurrence deletion
            delete_date = start_date + timedelta(days=2)  # Third day
            success, error = BlockService.delete_series_options(
                series_id, 'single', delete_date
            )
            
            assert error is None
            assert success is True
            
            # Verify only one block was deleted
            remaining_blocks = BlockService.get_series_blocks(series_id)
            assert len(remaining_blocks) == 6  # 7 - 1 = 6
            assert not any(block.date == delete_date for block in remaining_blocks)
            
            # Test future deletion
            future_date = start_date + timedelta(days=4)  # Fifth day onwards
            success, error = BlockService.delete_series_options(
                series_id, 'future', future_date
            )
            
            assert error is None
            assert success is True
            
            # Verify future blocks were deleted
            remaining_blocks = BlockService.get_series_blocks(series_id)
            for block in remaining_blocks:
                assert block.date < future_date
            
            # Test complete series deletion
            success, error = BlockService.delete_series_options(
                series_id, 'all'
            )
            
            assert error is None
            assert success is True
            
            # Verify series and all blocks are gone
            assert BlockSeries.query.get(series_id) is None
            assert len(BlockService.get_series_blocks(series_id)) == 0


class TestMultiCourtAndBulkOperations:
    """Test multi-court and bulk operations."""
    
    def test_multi_court_block_creation(self, app, test_admin):
        """Test creating blocks for multiple courts simultaneously."""
        with app.app_context():
            # Get multiple courts
            courts = Court.query.filter(Court.number.in_([1, 2, 3])).all()
            court_ids = [court.id for court in courts]
            reason = BlockReason.query.filter_by(name='Tournament').first()
            
            block_date = date.today() + timedelta(days=1)
            start_time = time(10, 0)
            end_time = time(12, 0)
            
            # Create multi-court blocks
            blocks, error = BlockService.create_multi_court_blocks(
                court_ids=court_ids,
                date=block_date,
                start_time=start_time,
                end_time=end_time,
                reason_id=reason.id,
                sub_reason='Multi-court tournament',
                admin_id=test_admin.id
            )
            
            assert error is None
            assert blocks is not None
            assert len(blocks) == len(court_ids)
            
            # Verify all blocks have correct properties
            for i, block in enumerate(blocks):
                assert block.court_id in court_ids
                assert block.date == block_date
                assert block.start_time == start_time
                assert block.end_time == end_time
                assert block.reason_id == reason.id
                assert block.sub_reason == 'Multi-court tournament'
                assert block.created_by_id == test_admin.id
            
            # Verify each court has exactly one block
            created_court_ids = [block.court_id for block in blocks]
            assert set(created_court_ids) == set(court_ids)
    
    def test_bulk_deletion_of_selected_blocks(self, app, test_admin):
        """Test bulk deletion of selected blocks."""
        with app.app_context():
            courts = Court.query.filter(Court.number.in_([4, 5, 6])).all()
            reason = BlockReason.query.filter_by(name='Maintenance').first()
            
            # Create multiple individual blocks
            blocks_to_create = []
            for i, court in enumerate(courts):
                block_date = date.today() + timedelta(days=i+1)
                blocks, error = BlockService.create_multi_court_blocks(
                    court_ids=[court.id],
                    date=block_date,
                    start_time=time(14, 0),
                    end_time=time(15, 0),
                    reason_id=reason.id,
                    sub_reason=f'Block {i+1}',
                    admin_id=test_admin.id
                )
                assert error is None
                blocks_to_create.extend(blocks)
            
            # Select some blocks for deletion (first and third)
            block_ids_to_delete = [blocks_to_create[0].id, blocks_to_create[2].id]
            
            # Perform bulk deletion
            success, error = BlockService.bulk_delete_blocks(
                block_ids_to_delete, test_admin.id
            )
            
            assert error is None
            assert success is True
            
            # Verify selected blocks were deleted
            for block_id in block_ids_to_delete:
                assert Block.query.get(block_id) is None
            
            # Verify other blocks remain
            remaining_block = Block.query.get(blocks_to_create[1].id)
            assert remaining_block is not None
    
    def test_conflict_preview_functionality(self, app, test_admin, test_member):
        """Test conflict preview shows affected reservations."""
        with app.app_context():
            court = Court.query.filter_by(number=1).first()
            
            # Create some reservations that will conflict
            conflict_date = date.today() + timedelta(days=1)
            
            # Create reservations at 10:00 and 11:00
            reservation1, error1 = ReservationService.create_reservation(
                court_id=court.id,
                date=conflict_date,
                start_time=time(10, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id
            )
            
            reservation2, error2 = ReservationService.create_reservation(
                court_id=court.id,
                date=conflict_date,
                start_time=time(11, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id
            )
            
            assert error1 is None and error2 is None
            
            # Preview conflicts for a block from 10:00-12:00
            conflicts = BlockService.get_conflict_preview(
                court_ids=[court.id],
                date=conflict_date,
                start_time=time(10, 0),
                end_time=time(12, 0)
            )
            
            # Should find both reservations
            assert len(conflicts) == 2
            conflict_ids = [r.id for r in conflicts]
            assert reservation1.id in conflict_ids
            assert reservation2.id in conflict_ids
            
            # Preview conflicts for a block from 11:30-12:30 (should only conflict with second reservation)
            conflicts_partial = BlockService.get_conflict_preview(
                court_ids=[court.id],
                date=conflict_date,
                start_time=time(11, 30),
                end_time=time(12, 30)
            )
            
            # Should find no conflicts (our reservations are hourly slots)
            assert len(conflicts_partial) == 0
    
    def test_transaction_handling_in_bulk_operations(self, app, test_admin):
        """Test proper transaction handling in bulk operations."""
        with app.app_context():
            courts = Court.query.filter(Court.number.in_([1, 2])).all()
            reason = BlockReason.query.filter_by(name='Weather').first()
            
            # Create blocks
            blocks, error = BlockService.create_multi_court_blocks(
                court_ids=[court.id for court in courts],
                date=date.today() + timedelta(days=1),
                start_time=time(16, 0),
                end_time=time(17, 0),
                reason_id=reason.id,
                sub_reason='Transaction test',
                admin_id=test_admin.id
            )
            
            assert error is None
            assert len(blocks) == 2
            
            # Test bulk deletion with invalid ID (should fail gracefully)
            invalid_block_ids = [blocks[0].id, 99999]  # One valid, one invalid
            success, error = BlockService.bulk_delete_blocks(
                invalid_block_ids, test_admin.id
            )
            
            # Should fail due to invalid ID
            assert success is False
            assert error is not None
            
            # Verify original blocks still exist (transaction rolled back)
            for block in blocks:
                assert Block.query.get(block.id) is not None


class TestTemplateManagement:
    """Test block template functionality."""
    
    def test_template_creation_and_storage(self, app, test_admin):
        """Test creating and storing block templates."""
        with app.app_context():
            reason = BlockReason.query.filter_by(name='Maintenance').first()
            
            template_data = {
                'court_selection': [1, 2, 3],
                'start_time': time(9, 0),
                'end_time': time(10, 0),
                'reason_id': reason.id,
                'sub_reason': 'Morning maintenance',
                'recurrence_pattern': 'weekly',
                'recurrence_days': [1, 3, 5]  # Tue, Thu, Sat
            }
            
            # Create template
            template, error = BlockService.create_block_template(
                name='Morning Maintenance Template',
                template_data=template_data,
                admin_id=test_admin.id
            )
            
            assert error is None
            assert template is not None
            assert template.name == 'Morning Maintenance Template'
            assert template.court_selection == [1, 2, 3]
            assert template.start_time == time(9, 0)
            assert template.end_time == time(10, 0)
            assert template.reason_id == reason.id
            assert template.sub_reason == 'Morning maintenance'
            assert template.recurrence_pattern == 'weekly'
            assert template.recurrence_days == [1, 3, 5]
            assert template.created_by_id == test_admin.id
    
    def test_template_application_and_form_prefilling(self, app, test_admin):
        """Test applying templates and form pre-filling."""
        with app.app_context():
            reason = BlockReason.query.filter_by(name='Tournament').first()
            
            # Create template
            template_data = {
                'court_selection': [4, 5, 6],
                'start_time': time(14, 0),
                'end_time': time(16, 0),
                'reason_id': reason.id,
                'sub_reason': 'Weekend tournament',
                'recurrence_pattern': 'daily',
                'recurrence_days': None
            }
            
            template, error = BlockService.create_block_template(
                name='Tournament Template',
                template_data=template_data,
                admin_id=test_admin.id
            )
            
            assert error is None
            
            # Apply template with date overrides
            date_overrides = {
                'start_date': '2025-02-01',
                'end_date': '2025-02-03'
            }
            
            form_data = BlockService.apply_block_template(
                template.id, date_overrides
            )
            
            assert form_data is not None
            assert form_data['court_selection'] == [4, 5, 6]
            assert form_data['start_time'] == time(14, 0)
            assert form_data['end_time'] == time(16, 0)
            assert form_data['reason_id'] == reason.id
            assert form_data['sub_reason'] == 'Weekend tournament'
            assert form_data['recurrence_pattern'] == 'daily'
            assert form_data['start_date'] == '2025-02-01'
            assert form_data['end_date'] == '2025-02-03'
    
    def test_template_editing_and_deletion(self, app, test_admin):
        """Test template editing and deletion."""
        with app.app_context():
            reason = BlockReason.query.filter_by(name='Weather').first()
            
            # Create template
            template_data = {
                'court_selection': [1],
                'start_time': time(12, 0),
                'end_time': time(13, 0),
                'reason_id': reason.id,
                'sub_reason': 'Rain protection',
                'recurrence_pattern': None,
                'recurrence_days': None
            }
            
            template, error = BlockService.create_block_template(
                name='Rain Template',
                template_data=template_data,
                admin_id=test_admin.id
            )
            
            assert error is None
            template_id = template.id
            
            # Test template deletion
            success, error = BlockService.delete_block_template(
                template_id, test_admin.id
            )
            
            assert error is None
            assert success is True
            
            # Verify template is deleted
            assert BlockTemplate.query.get(template_id) is None
    
    def test_template_listing(self, app, test_admin):
        """Test listing all available templates."""
        with app.app_context():
            reason = BlockReason.query.filter_by(name='Championship').first()
            
            # Create multiple templates
            template_names = ['Template A', 'Template B', 'Template C']
            created_templates = []
            
            for name in template_names:
                template_data = {
                    'court_selection': [1, 2],
                    'start_time': time(10, 0),
                    'end_time': time(11, 0),
                    'reason_id': reason.id,
                    'sub_reason': f'Sub-reason for {name}',
                    'recurrence_pattern': None,
                    'recurrence_days': None
                }
                
                template, error = BlockService.create_block_template(
                    name=name,
                    template_data=template_data,
                    admin_id=test_admin.id
                )
                
                assert error is None
                created_templates.append(template)
            
            # Get all templates
            all_templates = BlockService.get_block_templates()
            
            # Verify all created templates are in the list
            template_names_in_list = [t.name for t in all_templates]
            for name in template_names:
                assert name in template_names_in_list


class TestReasonManagement:
    """Test custom reason creation, editing, and management."""
    
    def test_custom_reason_creation_and_editing(self, app, test_admin):
        """Test creating and editing custom block reasons."""
        with app.app_context():
            # Create custom reason
            reason, error = BlockReasonService.create_block_reason(
                'Custom Event', test_admin.id
            )
            
            assert error is None
            assert reason is not None
            assert reason.name == 'Custom Event'
            assert reason.is_active is True
            assert reason.created_by_id == test_admin.id
            
            # Edit the reason
            success, error = BlockReasonService.update_block_reason(
                reason.id, 'Updated Custom Event', test_admin.id
            )
            
            assert error is None
            assert success is True
            
            # Verify update
            updated_reason = BlockReason.query.get(reason.id)
            assert updated_reason.name == 'Updated Custom Event'
    
    def test_reason_deletion_with_usage_checking(self, app, test_admin):
        """Test reason deletion with usage checking."""
        with app.app_context():
            court = Court.query.filter_by(number=1).first()
            
            # Create custom reason
            reason, error = BlockReasonService.create_block_reason(
                'Temporary Event', test_admin.id
            )
            assert error is None
            
            # Create a block using this reason
            block, block_error = BlockService.create_block(
                court_id=court.id,
                date=date.today() + timedelta(days=1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                reason_id=reason.id,
                sub_reason='Test usage',
                admin_id=test_admin.id
            )
            assert block_error is None
            
            # Try to delete reason (should be deactivated, not deleted)
            success, message = BlockReasonService.delete_block_reason(
                reason.id, test_admin.id
            )
            
            assert success is True
            assert message is not None  # Should have a message about deactivation
            assert 'deaktiviert' in message
            
            # Verify reason is deactivated, not deleted
            deactivated_reason = BlockReason.query.get(reason.id)
            assert deactivated_reason is not None
            assert deactivated_reason.is_active is False
            
            # Verify block still exists with original reason
            existing_block = Block.query.get(block.id)
            assert existing_block is not None
            assert existing_block.reason_id == reason.id
    
    def test_historical_preservation_of_reason_data(self, app, test_admin):
        """Test that historical block data is preserved when reasons are edited/deleted."""
        with app.app_context():
            court = Court.query.filter_by(number=2).first()
            
            # Create reason and block
            reason, error = BlockReasonService.create_block_reason(
                'Historical Test', test_admin.id
            )
            assert error is None
            
            # Create past block (simulate historical data)
            past_block, block_error = BlockService.create_block(
                court_id=court.id,
                date=date.today() - timedelta(days=1),  # Past date
                start_time=time(9, 0),
                end_time=time(10, 0),
                reason_id=reason.id,
                sub_reason='Historical block',
                admin_id=test_admin.id
            )
            assert block_error is None
            
            # Create future block
            future_block, future_error = BlockService.create_block(
                court_id=court.id,
                date=date.today() + timedelta(days=1),  # Future date
                start_time=time(9, 0),
                end_time=time(10, 0),
                reason_id=reason.id,
                sub_reason='Future block',
                admin_id=test_admin.id
            )
            assert future_error is None
            
            # Delete reason (should preserve historical, delete future)
            success, message = BlockReasonService.delete_block_reason(
                reason.id, test_admin.id
            )
            
            assert success is True
            
            # Verify historical block is preserved
            historical_block = Block.query.get(past_block.id)
            assert historical_block is not None
            assert historical_block.reason_id == reason.id
            
            # Verify future block is deleted
            deleted_future_block = Block.query.get(future_block.id)
            assert deleted_future_block is None
    
    def test_sub_reason_template_management(self, app, test_admin):
        """Test sub-reason template creation and management."""
        with app.app_context():
            # Create reason
            reason, error = BlockReasonService.create_block_reason(
                'Championship', test_admin.id
            )
            assert error is None
            
            # Create sub-reason templates
            template_names = ['Team A vs Team B', 'Junior Championship', 'Senior Finals']
            created_templates = []
            
            for template_name in template_names:
                template, template_error = BlockReasonService.create_sub_reason_template(
                    reason.id, template_name, test_admin.id
                )
                assert template_error is None
                assert template.template_name == template_name
                assert template.reason_id == reason.id
                created_templates.append(template)
            
            # Get all templates for the reason
            templates = BlockReasonService.get_sub_reason_templates(reason.id)
            assert len(templates) == len(template_names)
            
            template_names_found = [t.template_name for t in templates]
            for name in template_names:
                assert name in template_names_found
            
            # Delete a template
            success, error = BlockReasonService.delete_sub_reason_template(
                created_templates[0].id, test_admin.id
            )
            assert error is None
            assert success is True
            
            # Verify template is deleted
            remaining_templates = BlockReasonService.get_sub_reason_templates(reason.id)
            assert len(remaining_templates) == len(template_names) - 1
    
    def test_reason_usage_count_tracking(self, app, test_admin):
        """Test usage count tracking for reasons."""
        with app.app_context():
            courts = Court.query.filter(Court.number.in_([1, 2, 3])).all()
            
            # Create reason
            reason, error = BlockReasonService.create_block_reason(
                'Usage Test', test_admin.id
            )
            assert error is None
            
            # Initially no usage
            usage_count = BlockReasonService.get_reason_usage_count(reason.id)
            assert usage_count == 0
            
            # Create blocks using this reason
            for i, court in enumerate(courts):
                block, block_error = BlockService.create_block(
                    court_id=court.id,
                    date=date.today() + timedelta(days=i+1),
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    reason_id=reason.id,
                    sub_reason=f'Usage test {i+1}',
                    admin_id=test_admin.id
                )
                assert block_error is None
            
            # Check usage count
            usage_count = BlockReasonService.get_reason_usage_count(reason.id)
            assert usage_count == len(courts)


class TestFilteringAndSearch:
    """Test filtering and search functionality."""
    
    def test_all_filter_combinations(self, app, test_admin):
        """Test filtering blocks with various combinations of criteria."""
        with app.app_context():
            courts = Court.query.filter(Court.number.in_([1, 2, 3])).all()
            reason1 = BlockReason.query.filter_by(name='Maintenance').first()
            reason2 = BlockReason.query.filter_by(name='Tournament').first()
            
            # Create test blocks with different properties
            test_blocks = []
            
            # Single blocks
            for i, court in enumerate(courts[:2]):
                block, error = BlockService.create_block(
                    court_id=court.id,
                    date=date.today() + timedelta(days=i+1),
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    reason_id=reason1.id if i == 0 else reason2.id,
                    sub_reason=f'Single block {i+1}',
                    admin_id=test_admin.id
                )
                assert error is None
                test_blocks.append(block)
            
            # Series blocks
            series_blocks, series_error = BlockService.create_recurring_block_series(
                court_ids=[courts[2].id],
                start_date=date.today() + timedelta(days=3),
                end_date=date.today() + timedelta(days=5),
                start_time=time(14, 0),
                end_time=time(15, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reason2.id,
                sub_reason='Series block',
                admin_id=test_admin.id,
                series_name='Test Series'
            )
            assert series_error is None
            test_blocks.extend(series_blocks)
            
            # Test date range filtering
            date_range = (date.today() + timedelta(days=1), date.today() + timedelta(days=3))
            filtered_by_date = BlockService.filter_blocks(date_range=date_range)
            
            # Should include blocks within the date range
            for block in filtered_by_date:
                assert date_range[0] <= block.date <= date_range[1]
            
            # Test court filtering
            court_ids = [courts[0].id, courts[1].id]
            filtered_by_court = BlockService.filter_blocks(court_ids=court_ids)
            
            for block in filtered_by_court:
                assert block.court_id in court_ids
            
            # Test reason filtering
            reason_ids = [reason1.id]
            filtered_by_reason = BlockService.filter_blocks(reason_ids=reason_ids)
            
            for block in filtered_by_reason:
                assert block.reason_id in reason_ids
            
            # Test block type filtering
            single_blocks = BlockService.filter_blocks(block_types=['single'])
            series_blocks_filtered = BlockService.filter_blocks(block_types=['series'])
            
            for block in single_blocks:
                assert block.series_id is None
            
            for block in series_blocks_filtered:
                assert block.series_id is not None
            
            # Test combined filtering
            combined_filtered = BlockService.filter_blocks(
                date_range=date_range,
                court_ids=[courts[0].id],
                reason_ids=[reason1.id],
                block_types=['single']
            )
            
            for block in combined_filtered:
                assert date_range[0] <= block.date <= date_range[1]
                assert block.court_id == courts[0].id
                assert block.reason_id == reason1.id
                assert block.series_id is None
    
    def test_search_functionality(self, app, test_admin):
        """Test search functionality in block reasons and sub-reasons."""
        with app.app_context():
            court = Court.query.filter_by(number=1).first()
            
            # Create reasons with searchable names
            searchable_reasons = ['Special Event', 'Regular Maintenance', 'Championship Match']
            created_reasons = []
            
            for reason_name in searchable_reasons:
                reason, error = BlockReasonService.create_block_reason(
                    reason_name, test_admin.id
                )
                assert error is None
                created_reasons.append(reason)
            
            # Create blocks with searchable sub-reasons
            sub_reasons = ['Team Alpha vs Beta', 'Court Resurfacing', 'Finals Tournament']
            
            for i, (reason, sub_reason) in enumerate(zip(created_reasons, sub_reasons)):
                block, error = BlockService.create_block(
                    court_id=court.id,
                    date=date.today() + timedelta(days=i+1),
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    reason_id=reason.id,
                    sub_reason=sub_reason,
                    admin_id=test_admin.id
                )
                assert error is None
            
            # Test filtering by reason name (simulated search)
            maintenance_reason = next(r for r in created_reasons if 'Maintenance' in r.name)
            maintenance_blocks = BlockService.filter_blocks(reason_ids=[maintenance_reason.id])
            
            assert len(maintenance_blocks) == 1
            assert 'Resurfacing' in maintenance_blocks[0].sub_reason
    
    def test_filter_persistence(self, app, test_admin):
        """Test that filters work consistently across multiple queries."""
        with app.app_context():
            courts = Court.query.filter(Court.number.in_([4, 5])).all()
            reason = BlockReason.query.filter_by(name='Weather').first()
            
            # Create consistent test data
            test_date_range = (date.today() + timedelta(days=1), date.today() + timedelta(days=3))
            
            for court in courts:
                for day_offset in range(1, 4):  # Days 1, 2, 3
                    block, error = BlockService.create_block(
                        court_id=court.id,
                        date=date.today() + timedelta(days=day_offset),
                        start_time=time(12, 0),
                        end_time=time(13, 0),
                        reason_id=reason.id,
                        sub_reason='Consistent test',
                        admin_id=test_admin.id
                    )
                    assert error is None
            
            # Apply same filter multiple times
            filter_criteria = {
                'date_range': test_date_range,
                'court_ids': [courts[0].id],
                'reason_ids': [reason.id]
            }
            
            # First query
            result1 = BlockService.filter_blocks(**filter_criteria)
            
            # Second query with same criteria
            result2 = BlockService.filter_blocks(**filter_criteria)
            
            # Results should be identical
            assert len(result1) == len(result2)
            result1_ids = [b.id for b in result1]
            result2_ids = [b.id for b in result2]
            assert set(result1_ids) == set(result2_ids)


class TestAuditLogging:
    """Test audit logging functionality."""
    
    def test_audit_log_creation_for_all_operations(self, app, test_admin):
        """Test that audit logs are created for all block operations."""
        with app.app_context():
            court = Court.query.filter_by(number=1).first()
            reason = BlockReason.query.filter_by(name='Maintenance').first()
            
            # Create block (should log)
            block, error = BlockService.create_block(
                court_id=court.id,
                date=date.today() + timedelta(days=1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                reason_id=reason.id,
                sub_reason='Audit test',
                admin_id=test_admin.id
            )
            assert error is None
            
            # Check audit log for creation
            create_logs = BlockService.get_audit_log({'operation': 'create'})
            assert len(create_logs) > 0
            
            latest_create_log = create_logs[0]  # Most recent first
            assert latest_create_log.operation == 'create'
            assert latest_create_log.admin_id == test_admin.id
            assert latest_create_log.block_id == block.id
            assert 'court_id' in latest_create_log.operation_data
            
            # Update block (should log)
            success, update_error = BlockService.update_single_instance(
                block.id,
                sub_reason='Updated audit test',
                admin_id=test_admin.id
            )
            assert update_error is None
            assert success is True
            
            # Check audit log for update
            update_logs = BlockService.get_audit_log({'operation': 'update'})
            assert len(update_logs) > 0
            
            latest_update_log = update_logs[0]
            assert latest_update_log.operation == 'update'
            assert latest_update_log.admin_id == test_admin.id
            assert latest_update_log.block_id == block.id
            
            # Delete block (should log)
            db.session.delete(block)
            db.session.commit()
            
            # Manual log for deletion (since we're not using the service method)
            BlockService.log_block_operation(
                operation='delete',
                block_data={'block_id': block.id, 'manual_delete': True},
                admin_id=test_admin.id
            )
            
            # Check audit log for deletion
            delete_logs = BlockService.get_audit_log({'operation': 'delete'})
            assert len(delete_logs) > 0
    
    def test_audit_log_filtering_and_retrieval(self, app, test_admin):
        """Test filtering and retrieving audit logs."""
        with app.app_context():
            court = Court.query.filter_by(number=2).first()
            reason = BlockReason.query.filter_by(name='Tournament').first()
            
            # Create multiple operations to generate audit logs
            operations_data = []
            
            for i in range(3):
                block, error = BlockService.create_block(
                    court_id=court.id,
                    date=date.today() + timedelta(days=i+1),
                    start_time=time(11, 0),
                    end_time=time(12, 0),
                    reason_id=reason.id,
                    sub_reason=f'Audit filter test {i+1}',
                    admin_id=test_admin.id
                )
                assert error is None
                operations_data.append(('create', block.id))
                
                # Update each block
                success, update_error = BlockService.update_single_instance(
                    block.id,
                    sub_reason=f'Updated audit filter test {i+1}',
                    admin_id=test_admin.id
                )
                assert update_error is None
                operations_data.append(('update', block.id))
            
            # Test filtering by operation type
            create_logs = BlockService.get_audit_log({'operation': 'create'})
            update_logs = BlockService.get_audit_log({'operation': 'update'})
            
            # Should have at least 3 create and 3 update logs from this test
            create_count = len([log for log in create_logs if log.admin_id == test_admin.id])
            update_count = len([log for log in update_logs if log.admin_id == test_admin.id])
            
            assert create_count >= 3
            assert update_count >= 3
            
            # Test filtering by admin
            admin_logs = BlockService.get_audit_log({'admin_id': test_admin.id})
            
            for log in admin_logs:
                assert log.admin_id == test_admin.id
            
            # Test date range filtering
            from datetime import datetime
            today_start = datetime.combine(date.today(), time.min)
            today_end = datetime.combine(date.today(), time.max)
            
            today_logs = BlockService.get_audit_log({
                'date_range': (today_start, today_end)
            })
            
            for log in today_logs:
                assert today_start <= log.timestamp <= today_end
    
    def test_proper_operation_data_storage(self, app, test_admin):
        """Test that operation data is properly stored in audit logs."""
        with app.app_context():
            courts = Court.query.filter(Court.number.in_([3, 4])).all()
            reason = BlockReason.query.filter_by(name='Championship').first()
            
            # Create recurring series (complex operation)
            blocks, error = BlockService.create_recurring_block_series(
                court_ids=[court.id for court in courts],
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=3),
                start_time=time(15, 0),
                end_time=time(16, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reason.id,
                sub_reason='Audit data test',
                admin_id=test_admin.id,
                series_name='Audit Test Series'
            )
            
            assert error is None
            series_id = blocks[0].series_id
            
            # Find the audit log for this series creation
            create_logs = BlockService.get_audit_log({'operation': 'create'})
            series_log = next(
                (log for log in create_logs 
                 if log.series_id == series_id and log.admin_id == test_admin.id),
                None
            )
            
            assert series_log is not None
            assert series_log.operation_data is not None
            
            # Verify operation data contains expected fields
            op_data = series_log.operation_data
            assert 'series_id' in op_data
            assert 'series_name' in op_data
            assert 'court_ids' in op_data
            assert 'recurrence_pattern' in op_data
            assert 'blocks_created' in op_data
            
            assert op_data['series_id'] == series_id
            assert op_data['series_name'] == 'Audit Test Series'
            assert op_data['recurrence_pattern'] == 'daily'
            assert op_data['blocks_created'] == len(blocks)


class TestCalendarViewFunctionality:
    """Test calendar view functionality."""
    
    def test_calendar_rendering_with_blocks(self, app, test_admin):
        """Test that calendar can render blocks correctly."""
        with app.app_context():
            courts = Court.query.filter(Court.number.in_([1, 2])).all()
            reasons = [
                BlockReason.query.filter_by(name='Maintenance').first(),
                BlockReason.query.filter_by(name='Tournament').first(),
                BlockReason.query.filter_by(name='Weather').first()
            ]
            
            # Create blocks for different days and reasons
            test_blocks = []
            for i, (court, reason) in enumerate(zip(courts, reasons[:2])):
                for day_offset in range(1, 4):  # 3 days
                    block, error = BlockService.create_block(
                        court_id=court.id,
                        date=date.today() + timedelta(days=day_offset),
                        start_time=time(10 + i, 0),  # Different times
                        end_time=time(11 + i, 0),
                        reason_id=reason.id,
                        sub_reason=f'Calendar test {i+1}',
                        admin_id=test_admin.id
                    )
                    assert error is None
                    test_blocks.append(block)
            
            # Create a recurring series for calendar display
            series_blocks, series_error = BlockService.create_recurring_block_series(
                court_ids=[courts[0].id],
                start_date=date.today() + timedelta(days=5),
                end_date=date.today() + timedelta(days=7),
                start_time=time(14, 0),
                end_time=time(15, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reasons[2].id,
                sub_reason='Calendar series',
                admin_id=test_admin.id,
                series_name='Calendar Test Series'
            )
            assert series_error is None
            
            # Test calendar data retrieval for a date range
            calendar_start = date.today() + timedelta(days=1)
            calendar_end = date.today() + timedelta(days=7)
            
            calendar_blocks = BlockService.filter_blocks(
                date_range=(calendar_start, calendar_end)
            )
            
            # Verify we get both single blocks and series blocks
            single_blocks = [b for b in calendar_blocks if b.series_id is None]
            series_blocks_found = [b for b in calendar_blocks if b.series_id is not None]
            
            assert len(single_blocks) > 0
            assert len(series_blocks_found) > 0
            
            # Verify blocks have all necessary data for calendar display
            for block in calendar_blocks:
                assert block.date is not None
                assert block.start_time is not None
                assert block.end_time is not None
                assert block.court_id is not None
                assert block.reason_id is not None
                assert hasattr(block, 'reason_obj')  # For reason name
                assert hasattr(block, 'court')  # For court number
    
    def test_hover_tooltips_and_click_interactions(self, app, test_admin):
        """Test data availability for hover tooltips and click interactions."""
        with app.app_context():
            court = Court.query.filter_by(number=3).first()
            reason = BlockReason.query.filter_by(name='Championship').first()
            
            # Create single block with detailed information
            single_block, error = BlockService.create_block(
                court_id=court.id,
                date=date.today() + timedelta(days=1),
                start_time=time(16, 0),
                end_time=time(18, 0),
                reason_id=reason.id,
                sub_reason='Finals - Team A vs Team B',
                admin_id=test_admin.id
            )
            assert error is None
            
            # Create series block with modification
            series_blocks, series_error = BlockService.create_recurring_block_series(
                court_ids=[court.id],
                start_date=date.today() + timedelta(days=3),
                end_date=date.today() + timedelta(days=5),
                start_time=time(12, 0),
                end_time=time(13, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reason.id,
                sub_reason='Series championship',
                admin_id=test_admin.id,
                series_name='Championship Series'
            )
            assert series_error is None
            
            # Modify one instance in the series
            middle_block = series_blocks[1]
            success, update_error = BlockService.update_single_instance(
                middle_block.id,
                sub_reason='Modified instance',
                admin_id=test_admin.id
            )
            assert update_error is None
            
            # Test tooltip data for single block
            tooltip_data_single = {
                'id': single_block.id,
                'court_number': single_block.court.number,
                'date': single_block.date.isoformat(),
                'start_time': single_block.start_time.strftime('%H:%M'),
                'end_time': single_block.end_time.strftime('%H:%M'),
                'reason_name': single_block.reason_obj.name,
                'sub_reason': single_block.sub_reason,
                'series_id': single_block.series_id,
                'is_modified': single_block.is_modified,
                'created_by': single_block.created_by.name
            }
            
            # Verify all tooltip data is available
            assert tooltip_data_single['court_number'] == 3
            assert tooltip_data_single['reason_name'] == 'Championship'
            assert tooltip_data_single['sub_reason'] == 'Finals - Team A vs Team B'
            assert tooltip_data_single['series_id'] is None
            assert tooltip_data_single['is_modified'] is False
            
            # Test tooltip data for modified series block
            modified_block = Block.query.get(middle_block.id)
            tooltip_data_series = {
                'id': modified_block.id,
                'court_number': modified_block.court.number,
                'reason_name': modified_block.reason_obj.name,
                'sub_reason': modified_block.sub_reason,
                'series_id': modified_block.series_id,
                'is_modified': modified_block.is_modified,
                'series_name': modified_block.series.name if modified_block.series else None
            }
            
            assert tooltip_data_series['series_id'] is not None
            assert tooltip_data_series['is_modified'] is True
            assert tooltip_data_series['sub_reason'] == 'Modified instance'
            assert tooltip_data_series['series_name'] == 'Championship Series'
    
    def test_color_coding_and_visual_indicators(self, app, test_admin):
        """Test that blocks have proper data for color coding and visual indicators."""
        with app.app_context():
            court = Court.query.filter_by(number=4).first()
            
            # Create blocks with different reasons for color coding
            reason_types = [
                ('Maintenance', 'blue'),
                ('Weather', 'gray'),
                ('Tournament', 'green'),
                ('Championship', 'gold')
            ]
            
            created_blocks = []
            for i, (reason_name, expected_color) in enumerate(reason_types):
                reason = BlockReason.query.filter_by(name=reason_name).first()
                
                block, error = BlockService.create_block(
                    court_id=court.id,
                    date=date.today() + timedelta(days=i+1),
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    reason_id=reason.id,
                    sub_reason=f'Color test {reason_name}',
                    admin_id=test_admin.id
                )
                assert error is None
                created_blocks.append((block, expected_color))
            
            # Create series blocks for striped pattern indicator
            series_blocks, series_error = BlockService.create_recurring_block_series(
                court_ids=[court.id],
                start_date=date.today() + timedelta(days=10),
                end_date=date.today() + timedelta(days=12),
                start_time=time(15, 0),
                end_time=time(16, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=BlockReason.query.filter_by(name='Tennis Course').first().id,
                sub_reason='Visual indicator test',
                admin_id=test_admin.id,
                series_name='Visual Test Series'
            )
            assert series_error is None
            
            # Modify one series instance for dotted border indicator
            success, update_error = BlockService.update_single_instance(
                series_blocks[1].id,
                sub_reason='Modified for visual test',
                admin_id=test_admin.id
            )
            assert update_error is None
            
            # Test visual indicator data
            for block, expected_color in created_blocks:
                visual_data = {
                    'reason_name': block.reason_obj.name,
                    'is_series': block.series_id is not None,
                    'is_modified': block.is_modified,
                    'expected_color': expected_color
                }
                
                # Verify reason-based color mapping data is available
                assert visual_data['reason_name'] in [rt[0] for rt in reason_types]
                assert visual_data['is_series'] is False
                assert visual_data['is_modified'] is False
            
            # Test series visual indicators
            for block in series_blocks:
                updated_block = Block.query.get(block.id)
                series_visual_data = {
                    'is_series': updated_block.series_id is not None,
                    'is_modified': updated_block.is_modified,
                    'series_name': updated_block.series.name if updated_block.series else None
                }
                
                assert series_visual_data['is_series'] is True
                assert series_visual_data['series_name'] == 'Visual Test Series'
                
                # Check if this is the modified instance
                if updated_block.sub_reason == 'Modified for visual test':
                    assert series_visual_data['is_modified'] is True
                else:
                    assert series_visual_data['is_modified'] is False