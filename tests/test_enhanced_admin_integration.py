"""Integration tests for enhanced admin panel functionality (trimmed after series removal)."""
from datetime import date, time, timedelta
from app.models import Court, Block, BlockReason
from app.services.block_service import BlockService
from app.services.block_reason_service import BlockReasonService


class TestReasonManagement:
    """Test custom reason creation, editing, and management."""
    
    def test_custom_reason_creation_and_editing(self, app, test_admin):
        """Test creating and editing custom block reasons."""
        with app.app_context():
            reason, error = BlockReasonService.create_block_reason(
                'Custom Event', test_admin.id
            )
            assert error is None
            assert reason is not None
            assert reason.name == 'Custom Event'
            assert reason.is_active is True
            assert reason.created_by_id == test_admin.id
            
            success, error = BlockReasonService.update_block_reason(
                reason.id, 'Updated Custom Event', test_admin.id
            )
            assert error is None
            assert success is True
            
            updated_reason = BlockReason.query.get(reason.id)
            assert updated_reason.name == 'Updated Custom Event'
    
    def test_reason_deletion_with_usage_checking(self, app, test_admin):
        """Test reason deletion with usage checking."""
        with app.app_context():
            court = Court.query.filter_by(number=1).first()
            reason, error = BlockReasonService.create_block_reason(
                'Temporary Event', test_admin.id
            )
            assert error is None
            
            blocks, block_error = BlockService.create_multi_court_blocks(
                court_ids=[court.id],
                date=date.today() + timedelta(days=1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                reason_id=reason.id,
                details='Test usage',
                admin_id=test_admin.id
            )
            assert block_error is None
            block = blocks[0]
            
            success, message = BlockReasonService.delete_block_reason(
                reason.id, test_admin.id
            )
            assert success is True
            assert message is not None
            assert 'deaktiviert' in message
            
            deactivated_reason = BlockReason.query.get(reason.id)
            assert deactivated_reason is not None
            assert deactivated_reason.is_active is False
            
            existing_block = Block.query.get(block.id)
            assert existing_block is not None
            assert existing_block.reason_id == reason.id
    
    def test_historical_preservation_of_reason_data(self, app, test_admin):
        """Historical block data is preserved when reasons are edited/deleted."""
        with app.app_context():
            court = Court.query.filter_by(number=2).first()
            reason, error = BlockReasonService.create_block_reason(
                'Historical Test', test_admin.id
            )
            assert error is None
            
            past_blocks, block_error = BlockService.create_multi_court_blocks(
                court_ids=[court.id],
                date=date.today() - timedelta(days=1),
                start_time=time(9, 0),
                end_time=time(10, 0),
                reason_id=reason.id,
                details='Historical block',
                admin_id=test_admin.id
            )
            assert block_error is None
            past_block = past_blocks[0]

            future_blocks, future_error = BlockService.create_multi_court_blocks(
                court_ids=[court.id],
                date=date.today() + timedelta(days=1),
                start_time=time(9, 0),
                end_time=time(10, 0),
                reason_id=reason.id,
                details='Future block',
                admin_id=test_admin.id
            )
            assert future_error is None
            future_block = future_blocks[0]

            success, _ = BlockReasonService.delete_block_reason(
                reason.id, test_admin.id
            )
            assert success is True
            
            historical_block = Block.query.get(past_block.id)
            assert historical_block is not None
            assert historical_block.reason_id == reason.id
            
            deleted_future_block = Block.query.get(future_block.id)
            assert deleted_future_block is None
    
    def test_reason_usage_count_tracking(self, app, test_admin):
        """Usage count tracking for reasons."""
        with app.app_context():
            courts = Court.query.filter(Court.number.in_([1, 2, 3])).all()
            reason, error = BlockReasonService.create_block_reason(
                'Usage Test', test_admin.id
            )
            assert error is None
            
            usage_count = BlockReasonService.get_reason_usage_count(reason.id)
            assert usage_count == 0
            
            for i, court in enumerate(courts):
                blocks, block_error = BlockService.create_multi_court_blocks(
                    court_ids=[court.id],
                    date=date.today() + timedelta(days=i + 1),
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    reason_id=reason.id,
                    details=f'Usage test {i + 1}',
                    admin_id=test_admin.id
                )
                assert block_error is None
                block = blocks[0]

            usage_count = BlockReasonService.get_reason_usage_count(reason.id)
            assert usage_count == len(courts)
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
                assert block.id is None
    
    def test_search_functionality(self, app, test_admin):
        """Test search functionality in block reasons and details."""
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
            
            # Create blocks with searchable details
            details_list = ['Team Alpha vs Beta', 'Court Resurfacing', 'Finals Tournament']
            
            for i, (reason, details) in enumerate(zip(created_reasons, details_list)):
                block_list, error = BlockService.create_multi_court_blocks(
                    court_ids=[court.id],
                    date=date.today() + timedelta(days=i+1),
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    reason_id=reason.id,
                    details=details,
                    admin_id=test_admin.id
                )
                assert error is None
                block = block_list[0]

            # Test filtering by reason name (simulated search)
            maintenance_reason = next(r for r in created_reasons if 'Maintenance' in r.name)
            maintenance_blocks = BlockService.filter_blocks(reason_ids=[maintenance_reason.id])
            
            assert len(maintenance_blocks) == 1
            assert 'Resurfacing' in maintenance_blocks[0].details
    
    def test_filter_persistence(self, app, test_admin):
        """Test that filters work consistently across multiple queries."""
        with app.app_context():
            courts = Court.query.filter(Court.number.in_([4, 5])).all()
            reason = BlockReason.query.filter_by(name='Weather').first()
            
            # Create consistent test data
            test_date_range = (date.today() + timedelta(days=1), date.today() + timedelta(days=3))
            
            for court in courts:
                for day_offset in range(1, 4):  # Days 1, 2, 3
                    block_list, error = BlockService.create_multi_court_blocks(
                        court_ids=[court.id],
                        date=date.today() + timedelta(days=day_offset),
                        start_time=time(12, 0),
                        end_time=time(13, 0),
                        reason_id=reason.id,
                        details='Consistent test',
                        admin_id=test_admin.id
                    )
                    assert error is None
                    block = block_list[0]

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
            block_list, error = BlockService.create_multi_court_blocks(
                court_ids=[court.id],
                date=date.today() + timedelta(days=1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                reason_id=reason.id,
                details='Audit test',
                admin_id=test_admin.id
            )
            assert error is None
            block = block_list[0]

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
                details='Updated audit test',
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
                block_list, error = BlockService.create_multi_court_blocks(
                    court_ids=[court.id],
                    date=date.today() + timedelta(days=i+1),
                    start_time=time(11, 0),
                    end_time=time(12, 0),
                    reason_id=reason.id,
                    details=f'Audit filter test {i+1}',
                    admin_id=test_admin.id
                )
                assert error is None
                block = block_list[0]
                operations_data.append(('create', block.id))
                
                # Update each block
                success, update_error = BlockService.update_single_instance(
                    block.id,
                    details=f'Updated audit filter test {i+1}',
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
                details='Audit data test',
                admin_id=test_admin.id,
                name='Audit Test '
            )
            
            assert error is None
            id = blocks[0].id
            
            # Find the audit log for this series creation
            create_logs = BlockService.get_audit_log({'operation': 'create'})
            log = next(
                (log for log in create_logs 
                 if log.id == id and log.admin_id == test_admin.id),
                None
            )
            
            assert log is not None
            assert log.operation_data is not None
            
            # Verify operation data contains expected fields
            op_data = log.operation_data
            assert 'id' in op_data
            assert 'name' in op_data
            assert 'court_ids' in op_data
            assert 'recurrence_pattern' in op_data
            assert 'blocks_created' in op_data
            
            assert op_data['id'] == id
            assert op_data['name'] == 'Audit Test '
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
                    block_list, error = BlockService.create_multi_court_blocks(
                        court_ids=[court.id],
                        date=date.today() + timedelta(days=day_offset),
                        start_time=time(10 + i, 0),  # Different times
                        end_time=time(11 + i, 0),
                        reason_id=reason.id,
                        details=f'Calendar test {i+1}',
                        admin_id=test_admin.id
                    )
                    assert error is None
                    block = block_list[0]
                    test_blocks.append(block)

            # Create a recurring series for calendar display
                court_ids=[courts[0].id],
                start_date=date.today() + timedelta(days=5),
                end_date=date.today() + timedelta(days=7),
                start_time=time(14, 0),
                end_time=time(15, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reasons[2].id,
                details='Calendar series',
                admin_id=test_admin.id,
                name='Calendar Test '
            )
            assert error is None
            
            # Test calendar data retrieval for a date range
            calendar_start = date.today() + timedelta(days=1)
            calendar_end = date.today() + timedelta(days=7)
            
            calendar_blocks = BlockService.filter_blocks(
                date_range=(calendar_start, calendar_end)
            )
            
            # Verify we get both single blocks and series blocks
            single_blocks = [b for b in calendar_blocks if b.id is None]
            
            assert len(single_blocks) > 0
            assert len(
            
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
            single_blocks, error = BlockService.create_multi_court_blocks(
                court_ids=[court.id],
                date=date.today() + timedelta(days=1),
                start_time=time(16, 0),
                end_time=time(18, 0),
                reason_id=reason.id,
                details='Finals - Team A vs Team B',
                admin_id=test_admin.id
            )
            assert error is None
            single_block = single_blocks[0]

            # Create series block with modification
                court_ids=[court.id],
                start_date=date.today() + timedelta(days=3),
                end_date=date.today() + timedelta(days=5),
                start_time=time(12, 0),
                end_time=time(13, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=reason.id,
                details=' championship',
                admin_id=test_admin.id,
                name='Championship '
            )
            assert error is None
            
            # Modify one instance in the series
            middle_block =
            success, update_error = BlockService.update_single_instance(
                middle_block.id,
                details='Modified instance',
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
                'details': single_block.details,
                'id': single_block.id,
                'is_modified': single_block.is_modified,
                'created_by': single_block.created_by.name
            }
            
            # Verify all tooltip data is available
            assert tooltip_data_single['court_number'] == 3
            assert tooltip_data_single['reason_name'] == 'Championship'
            assert tooltip_data_single['details'] == 'Finals - Team A vs Team B'
            assert tooltip_data_single['id'] is None
            assert tooltip_data_single['is_modified'] is False
            
            # Test tooltip data for modified series block
            modified_block = Block.query.get(middle_block.id)
            tooltip_data_series = {
                'id': modified_block.id,
                'court_number': modified_block.court.number,
                'reason_name': modified_block.reason_obj.name,
                'details': modified_block.details,
                'id': modified_block.id,
                'is_modified': modified_block.is_modified,
                'name': modified_block.series.name if modified_block.series else None
            }
            
            assert tooltip_data_series['id'] is not None
            assert tooltip_data_series['is_modified'] is True
            assert tooltip_data_series['details'] == 'Modified instance'
            assert tooltip_data_series['name'] == 'Championship '
    
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

                block_list, error = BlockService.create_multi_court_blocks(
                    court_ids=[court.id],
                    date=date.today() + timedelta(days=i+1),
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    reason_id=reason.id,
                    details=f'Color test {reason_name}',
                    admin_id=test_admin.id
                )
                assert error is None
                block = block_list[0]
                created_blocks.append((block, expected_color))
            
            # Create series blocks for striped pattern indicator
                court_ids=[court.id],
                start_date=date.today() + timedelta(days=10),
                end_date=date.today() + timedelta(days=12),
                start_time=time(15, 0),
                end_time=time(16, 0),
                recurrence_pattern='daily',
                recurrence_days=None,
                reason_id=BlockReason.query.filter_by(name='Tennis Course').first().id,
                details='Visual indicator test',
                admin_id=test_admin.id,
                name='Visual Test '
            )
            assert error is None
            
            # Modify one series instance for dotted border indicator
            success, update_error = BlockService.update_single_instance(
                details='Modified for visual test',
                admin_id=test_admin.id
            )
            assert update_error is None
            
            # Test visual indicator data
            for block, expected_color in created_blocks:
                visual_data = {
                    'reason_name': block.reason_obj.name,
                    'is_series': block.id is not None,
                    'is_modified': block.is_modified,
                    'expected_color': expected_color
                }
                
                # Verify reason-based color mapping data is available
                assert visual_data['reason_name'] in [rt[0] for rt in reason_types]
                assert visual_data['is_series'] is False
                assert visual_data['is_modified'] is False
            
            # Test series visual indicators
            for block in
                updated_block = Block.query.get(block.id)
                visual_data = {
                    'is_series': updated_block.id is not None,
                    'is_modified': updated_block.is_modified,
                    'name': updated_block.series.name if updated_block.series else None
                }
                
                assert visual_data['is_series'] is True
                assert visual_data['name'] == 'Visual Test '
                
                # Check if this is the modified instance
                if updated_block.details == 'Modified for visual test':
                    assert visual_data['is_modified'] is True
                else:
                    assert visual_data['is_modified'] is False
