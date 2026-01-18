"""Property-based tests for reservation service."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, time, timedelta
from app.models import Member, Court, Reservation
from app.services.reservation_service import ReservationService
from app import db


# Hypothesis strategies for generating test data
court_numbers = st.integers(min_value=1, max_value=6)
# Only generate full hour times (no minutes or seconds)
booking_times = st.sampled_from([time(h, 0) for h in range(6, 22)])  # 6:00 to 21:00, full hours only
future_dates = st.dates(min_value=date.today(), max_value=date.today() + timedelta(days=90))


@given(court_num=court_numbers, booking_date=future_dates, start=booking_times)
@pytest.mark.usefixtures("app")
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_33_one_hour_duration_enforcement(app, court_num, booking_date, start):
    """Feature: tennis-club-reservation, Property 33: One-hour duration enforcement
    Validates: Requirements 14.2
    
    For any reservation created, the duration (end_time - start_time) should equal exactly one hour.
    """
    with app.app_context():
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=court_num).first()
        assert court is not None, f"Court {court_num} should exist"
        
        # Create test members with unique emails
        import random
        import time as time_module
        unique_id = random.randint(100000, 999999)
        timestamp = int(time_module.time() * 1000000)  # microsecond precision
        member1 = Member(
            firstname="Test", 
            lastname="Member1",
            email=f"test1_{unique_id}_{timestamp}_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="member"
        )
        member1.set_password("password123")
        member2 = Member(
            firstname="Test", 
            lastname="Member2",
            email=f"test2_{unique_id}_{timestamp}_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="member"
        )
        member2.set_password("password123")
        db.session.add(member1)
        db.session.add(member2)
        db.session.commit()
        
        # Create reservation using the service with a fixed current_time to ensure validity
        # Use a time early in the day to ensure all generated booking times are in the future
        from datetime import datetime
        fixed_current_time = datetime.combine(booking_date, time(6, 0))  # 6:00 AM on the booking date
        
        reservation, error, _ = ReservationService.create_reservation(
            court_id=court.id,
            date=booking_date,
            start_time=start,
            booked_for_id=member1.id,
            booked_by_id=member2.id,
            current_time=fixed_current_time
        )
        
        # Verify reservation was created successfully
        assert reservation is not None, f"Reservation creation failed: {error}"
        assert error is None
        
        # Calculate duration in hours
        start_minutes = start.hour * 60 + start.minute
        end_minutes = reservation.end_time.hour * 60 + reservation.end_time.minute
        duration_minutes = end_minutes - start_minutes
        duration_hours = duration_minutes / 60.0
        
        # Verify duration is exactly 1 hour
        assert duration_hours == 1.0, \
            f"Duration should be exactly 1 hour, but was {duration_hours} hours " \
            f"(start: {start}, end: {reservation.end_time})"
        
        # Also verify end_time is exactly 1 hour after start_time
        expected_end = time(start.hour + 1, start.minute)
        assert reservation.end_time == expected_end, \
            f"End time should be {expected_end}, but was {reservation.end_time}"
        
        # Cleanup (don't delete court - it's shared)
        db.session.delete(reservation)
        db.session.delete(member1)
        db.session.delete(member2)
        db.session.commit()


def test_book_cancel_rebook_same_slot(app):
    """Test that a cancelled reservation allows rebooking the same slot.
    
    This test verifies that:
    1. A reservation can be created
    2. The reservation can be cancelled
    3. The same slot can be booked again after cancellation
    
    This ensures the unique constraint doesn't block rebooking cancelled slots.
    """
    with app.app_context():
        # Setup: Get or create court
        court = Court.query.filter_by(number=1).first()
        if not court:
            court = Court(number=1)
            db.session.add(court)
            db.session.commit()
        
        # Create unique member for this test
        import random
        unique_id = random.randint(10000, 99999)
        member = Member(
            firstname="Test",
            lastname=f"Member{unique_id}",
            email=f"test_rebook_{unique_id}@example.com",
            role="member"
        )
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        
        # Test data
        test_date = date.today() + timedelta(days=1)
        test_time = time(10, 0)
        
        # Step 1: Create initial reservation
        reservation1, error1, _ = ReservationService.create_reservation(
            court_id=court.id,
            date=test_date,
            start_time=test_time,
            booked_for_id=member.id,
            booked_by_id=member.id
        )
        
        assert reservation1 is not None, f"First booking failed: {error1}"
        assert error1 is None
        assert reservation1.status == 'active'
        reservation1_id = reservation1.id
        
        # Step 2: Cancel the reservation
        success, error2 = ReservationService.cancel_reservation(
            reservation_id=reservation1_id,
            reason="Test cancellation"
        )
        
        assert success is True, f"Cancellation failed: {error2}"
        assert error2 is None
        
        # Verify cancellation
        cancelled_res = Reservation.query.get(reservation1_id)
        assert cancelled_res is not None
        assert cancelled_res.status == 'cancelled'
        assert cancelled_res.reason == "Test cancellation"
        
        # Step 3: Book the same slot again
        reservation2, error3, _ = ReservationService.create_reservation(
            court_id=court.id,
            date=test_date,
            start_time=test_time,
            booked_for_id=member.id,
            booked_by_id=member.id
        )
        
        assert reservation2 is not None, f"Rebooking failed: {error3}"
        assert error3 is None
        assert reservation2.status == 'active'
        assert reservation2.id != reservation1_id  # Should be a new reservation
        
        # Verify both reservations exist in database
        all_reservations = Reservation.query.filter_by(
            court_id=court.id,
            date=test_date,
            start_time=test_time
        ).all()
        
        assert len(all_reservations) == 2, "Should have 2 reservations (1 cancelled, 1 active)"
        
        statuses = [r.status for r in all_reservations]
        assert 'cancelled' in statuses
        assert 'active' in statuses
        
        # Cleanup
        for res in all_reservations:
            db.session.delete(res)
        db.session.delete(member)
        db.session.commit()
