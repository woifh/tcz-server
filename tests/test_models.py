"""Property-based tests for database models."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, time, timedelta
from app.models import Member, Court, Reservation, Block, Notification
from app import db


# Hypothesis strategies for generating test data
member_names = st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
member_emails = st.emails()
member_passwords = st.text(min_size=8, max_size=50)
member_roles = st.sampled_from(['member', 'administrator'])

court_numbers = st.integers(min_value=1, max_value=6)
court_statuses = st.sampled_from(['available', 'blocked'])

booking_times = st.times(min_value=time(6, 0), max_value=time(20, 0))
future_dates = st.dates(min_value=date.today(), max_value=date.today() + timedelta(days=90))
reservation_statuses = st.sampled_from(['active', 'cancelled', 'completed'])

block_reasons = st.sampled_from(['rain', 'maintenance', 'tournament', 'championship'])

notification_types = st.sampled_from(['booking_created', 'booking_modified', 'booking_cancelled', 'admin_override'])
notification_messages = st.text(min_size=1, max_size=500)


@given(name=member_names, email=member_emails, password=member_passwords, role=member_roles)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_17_member_creation_stores_all_fields(app, name, email, password, role):
    """Feature: tennis-club-reservation, Property 17: Member creation stores all fields
    Validates: Requirements 6.1, 13.3
    
    For any valid name, email, password, and role, creating a member should result in 
    a database record containing all fields with the password properly hashed.
    """
    with app.app_context():
        # Create member
        member = Member(name=name, email=email, role=role)
        member.set_password(password)
        
        db.session.add(member)
        db.session.commit()
        
        # Retrieve member from database
        retrieved = Member.query.filter_by(email=email).first()
        
        # Verify all fields are stored correctly
        assert retrieved is not None
        assert retrieved.name == name
        assert retrieved.email == email
        assert retrieved.role == role
        assert retrieved.created_at is not None
        
        # Verify password is hashed (not stored in plain text)
        assert retrieved.password_hash != password
        assert retrieved.password_hash is not None
        assert len(retrieved.password_hash) > 0
        
        # Verify password verification works
        assert retrieved.check_password(password) is True
        assert retrieved.check_password(password + "wrong") is False
        
        # Cleanup
        db.session.delete(retrieved)
        db.session.commit()



@given(court_num=court_numbers, booking_date=future_dates, start=booking_times)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_1_reservation_stores_all_fields(app, court_num, booking_date, start):
    """Feature: tennis-club-reservation, Property 1: Reservation creation stores all required fields
    Validates: Requirements 1.1, 1.2
    
    For any valid court, date, time, booked_for member, and booked_by member, creating a 
    reservation should result in a database record containing all five fields with correct values.
    """
    with app.app_context():
        # Create test court
        court = Court(number=court_num)
        db.session.add(court)
        db.session.commit()
        
        # Create test members
        member1 = Member(name="Test Member 1", email=f"test1_{booking_date}_{start}@example.com", role="member")
        member1.set_password("password123")
        member2 = Member(name="Test Member 2", email=f"test2_{booking_date}_{start}@example.com", role="member")
        member2.set_password("password123")
        db.session.add(member1)
        db.session.add(member2)
        db.session.commit()
        
        # Calculate end time (1 hour after start)
        end = time(start.hour + 1, start.minute)
        
        # Create reservation
        reservation = Reservation(
            court_id=court.id,
            date=booking_date,
            start_time=start,
            end_time=end,
            booked_for_id=member1.id,
            booked_by_id=member2.id,
            status='active'
        )
        db.session.add(reservation)
        db.session.commit()
        
        # Retrieve reservation from database
        retrieved = Reservation.query.filter_by(
            court_id=court.id,
            date=booking_date,
            start_time=start
        ).first()
        
        # Verify all fields are stored correctly
        assert retrieved is not None
        assert retrieved.court_id == court.id
        assert retrieved.date == booking_date
        assert retrieved.start_time == start
        assert retrieved.end_time == end
        assert retrieved.booked_for_id == member1.id
        assert retrieved.booked_by_id == member2.id
        assert retrieved.status == 'active'
        assert retrieved.created_at is not None
        
        # Cleanup
        db.session.delete(retrieved)
        db.session.delete(member1)
        db.session.delete(member2)
        db.session.delete(court)
        db.session.commit()



@given(court_num=court_numbers, block_date=future_dates, start=booking_times, reason=block_reasons)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_16_block_stores_all_fields(app, court_num, block_date, start, reason):
    """Feature: tennis-club-reservation, Property 16: Block creation stores all fields
    Validates: Requirements 5.4
    
    For any valid court, date, time range, and reason, creating a block should result in 
    a database record containing all fields with correct values.
    """
    with app.app_context():
        # Create test court
        court = Court(number=court_num)
        db.session.add(court)
        db.session.commit()
        
        # Create test admin member
        admin = Member(name="Admin", email=f"admin_{block_date}_{start}_{reason}@example.com", role="administrator")
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()
        
        # Calculate end time (1 hour after start)
        end = time(start.hour + 1, start.minute)
        
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
        
        # Retrieve block from database
        retrieved = Block.query.filter_by(
            court_id=court.id,
            date=block_date,
            start_time=start
        ).first()
        
        # Verify all fields are stored correctly
        assert retrieved is not None
        assert retrieved.court_id == court.id
        assert retrieved.date == block_date
        assert retrieved.start_time == start
        assert retrieved.end_time == end
        assert retrieved.reason == reason
        assert retrieved.created_by_id == admin.id
        assert retrieved.created_at is not None
        
        # Cleanup
        db.session.delete(retrieved)
        db.session.delete(admin)
        db.session.delete(court)
        db.session.commit()
