"""Property-based tests for reservation routes functionality."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, time, timedelta
from app import create_app, db
from app.models import Member, Court, Reservation


# Hypothesis strategies
valid_emails = st.emails()
valid_passwords = st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=33, max_codepoint=126))
valid_names = st.text(min_size=1, max_size=100, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
    blacklist_characters='\x00'
))


@given(
    booked_for_firstname=valid_names,
    booked_for_lastname=valid_names,
    booked_for_email=valid_emails,
    booked_by_firstname=valid_names,
    booked_by_lastname=valid_names,
    booked_by_email=valid_emails,
    other_firstname=valid_names,
    other_lastname=valid_names,
    other_email=valid_emails,
    password=valid_passwords
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_4_dual_member_access_control(
    booked_for_firstname, booked_for_lastname, booked_for_email, 
    booked_by_firstname, booked_by_lastname, booked_by_email,
    other_firstname, other_lastname, other_email, password
):
    """Feature: tennis-club-reservation, Property 4: Dual-member access control
    Validates: Requirements 2.1, 2.2, 2.3
    
    For any reservation, both the booked_for member and the booked_by member should 
    be able to view, modify, and cancel that reservation, while other members should 
    not have these permissions.
    """
    # Ensure emails are unique
    if booked_for_email == booked_by_email:
        booked_by_email = "by_" + booked_by_email
    if other_email in [booked_for_email, booked_by_email]:
        other_email = "other_" + other_email
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create courts
        for i in range(1, 7):
            court = Court(number=i)
            db.session.add(court)
        db.session.commit()
        
        # Create three members
        booked_for = Member(firstname=booked_for_firstname, lastname=booked_for_lastname, email=booked_for_email, role="member")
        booked_for.set_password(password)
        booked_by = Member(firstname=booked_by_firstname, lastname=booked_by_lastname, email=booked_by_email, role="member")
        booked_by.set_password(password)
        other_member = Member(firstname=other_firstname, lastname=other_lastname, email=other_email, role="member")
        other_member.set_password(password)
        
        db.session.add_all([booked_for, booked_by, other_member])
        db.session.commit()
        
        # Get court
        court = Court.query.filter_by(number=1).first()
        assert court is not None, "Court 1 should exist"
        
        # Create a reservation
        reservation_date = date.today() + timedelta(days=1)
        reservation = Reservation(
            court_id=court.id,
            date=reservation_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            booked_for_id=booked_for.id,
            booked_by_id=booked_by.id,
            status='active'
        )
        db.session.add(reservation)
        db.session.commit()
        
        reservation_id = reservation.id
        booked_for_id = booked_for.id
        booked_by_id = booked_by.id
        other_id = other_member.id
    
    try:
        client = app.test_client()
        
        # Test 1: booked_for can access (view via update endpoint)
        with app.app_context():
            # Login as booked_for
            client.post('/auth/login', data={
                'email': booked_for_email,
                'password': password
            })
            
            # Try to update reservation (should succeed)
            response = client.put(f'/reservations/{reservation_id}', 
                                json={'start_time': '11:00'},
                                content_type='application/json')
            
            # Should be allowed (200) or have validation error (400), but not forbidden (403)
            assert response.status_code != 403, \
                "booked_for member should be able to modify reservation"
            
            client.get('/auth/logout')
        
        # Test 2: booked_by can access
        with app.app_context():
            # Login as booked_by
            client.post('/auth/login', data={
                'email': booked_by_email,
                'password': password
            })
            
            # Try to update reservation (should succeed)
            response = client.put(f'/reservations/{reservation_id}', 
                                json={'start_time': '12:00'},
                                content_type='application/json')
            
            # Should be allowed (200) or have validation error (400), but not forbidden (403)
            assert response.status_code != 403, \
                "booked_by member should be able to modify reservation"
            
            client.get('/auth/logout')
        
        # Test 3: other member cannot access
        with app.app_context():
            # Login as other member
            client.post('/auth/login', data={
                'email': other_email,
                'password': password
            })
            
            # Try to update reservation (should fail with 403)
            response = client.put(f'/reservations/{reservation_id}', 
                                json={'start_time': '13:00'},
                                content_type='application/json')
            
            assert response.status_code == 403, \
                "Other members should not be able to modify reservation"
            
            # Try to delete reservation (should fail with 403)
            response = client.delete(f'/reservations/{reservation_id}')
            
            assert response.status_code == 403, \
                "Other members should not be able to delete reservation"
            
            client.get('/auth/logout')
    
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
