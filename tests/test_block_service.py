"""Property-based tests for block service."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, time, timedelta
from app.models import Member, Court, Reservation, Block, BlockReason
from app.services.block_service import BlockService
from app.services.block_reason_service import BlockReasonService
from app.services.reservation_service import ReservationService
from app import db


# Hypothesis strategies for generating test data
court_numbers = st.integers(min_value=1, max_value=6)
booking_times = st.times(min_value=time(6, 0), max_value=time(21, 0))
future_dates = st.dates(min_value=date.today(), max_value=date.today() + timedelta(days=90))
block_reasons = st.sampled_from(['rain', 'maintenance', 'tournament', 'championship'])


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
            details=None,
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
            details=None,
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
        # Test delete_block_reason (unused reason)
        success, error = BlockReasonService.delete_block_reason(reason.id, admin.id)
        assert error is None, f"Error deleting reason: {error}"
        assert success is True
        
        # Cleanup
        db.session.delete(admin)
        db.session.commit()
