"""Property-based tests for block service."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from datetime import date, time, timedelta
import calendar
from app.models import Member, Court, Reservation, Block, BlockReason, BlockSeries
from app.services.block_service import BlockService
from app.services.block_reason_service import BlockReasonService
from app.services.reservation_service import ReservationService
from app import db


# Hypothesis strategies for generating test data
court_numbers = st.integers(min_value=1, max_value=6)
booking_times = st.times(min_value=time(6, 0), max_value=time(21, 0))
future_dates = st.dates(min_value=date.today(), max_value=date.today() + timedelta(days=90))
block_reasons = st.sampled_from(['rain', 'maintenance', 'tournament', 'championship'])
recurrence_patterns = st.sampled_from(['daily', 'weekly', 'monthly'])


@given(court_num=court_numbers, booking_date=future_dates, start=booking_times, reason=block_reasons)
@pytest.mark.usefixtures("app")
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_14_blocks_cascade_cancel_existing_reservations(app, court_num, booking_date, start, reason):
    """Feature: tennis-club-reservation, Property 14: Blocks cascade-cancel existing reservations
    Validates: Requirements 5.2
    
    For any block created on a court with existing reservations in the blocked time period,
    those reservations should be automatically cancelled.
    """
    with app.app_context():
        # Get existing court (created by app fixture)

        court = Court.query.filter_by(number=court_num).first()

        assert court is not None, f"Court {court_num} should exist"
        
        # Create test members with unique emails
        import random
        import time
        unique_id = random.randint(100000, 999999)
        timestamp = int(time.time() * 1000000)  # microsecond timestamp for uniqueness
        member1 = Member(
            firstname="Test", 
            lastname="Member1",
            email=f"test1_{unique_id}_{timestamp}_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="member"
        )
        member1.set_password("password123")
        
        admin = Member(
            firstname="Admin", 
            lastname="User",
            email=f"admin_{unique_id}_{timestamp}_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="administrator"
        )
        admin.set_password("password123")
        
        db.session.add(member1)
        db.session.add(admin)
        db.session.commit()
        
        # Create a reservation that will conflict with the block
        reservation, error = ReservationService.create_reservation(
            court_id=court.id,
            date=booking_date,
            start_time=start,
            booked_for_id=member1.id,
            booked_by_id=member1.id
        )
        
        # Verify reservation was created successfully
        assert reservation is not None, f"Reservation creation failed: {error}"
        assert error is None
        assert reservation.status == 'active'
        
        reservation_id = reservation.id
        
        # Calculate end time for block (covers the reservation)
        end_time = time(start.hour + 1, start.minute)
        
        # Get or create block reason
        block_reason = BlockReason.query.filter_by(name='Maintenance').first()
        if not block_reason:
            block_reason = BlockReason(name='Maintenance', is_active=True, created_by_id=admin.id)
            db.session.add(block_reason)
            db.session.commit()
        
        # Create a block that covers the reservation time
        block, block_error = BlockService.create_block(
            court_id=court.id,
            date=booking_date,
            start_time=start,
            end_time=end_time,
            reason_id=block_reason.id,
            sub_reason=None,
            admin_id=admin.id
        )
        
        # Verify block was created successfully
        assert block is not None, f"Block creation failed: {block_error}"
        assert block_error is None
        
        # Verify the reservation was cancelled
        cancelled_reservation = Reservation.query.get(reservation_id)
        assert cancelled_reservation is not None, "Reservation should still exist in database"
        assert cancelled_reservation.status == 'cancelled', \
            f"Reservation status should be 'cancelled', but was '{cancelled_reservation.status}'"
        
        # Verify the cancellation reason includes the block reason
        assert cancelled_reservation.reason is not None, "Cancellation reason should be set"
        assert 'Platzsperre' in cancelled_reservation.reason, \
            f"Cancellation reason should mention 'Platzsperre', but was: {cancelled_reservation.reason}"
        
        # Cleanup
        db.session.delete(cancelled_reservation)
        db.session.delete(block)
        db.session.delete(member1)
        db.session.delete(admin)
        db.session.commit()



@given(court_num=court_numbers, booking_date=future_dates, start=booking_times, reason=block_reasons)
@pytest.mark.usefixtures("app")
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_15_block_cancellations_include_reason_in_notification(app, court_num, booking_date, start, reason):
    """Feature: tennis-club-reservation, Property 15: Block cancellations include reason in notification
    Validates: Requirements 5.3
    
    For any reservation cancelled due to a block, the email notifications sent to the booked_by
    and booked_for members should include the block reason.
    """
    with app.app_context():
        # Get existing court (created by app fixture)

        court = Court.query.filter_by(number=court_num).first()

        assert court is not None, f"Court {court_num} should exist"
        
        # Create test members with unique emails
        import random
        import time
        unique_id = random.randint(100000, 999999)
        timestamp = int(time.time() * 1000000)  # microsecond timestamp for uniqueness
        member1 = Member(
            firstname="Test", 
            lastname="Member1",
            email=f"test1_notif_{unique_id}_{timestamp}_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="member"
        )
        member1.set_password("password123")
        
        member2 = Member(
            firstname="Test", 
            lastname="Member2",
            email=f"test2_notif_{unique_id}_{timestamp}_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="member"
        )
        member2.set_password("password123")
        
        admin = Member(
            firstname="Admin", 
            lastname="User",
            email=f"admin_notif_{unique_id}_{timestamp}_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="administrator"
        )
        admin.set_password("password123")
        
        db.session.add(member1)
        db.session.add(member2)
        db.session.add(admin)
        db.session.commit()
        
        # Create a reservation with different booked_for and booked_by members
        reservation, error = ReservationService.create_reservation(
            court_id=court.id,
            date=booking_date,
            start_time=start,
            booked_for_id=member1.id,
            booked_by_id=member2.id
        )
        
        # Verify reservation was created successfully
        assert reservation is not None, f"Reservation creation failed: {error}"
        assert error is None
        assert reservation.status == 'active'
        
        reservation_id = reservation.id
        
        # Calculate end time for block (covers the reservation)
        end_time = time(start.hour + 1, start.minute)
        
        # Get or create block reason based on the test reason parameter
        reason_name_map = {
            'rain': 'Weather',
            'maintenance': 'Maintenance', 
            'tournament': 'Tournament',
            'championship': 'Championship'
        }
        reason_name = reason_name_map.get(reason, 'Maintenance')
        
        block_reason = BlockReason.query.filter_by(name=reason_name).first()
        if not block_reason:
            block_reason = BlockReason(name=reason_name, is_active=True, created_by_id=admin.id)
            db.session.add(block_reason)
            db.session.commit()
        
        # Create a block that covers the reservation time
        block, block_error = BlockService.create_block(
            court_id=court.id,
            date=booking_date,
            start_time=start,
            end_time=end_time,
            reason_id=block_reason.id,
            sub_reason=None,
            admin_id=admin.id
        )
        
        # Verify block was created successfully
        assert block is not None, f"Block creation failed: {block_error}"
        assert block_error is None
        
        # Verify the reservation was cancelled
        cancelled_reservation = Reservation.query.get(reservation_id)
        assert cancelled_reservation is not None, "Reservation should still exist in database"
        assert cancelled_reservation.status == 'cancelled'
        
        # Verify the cancellation reason includes the block reason
        assert cancelled_reservation.reason is not None, "Cancellation reason should be set"
        
        # Map the reason to German text (updated for new reason names)
        reason_map = {
            'Weather': 'Regen',
            'Maintenance': 'Wartung',
            'Tournament': 'Turnier',
            'Championship': 'Meisterschaft'
        }
        
        expected_reason_text = reason_map.get(reason_name, reason_name)
        
        # Verify the reason contains both "Platzsperre" and the specific reason
        assert 'Platzsperre' in cancelled_reservation.reason, \
            f"Cancellation reason should mention 'Platzsperre', but was: {cancelled_reservation.reason}"
        assert expected_reason_text in cancelled_reservation.reason, \
            f"Cancellation reason should include '{expected_reason_text}', but was: {cancelled_reservation.reason}"
        
        # Cleanup
        db.session.delete(cancelled_reservation)
        db.session.delete(block)
        db.session.delete(member1)
        db.session.delete(member2)
        db.session.delete(admin)
        db.session.commit()


@given(court_num=court_numbers, 
       start_date=future_dates, 
       end_date=future_dates,
       start_time=booking_times,
       recurrence_pattern=recurrence_patterns)
@pytest.mark.usefixtures("app")
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_48_recurring_block_series_generation(app, court_num, start_date, end_date, start_time, recurrence_pattern):
    """Feature: tennis-club-reservation, Property 48: Recurring block series generation
    Validates: Requirements 19.1
    
    For any valid recurring block parameters (start date, end date, recurrence pattern, time range),
    creating a recurring block series should generate the correct number of individual block instances
    with proper dates and times according to the recurrence pattern.
    """
    with app.app_context():
        # Ensure valid date range
        assume(end_date >= start_date)
        # Limit the date range to avoid too many blocks in tests
        assume((end_date - start_date).days <= 30)
        
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=court_num).first()
        assert court is not None, f"Court {court_num} should exist"
        
        # Create test admin with unique email
        import random
        import time as time_module
        unique_id = random.randint(100000, 999999)
        timestamp = int(time_module.time() * 1000000)
        admin = Member(
            firstname="Admin", 
            lastname="User",
            email=f"admin_series_{unique_id}_{timestamp}_{court_num}_{start_date}_{recurrence_pattern}@example.com", 
            role="administrator"
        )
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()
        
        # Get or create block reason
        block_reason = BlockReason.query.filter_by(name='Maintenance').first()
        if not block_reason:
            block_reason = BlockReason(name='Maintenance', is_active=True, created_by_id=admin.id)
            db.session.add(block_reason)
            db.session.commit()
        
        # Calculate end time (1 hour after start)
        end_time = time((start_time.hour + 1) % 24, start_time.minute)
        
        # Create recurring block series
        series_name = f"Test Series {recurrence_pattern}"
        recurrence_days = None
        if recurrence_pattern == 'weekly':
            # For weekly, use the day of week from start_date
            recurrence_days = [start_date.weekday()]
        
        blocks, error = BlockService.create_recurring_block_series(
            court_ids=[court.id],
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            recurrence_pattern=recurrence_pattern,
            recurrence_days=recurrence_days,
            reason_id=block_reason.id,
            sub_reason=None,
            admin_id=admin.id,
            series_name=series_name
        )
        
        # Verify series was created successfully
        assert error is None, f"Series creation failed: {error}"
        assert blocks is not None, "Blocks should not be None"
        assert len(blocks) > 0, "At least one block should be created"
        
        # Verify all blocks have the same series_id
        series_id = blocks[0].series_id
        assert series_id is not None, "Blocks should have a series_id"
        
        for block in blocks:
            assert block.series_id == series_id, "All blocks should have the same series_id"
            assert block.court_id == court.id, "All blocks should be for the correct court"
            assert block.start_time == start_time, "All blocks should have the correct start time"
            assert block.end_time == end_time, "All blocks should have the correct end time"
            assert block.reason_id == block_reason.id, "All blocks should have the correct reason"
            assert block.created_by_id == admin.id, "All blocks should be created by the admin"
        
        # Verify the BlockSeries record was created
        series = BlockSeries.query.get(series_id)
        assert series is not None, "BlockSeries record should exist"
        assert series.name == series_name, "Series should have the correct name"
        assert series.start_date == start_date, "Series should have the correct start date"
        assert series.end_date == end_date, "Series should have the correct end date"
        assert series.start_time == start_time, "Series should have the correct start time"
        assert series.end_time == end_time, "Series should have the correct end time"
        assert series.recurrence_pattern == recurrence_pattern, "Series should have the correct recurrence pattern"
        assert series.reason_id == block_reason.id, "Series should have the correct reason"
        assert series.created_by_id == admin.id, "Series should be created by the admin"
        
        if recurrence_pattern == 'weekly':
            assert series.recurrence_days == recurrence_days, "Weekly series should have correct recurrence days"
        
        # Calculate expected number of blocks based on recurrence pattern
        expected_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            if recurrence_pattern == 'daily':
                expected_count += 1
                current_date += timedelta(days=1)
            elif recurrence_pattern == 'weekly':
                if current_date.weekday() in recurrence_days:
                    expected_count += 1
                current_date += timedelta(days=1)
            elif recurrence_pattern == 'monthly':
                expected_count += 1
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
        
        # Verify the correct number of blocks were created
        assert len(blocks) == expected_count, \
            f"Expected {expected_count} blocks for {recurrence_pattern} pattern, but got {len(blocks)}"
        
        # Verify block dates follow the recurrence pattern
        block_dates = sorted([block.date for block in blocks])
        
        if recurrence_pattern == 'daily':
            # For daily, each date should be consecutive
            for i in range(1, len(block_dates)):
                assert (block_dates[i] - block_dates[i-1]).days == 1, \
                    "Daily blocks should be on consecutive days"
        
        elif recurrence_pattern == 'weekly':
            # For weekly, blocks should be on the correct day of week
            for block_date in block_dates:
                assert block_date.weekday() in recurrence_days, \
                    f"Weekly block on {block_date} should be on day {recurrence_days}"
        
        elif recurrence_pattern == 'monthly':
            # For monthly, blocks should be on the same day of month (when possible)
            target_day = start_date.day
            for block_date in block_dates:
                # Allow for month-end adjustments (e.g., Jan 31 -> Feb 28)
                assert block_date.day <= target_day + 3, \
                    f"Monthly block day {block_date.day} should be close to target day {target_day}"
        
        # Cleanup
        for block in blocks:
            db.session.delete(block)
        db.session.delete(series)
        db.session.delete(admin)
        db.session.commit()


def test_block_reason_service_basic_functionality(app):
    """Test basic BlockReasonService functionality."""
    with app.app_context():
        # Create test admin
        admin = Member(
            firstname='Test',
            lastname='Admin',
            email='test_admin_reason@example.com',
            role='administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # Test create_block_reason
        reason, error = BlockReasonService.create_block_reason('Test Reason', admin.id)
        assert error is None, f"Error creating reason: {error}"
        assert reason is not None
        assert reason.name == 'Test Reason'
        assert reason.is_active is True
        
        # Test get_all_block_reasons
        reasons = BlockReasonService.get_all_block_reasons()
        reason_names = [r.name for r in reasons]
        assert 'Test Reason' in reason_names
        
        # Test update_block_reason
        success, error = BlockReasonService.update_block_reason(reason.id, 'Updated Reason', admin.id)
        assert error is None, f"Error updating reason: {error}"
        assert success is True
        
        # Verify update
        updated_reason = BlockReason.query.get(reason.id)
        assert updated_reason.name == 'Updated Reason'
        
        # Test create_sub_reason_template
        template, error = BlockReasonService.create_sub_reason_template(reason.id, 'Test Template', admin.id)
        assert error is None, f"Error creating template: {error}"
        assert template is not None
        assert template.template_name == 'Test Template'
        
        # Test get_sub_reason_templates
        templates = BlockReasonService.get_sub_reason_templates(reason.id)
        assert len(templates) == 1
        assert templates[0].template_name == 'Test Template'
        
        # Test delete_sub_reason_template
        success, error = BlockReasonService.delete_sub_reason_template(template.id, admin.id)
        assert error is None, f"Error deleting template: {error}"
        assert success is True
        
        # Test delete_block_reason (unused reason)
        success, error = BlockReasonService.delete_block_reason(reason.id, admin.id)
        assert error is None, f"Error deleting reason: {error}"
        assert success is True
        
        # Cleanup
        db.session.delete(admin)
        db.session.commit()