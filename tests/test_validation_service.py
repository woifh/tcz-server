"""Property-based tests for validation service."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import time
from app.services.validation_service import ValidationService


# Hypothesis strategies
# Generate only full-hour times (minutes and seconds must be 0)
valid_booking_times = st.builds(time, hour=st.integers(min_value=6, max_value=21), minute=st.just(0), second=st.just(0))
invalid_early_times = st.times(min_value=time(0, 0), max_value=time(5, 59))
invalid_late_times = st.times(min_value=time(22, 0), max_value=time(23, 59))


@given(start_time=valid_booking_times)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_32_time_slot_validation_accepts_valid_times(app, start_time):
    """Feature: tennis-club-reservation, Property 32: Time slot validation
    Validates: Requirements 14.1, 14.3
    
    For any reservation attempt, the system should accept start times between 
    06:00 and 20:00 (inclusive).
    """
    with app.app_context():
        result = ValidationService.validate_booking_time(start_time)
        assert result is True, f"Valid time {start_time} should be accepted"


@given(start_time=invalid_early_times)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_32_time_slot_validation_rejects_early_times(app, start_time):
    """Feature: tennis-club-reservation, Property 32: Time slot validation
    Validates: Requirements 14.1, 14.3
    
    For any reservation attempt, the system should reject start times before 06:00.
    """
    with app.app_context():
        result = ValidationService.validate_booking_time(start_time)
        assert result is False, f"Early time {start_time} should be rejected"


@given(start_time=invalid_late_times)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_32_time_slot_validation_rejects_late_times(app, start_time):
    """Feature: tennis-club-reservation, Property 32: Time slot validation
    Validates: Requirements 14.1, 14.3
    
    For any reservation attempt, the system should reject start times at or after 21:00.
    """
    with app.app_context():
        result = ValidationService.validate_booking_time(start_time)
        assert result is False, f"Late time {start_time} should be rejected"


@given(start_time=st.builds(time, 
                           hour=st.integers(min_value=6, max_value=21), 
                           minute=st.integers(min_value=1, max_value=59), 
                           second=st.integers(min_value=0, max_value=59)))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_32_time_slot_validation_rejects_non_full_hour_times(app, start_time):
    """Feature: tennis-club-reservation, Property 32: Time slot validation
    Validates: Requirements 14.1, 14.3
    
    For any reservation attempt, the system should reject start times that are not on full hours.
    """
    with app.app_context():
        result = ValidationService.validate_booking_time(start_time)
        assert result is False, f"Non-full-hour time {start_time} should be rejected"



from datetime import date, timedelta
from app.models import Member, Court, Reservation
from app import db
import random


@given(st.integers(min_value=0, max_value=1))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_2_two_reservation_limit_allows_under_limit(app, existing_reservations):
    """Feature: tennis-club-reservation, Property 2: Two-reservation limit enforcement
    Validates: Requirements 1.3, 11.3
    
    For any member with fewer than 2 active reservations, creating a new reservation should succeed.
    """
    with app.app_context():
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=1).first()
        assert court is not None, "Court 1 should exist"
        
        # Create test member with unique email
        unique_id = random.randint(100000, 999999)
        member = Member(firstname="Test", lastname="Member", email=f"test_{unique_id}_{existing_reservations}@example.com", role="member")
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        
        # Create existing reservations
        for i in range(existing_reservations):
            reservation = Reservation(
                court_id=court.id,
                date=date.today() + timedelta(days=i+1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                booked_for_id=member.id,
                booked_by_id=member.id,
                status='active'
            )
            db.session.add(reservation)
        db.session.commit()
        
        # Validate member can make another reservation
        result = ValidationService.validate_member_reservation_limit(member.id)
        assert result is True, f"Member with {existing_reservations} reservations should be allowed to book"
        
        # Cleanup
        Reservation.query.filter_by(booked_for_id=member.id).delete()
        db.session.delete(member)
        db.session.commit()


@given(st.just(2))
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_2_two_reservation_limit_blocks_at_limit(app, _):
    """Feature: tennis-club-reservation, Property 2: Two-reservation limit enforcement
    Validates: Requirements 1.3, 11.3
    
    For any member with 2 active reservations, creating a new reservation should be rejected.
    """
    with app.app_context():
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=1).first()
        assert court is not None, "Court 1 should exist"
        
        # Create test member with unique email
        unique_id = random.randint(100000, 999999)
        member = Member(firstname="Test", lastname="Member", email=f"test_limit_{unique_id}@example.com", role="member")
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        
        # Create 2 active reservations (at the limit)
        for i in range(2):
            reservation = Reservation(
                court_id=court.id,
                date=date.today() + timedelta(days=i+1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                booked_for_id=member.id,
                booked_by_id=member.id,
                status='active'
            )
            db.session.add(reservation)
        db.session.commit()
        
        # Validate member cannot make another reservation
        result = ValidationService.validate_member_reservation_limit(member.id)
        assert result is False, "Member with 2 reservations should not be allowed to book"
        
        # Cleanup
        Reservation.query.filter_by(booked_for_id=member.id).delete()
        db.session.delete(member)
        db.session.commit()



court_numbers = st.integers(min_value=1, max_value=6)
future_dates = st.dates(min_value=date.today(), max_value=date.today() + timedelta(days=90))
booking_times = st.times(min_value=time(6, 0), max_value=time(21, 0))


@given(court_num=court_numbers, booking_date=future_dates, start=booking_times)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_27_reservation_conflicts_rejected(app, court_num, booking_date, start):
    """Feature: tennis-club-reservation, Property 27: Reservation conflicts are rejected
    Validates: Requirements 11.1, 11.5
    
    For any court and time slot with an existing active reservation, attempts to create 
    another reservation for the same court and time should be rejected.
    """
    with app.app_context():
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=court_num).first()
        assert court is not None, f"Court {court_num} should exist"
        
        # Create test member with unique email
        unique_id = random.randint(100000, 999999)
        member = Member(firstname="Test", lastname="Member", email=f"test_{unique_id}_{court_num}_{booking_date}_{start}@example.com", role="member")
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        
        # Calculate end time
        end = time(start.hour + 1, start.minute) if start.hour < 21 else time(22, 0)
        
        # Create first reservation
        reservation1 = Reservation(
            court_id=court.id,
            date=booking_date,
            start_time=start,
            end_time=end,
            booked_for_id=member.id,
            booked_by_id=member.id,
            status='active'
        )
        db.session.add(reservation1)
        db.session.commit()
        
        # Validate that a conflict is detected
        result = ValidationService.validate_no_conflict(court.id, booking_date, start)
        assert result is False, f"Conflict should be detected for court {court_num} on {booking_date} at {start}"
        
        # Cleanup
        db.session.delete(reservation1)
        db.session.delete(member)
        db.session.commit()


@given(court_num=court_numbers, booking_date=future_dates, start=booking_times)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_27_no_conflict_when_slot_free(app, court_num, booking_date, start):
    """Feature: tennis-club-reservation, Property 27: Reservation conflicts are rejected
    Validates: Requirements 11.1, 11.5
    
    For any court and time slot without an existing reservation, validation should pass.
    """
    with app.app_context():
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=court_num).first()
        assert court is not None, f"Court {court_num} should exist"
        
        # Validate that no conflict exists
        result = ValidationService.validate_no_conflict(court.id, booking_date, start)
        assert result is True, f"No conflict should exist for court {court_num} on {booking_date} at {start}"



from app.models import Block


block_reasons = st.sampled_from(['rain', 'maintenance', 'tournament', 'championship'])


@given(court_num=court_numbers, block_date=future_dates, start=booking_times, reason=block_reasons)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_13_blocks_prevent_reservations(app, court_num, block_date, start, reason):
    """Feature: tennis-club-reservation, Property 13: Blocks prevent new reservations
    Validates: Requirements 5.1, 11.2
    
    For any court and time period with an active block, attempts to create reservations 
    for that court during the blocked period should be rejected.
    """
    with app.app_context():
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=court_num).first()
        assert court is not None, f"Court {court_num} should exist"
        
        # Create test admin with unique email
        unique_id = random.randint(100000, 999999)
        admin = Member(firstname="Admin", lastname="Admin", email=f"admin_{unique_id}_{court_num}_{block_date}_{start}@example.com", role="administrator")
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()
        
        # Calculate end time
        end = time(start.hour + 1, start.minute) if start.hour < 21 else time(22, 0)
        
        # Create block
        block = Block(
            court_id=court.id,
            date=block_date,
            start_time=start,
            end_time=end,
            reason=reason,
            created_by_id=admin.id
        )
        db.session.add(block)
        db.session.commit()
        
        # Validate that the block prevents reservations
        result = ValidationService.validate_not_blocked(court.id, block_date, start)
        assert result is False, f"Block should prevent reservation for court {court_num} on {block_date} at {start}"
        
        # Cleanup
        db.session.delete(block)
        db.session.delete(admin)
        db.session.commit()


@given(court_num=court_numbers, booking_date=future_dates, start=booking_times)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_13_no_block_allows_reservations(app, court_num, booking_date, start):
    """Feature: tennis-club-reservation, Property 13: Blocks prevent new reservations
    Validates: Requirements 5.1, 11.2
    
    For any court and time period without a block, validation should pass.
    """
    with app.app_context():
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=court_num).first()
        assert court is not None, f"Court {court_num} should exist"
        
        # Validate that no block exists
        result = ValidationService.validate_not_blocked(court.id, booking_date, start)
        assert result is True, f"No block should exist for court {court_num} on {booking_date} at {start}"


# ============================================================================
# SHORT NOTICE BOOKING PROPERTY TESTS
# ============================================================================

from datetime import datetime, timedelta
from app.services.reservation_service import ReservationService


# Strategies for short notice testing
minutes_before_start = st.integers(min_value=1, max_value=30)
short_notice_minutes = st.integers(min_value=1, max_value=15)
regular_notice_minutes = st.integers(min_value=16, max_value=120)


@given(minutes_before=short_notice_minutes)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_40_short_notice_booking_classification(app, minutes_before):
    """Feature: tennis-club-reservation, Property 40: Short notice booking classification
    Validates: Requirements 18.1
    
    For any booking made within 15 minutes of start time, the system should classify it as short notice.
    """
    with app.app_context():
        # Set up test scenario
        current_time = datetime(2024, 1, 15, 10, 0)  # 10:00 AM
        booking_date = date(2024, 1, 15)
        start_time = time(10, minutes_before)  # Start time is minutes_before minutes after current time
        
        result = ReservationService.is_short_notice_booking(booking_date, start_time, current_time)
        assert result is True, f"Booking {minutes_before} minutes before start should be classified as short notice"
        
        classification = ReservationService.classify_booking_type(booking_date, start_time, current_time)
        assert classification == 'short_notice', f"Booking type should be 'short_notice', got '{classification}'"


@given(minutes_before=regular_notice_minutes)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_40_regular_booking_classification(app, minutes_before):
    """Feature: tennis-club-reservation, Property 40: Short notice booking classification
    Validates: Requirements 18.1
    
    For any booking made more than 15 minutes before start time, the system should classify it as regular.
    """
    with app.app_context():
        # Set up test scenario
        current_time = datetime(2024, 1, 15, 10, 0)  # 10:00 AM
        booking_date = date(2024, 1, 15)
        # Calculate start time that's more than 15 minutes away
        future_time = current_time + timedelta(minutes=minutes_before)
        start_time = future_time.time()
        
        result = ReservationService.is_short_notice_booking(booking_date, start_time, current_time)
        assert result is False, f"Booking {minutes_before} minutes before start should not be classified as short notice"
        
        classification = ReservationService.classify_booking_type(booking_date, start_time, current_time)
        assert classification == 'regular', f"Booking type should be 'regular', got '{classification}'"


@given(existing_regular=st.integers(min_value=0, max_value=2))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_41_short_notice_bookings_excluded_from_limit(app, existing_regular):
    """Feature: tennis-club-reservation, Property 41: Short notice bookings excluded from reservation limit
    Validates: Requirements 18.2, 18.3
    
    Short notice bookings should not count toward the 2-reservation limit.
    """
    with app.app_context():
        # Get existing court
        court = Court.query.filter_by(number=1).first()
        assert court is not None, "Court 1 should exist"
        
        # Create test member
        unique_id = random.randint(100000, 999999)
        member = Member(firstname="Test", lastname="Member", email=f"test_short_notice_{unique_id}@example.com", role="member")
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        
        # Create existing regular reservations
        for i in range(existing_regular):
            reservation = Reservation(
                court_id=court.id,
                date=date.today() + timedelta(days=i+1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                booked_for_id=member.id,
                booked_by_id=member.id,
                status='active',
                is_short_notice=False
            )
            db.session.add(reservation)
        
        # Create some short notice reservations (should not count toward limit)
        for i in range(3):
            reservation = Reservation(
                court_id=court.id,
                date=date.today() + timedelta(days=i+10),
                start_time=time(11, 0),
                end_time=time(12, 0),
                booked_for_id=member.id,
                booked_by_id=member.id,
                status='active',
                is_short_notice=True
            )
            db.session.add(reservation)
        
        db.session.commit()
        
        # Test that short notice bookings are always allowed regardless of regular limit
        result_short_notice = ValidationService.validate_member_reservation_limit(member.id, is_short_notice=True)
        assert result_short_notice is True, "Short notice bookings should always be allowed"
        
        # Test that regular booking limit only counts regular reservations
        result_regular = ValidationService.validate_member_reservation_limit(member.id, is_short_notice=False)
        expected = existing_regular < 2
        assert result_regular == expected, f"Regular booking should be {'allowed' if expected else 'blocked'} with {existing_regular} existing regular reservations"
        
        # Cleanup
        Reservation.query.filter_by(booked_for_id=member.id).delete()
        db.session.delete(member)
        db.session.commit()


@given(minutes_until_start=st.integers(min_value=1, max_value=30))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_46_cancellation_prevented_within_15_minutes(app, minutes_until_start):
    """Feature: tennis-club-reservation, Property 46: Cancellation prevented within 15 minutes and during slot time
    Validates: Requirements 2.3, 2.4
    
    Reservations cannot be cancelled within 15 minutes of start time or once started.
    """
    with app.app_context():
        # Get existing court
        court = Court.query.filter_by(number=1).first()
        assert court is not None, "Court 1 should exist"
        
        # Create test member
        unique_id = random.randint(100000, 999999)
        member = Member(firstname="Test", lastname="Member", email=f"test_cancel_{unique_id}@example.com", role="member")
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        
        # Create reservation
        reservation_date = date.today()
        start_time = time(10, 0)
        reservation = Reservation(
            court_id=court.id,
            date=reservation_date,
            start_time=start_time,
            end_time=time(11, 0),
            booked_for_id=member.id,
            booked_by_id=member.id,
            status='active',
            is_short_notice=False
        )
        db.session.add(reservation)
        db.session.commit()
        
        # Test cancellation at different times before start
        current_time = datetime.combine(reservation_date, start_time) - timedelta(minutes=minutes_until_start)
        
        is_allowed, error_msg = ValidationService.validate_cancellation_allowed(reservation.id, current_time)
        
        if minutes_until_start < 15:
            assert is_allowed is False, f"Cancellation should be blocked {minutes_until_start} minutes before start"
            assert "weniger als 15 Minuten" in error_msg, "Error message should mention 15-minute restriction"
        else:
            assert is_allowed is True, f"Cancellation should be allowed {minutes_until_start} minutes before start"
        
        # Cleanup
        db.session.delete(reservation)
        db.session.delete(member)
        db.session.commit()


@given(st.just(True))
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_47_short_notice_bookings_cannot_be_cancelled(app, _):
    """Feature: tennis-club-reservation, Property 47: Short notice bookings cannot be cancelled
    Validates: Requirements 18.10
    
    Short notice bookings can never be cancelled, regardless of timing.
    """
    with app.app_context():
        # Get existing court
        court = Court.query.filter_by(number=1).first()
        assert court is not None, "Court 1 should exist"
        
        # Create test member
        unique_id = random.randint(100000, 999999)
        member = Member(firstname="Test", lastname="Member", email=f"test_short_cancel_{unique_id}@example.com", role="member")
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        
        # Create short notice reservation
        reservation_date = date.today() + timedelta(days=1)
        start_time = time(10, 0)
        reservation = Reservation(
            court_id=court.id,
            date=reservation_date,
            start_time=start_time,
            end_time=time(11, 0),
            booked_for_id=member.id,
            booked_by_id=member.id,
            status='active',
            is_short_notice=True
        )
        db.session.add(reservation)
        db.session.commit()
        
        # Test cancellation well before start time (should still be blocked for short notice)
        current_time = datetime.combine(reservation_date, start_time) - timedelta(hours=2)
        
        is_allowed, error_msg = ValidationService.validate_cancellation_allowed(reservation.id, current_time)
        
        assert is_allowed is False, "Short notice bookings should never be cancellable"
        assert "Kurzfristige Buchungen können nicht storniert werden" in error_msg, "Error message should mention short notice restriction"
        
        # Cleanup
        db.session.delete(reservation)
        db.session.delete(member)
        db.session.commit()


@given(existing_short_notice=st.integers(min_value=0, max_value=1))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_42a_short_notice_booking_limit_enforcement(app, existing_short_notice):
    """Feature: tennis-club-reservation, Property 42a: Short notice booking limit enforcement
    Validates: Requirements 18.5, 18.6
    
    For any member with 1 active short notice booking, attempting to create another 
    short notice booking should be rejected until the existing short notice booking 
    is completed or cancelled.
    """
    with app.app_context():
        # Get existing court
        court = Court.query.filter_by(number=1).first()
        assert court is not None, "Court 1 should exist"
        
        # Create test member
        unique_id = random.randint(100000, 999999)
        member = Member(firstname="Test", lastname="Member", email=f"test_short_limit_{unique_id}@example.com", role="member")
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        
        # Create existing short notice reservations
        for i in range(existing_short_notice):
            reservation = Reservation(
                court_id=court.id,
                date=date.today() + timedelta(days=i+1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                booked_for_id=member.id,
                booked_by_id=member.id,
                status='active',
                is_short_notice=True
            )
            db.session.add(reservation)
        
        # Create some regular reservations (should not affect short notice limit)
        for i in range(2):
            reservation = Reservation(
                court_id=court.id,
                date=date.today() + timedelta(days=i+10),
                start_time=time(11, 0),
                end_time=time(12, 0),
                booked_for_id=member.id,
                booked_by_id=member.id,
                status='active',
                is_short_notice=False
            )
            db.session.add(reservation)
        
        db.session.commit()
        
        # Test short notice booking limit
        result = ValidationService.validate_member_short_notice_limit(member.id)
        
        if existing_short_notice == 0:
            assert result is True, "Member with 0 short notice bookings should be allowed to make one"
        else:  # existing_short_notice == 1
            assert result is False, "Member with 1 short notice booking should not be allowed to make another"
        
        # Test that the limit is enforced in validate_all_booking_constraints
        booking_date = date.today() + timedelta(days=20)
        start_time = time(14, 0)
        
        is_valid, error_msg = ValidationService.validate_all_booking_constraints(
            court_id=court.id,
            date=booking_date,
            start_time=start_time,
            member_id=member.id,
            is_short_notice=True
        )
        
        if existing_short_notice == 0:
            assert is_valid is True, "Short notice booking should be allowed when under limit"
        else:  # existing_short_notice == 1
            assert is_valid is False, "Short notice booking should be blocked when at limit"
            assert "bereits eine aktive kurzfristige Buchung" in error_msg, "Error message should mention short notice limit"
        
        # Cleanup
        Reservation.query.filter_by(booked_for_id=member.id).delete()
        db.session.delete(member)
        db.session.commit()
