"""Property-based tests for block service."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, time, timedelta
from app.models import Member, Court, Reservation, Block
from app.services.block_service import BlockService
from app.services.reservation_service import ReservationService
from app import db


# Hypothesis strategies for generating test data
court_numbers = st.integers(min_value=1, max_value=6)
booking_times = st.times(min_value=time(6, 0), max_value=time(20, 0))
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
        # Create test court
        court = Court(number=court_num)
        db.session.add(court)
        db.session.commit()
        
        # Create test members
        member1 = Member(
            name="Test Member 1", 
            email=f"test1_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="member"
        )
        member1.set_password("password123")
        
        admin = Member(
            name="Admin", 
            email=f"admin_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
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
        
        # Create a block that covers the reservation time
        block, block_error = BlockService.create_block(
            court_id=court.id,
            date=booking_date,
            start_time=start,
            end_time=end_time,
            reason=reason,
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
        db.session.delete(court)
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
        # Create test court
        court = Court(number=court_num)
        db.session.add(court)
        db.session.commit()
        
        # Create test members
        member1 = Member(
            name="Test Member 1", 
            email=f"test1_notif_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="member"
        )
        member1.set_password("password123")
        
        member2 = Member(
            name="Test Member 2", 
            email=f"test2_notif_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="member"
        )
        member2.set_password("password123")
        
        admin = Member(
            name="Admin", 
            email=f"admin_notif_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
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
        
        # Create a block that covers the reservation time
        block, block_error = BlockService.create_block(
            court_id=court.id,
            date=booking_date,
            start_time=start,
            end_time=end_time,
            reason=reason,
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
        
        # Map the reason to German text
        reason_map = {
            'rain': 'Regen',
            'maintenance': 'Wartung',
            'tournament': 'Turnier',
            'championship': 'Meisterschaft'
        }
        
        expected_reason_text = reason_map.get(reason, reason)
        
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
        db.session.delete(court)
        db.session.commit()
