"""Property-based tests for reservation service."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, time, timedelta
from app.models import Member, Court, Reservation
from app.services.reservation_service import ReservationService
from app import db


# Hypothesis strategies for generating test data
court_numbers = st.integers(min_value=1, max_value=6)
booking_times = st.times(min_value=time(6, 0), max_value=time(20, 0))
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
        member2 = Member(
            name="Test Member 2", 
            email=f"test2_{court_num}_{booking_date}_{start.hour}_{start.minute}@example.com", 
            role="member"
        )
        member2.set_password("password123")
        db.session.add(member1)
        db.session.add(member2)
        db.session.commit()
        
        # Create reservation using the service
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
        
        # Cleanup
        db.session.delete(reservation)
        db.session.delete(member1)
        db.session.delete(member2)
        db.session.delete(court)
        db.session.commit()
