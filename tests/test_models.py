"""Property-based tests for database models."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, time, timedelta
from app.models import Member, Court, Reservation, Block, BlockReason, Notification
from app import db


# Hypothesis strategies for generating test data
member_names = st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
member_emails = st.emails()
member_passwords = st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=33, max_codepoint=126))
member_roles = st.sampled_from(['member', 'administrator'])

court_numbers = st.integers(min_value=1, max_value=6)
court_statuses = st.sampled_from(['available', 'blocked'])

booking_times = st.times(min_value=time(6, 0), max_value=time(21, 0))
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
        # Split name into first and last name
        name_parts = name.split(' ', 1)
        firstname = name_parts[0]
        lastname = name_parts[1] if len(name_parts) > 1 else ''
        
        # Make email unique by adding timestamp
        import time
        unique_email = f"test_{int(time.time() * 1000000)}_{email}"
        
        # Create member
        member = Member(firstname=firstname, lastname=lastname, email=unique_email, role=role)
        member.set_password(password)
        
        db.session.add(member)
        db.session.commit()
        
        # Retrieve member from database
        retrieved = Member.query.filter_by(email=unique_email).first()
        
        # Verify all fields are stored correctly
        assert retrieved is not None
        # The name property always concatenates firstname + " " + lastname
        expected_name = f"{firstname} {lastname}"
        assert retrieved.name == expected_name
        assert retrieved.email == unique_email
        assert retrieved.role == role
        assert retrieved.check_password(password)  # Verify password is hashed correctly
        
        # Cleanup
        db.session.delete(retrieved)
        db.session.commit()
        assert retrieved.email == unique_email
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
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=court_num).first()
        assert court is not None, f"Court {court_num} should exist"
        
        # Create test members with unique emails
        import random
        unique_id = random.randint(100000, 999999)
        member1 = Member(firstname="Test", lastname="Member 1", email=f"test1_{unique_id}_{booking_date}_{start}@example.com", role="member")
        member1.set_password("password123")
        member2 = Member(firstname="Test", lastname="Member 2", email=f"test2_{unique_id}_{booking_date}_{start}@example.com", role="member")
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
        
        # Cleanup (don't delete court - it's shared)
        db.session.delete(retrieved)
        db.session.delete(member1)
        db.session.delete(member2)
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
        # Get existing court (created by app fixture)
        court = Court.query.filter_by(number=court_num).first()
        assert court is not None, f"Court {court_num} should exist"
        
        # Create test admin member with unique email
        import random
        unique_id = random.randint(100000, 999999)
        admin = Member(firstname="Admin", lastname="Admin", email=f"admin_{unique_id}_{block_date}_{start}_{reason}@example.com", role="administrator")
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
        end = time(start.hour + 1, start.minute)
        
        # Create block
        block = Block(
            court_id=court.id,
            date=block_date,
            start_time=start,
            end_time=end,
            reason_id=block_reason.id,
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
        assert retrieved.reason_id == block_reason.id
        assert retrieved.reason == 'Maintenance'  # Test the legacy property
        assert retrieved.created_by_id == admin.id
        assert retrieved.created_at is not None
        
        # Cleanup (don't delete court - it's shared)
        db.session.delete(retrieved)
        db.session.delete(admin)
        db.session.commit()

# Hypothesis strategies for BlockReason testing
block_reason_names = st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
block_reason_active_status = st.booleans()


@given(reason_name=block_reason_names, is_active=block_reason_active_status)
@pytest.mark.usefixtures("app")
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_64_block_reason_creation_and_availability(app, reason_name, is_active):
    """Feature: tennis-club-reservation, Property 64: Block reason creation and availability
    Validates: Requirements 20.2
    
    For any valid reason name and active status, creating a BlockReason should result in a database 
    record containing all fields with correct values and the reason should be available for use.
    """
    with app.app_context():
        # Get existing court (created by app fixture)
        court = Court.query.first()
        assert court is not None, "Court should exist"
        
        # Create test admin member with unique email
        import random
        import time as time_module
        unique_id = random.randint(100000, 999999)
        timestamp = int(time_module.time() * 1000000)  # microsecond timestamp for uniqueness
        admin = Member(
            firstname="Admin", 
            lastname="Admin", 
            email=f"admin_{unique_id}_{timestamp}_{reason_name[:10]}_{is_active}@example.com", 
            role="administrator"
        )
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()
        
        # Make reason name unique by adding timestamp
        unique_reason_name = f"{reason_name}_{timestamp}_{unique_id}"
        
        # Create block reason
        block_reason = BlockReason(
            name=unique_reason_name,
            is_active=is_active,
            created_by_id=admin.id
        )
        db.session.add(block_reason)
        db.session.commit()
        
        # Retrieve block reason from database
        retrieved = BlockReason.query.filter_by(
            name=unique_reason_name,
            created_by_id=admin.id
        ).first()
        
        # Verify all fields are stored correctly
        assert retrieved is not None, "BlockReason should be stored in database"
        assert retrieved.name == unique_reason_name, f"Name should be '{unique_reason_name}', but was '{retrieved.name}'"
        assert retrieved.is_active == is_active, f"Active status should be {is_active}, but was {retrieved.is_active}"
        assert retrieved.created_by_id == admin.id, f"Created by ID should be {admin.id}, but was {retrieved.created_by_id}"
        assert retrieved.created_at is not None, "Created at timestamp should be set"
        assert retrieved.id is not None, "ID should be assigned"
        
        # Verify the reason is available for use (can be referenced by blocks)
        if is_active:
            # Create a test block using this reason
            test_block = Block(
                court_id=court.id,
                date=date(2025, 12, 15),
                start_time=time(10, 0),
                end_time=time(11, 0),
                reason_id=retrieved.id,
                created_by_id=admin.id
            )
            db.session.add(test_block)
            db.session.commit()
            
            # Verify the block can access the reason
            assert test_block.reason_obj is not None, "Block should be able to access its reason"
            assert test_block.reason_obj.name == unique_reason_name, "Block should access correct reason name"
            assert test_block.reason == unique_reason_name, "Legacy reason property should work"
            
            # Cleanup test block
            db.session.delete(test_block)
        
        # Cleanup
        db.session.delete(retrieved)
        db.session.delete(admin)
        db.session.commit()