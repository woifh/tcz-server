"""Property-based tests for template rendering."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import date, time, timedelta
from app import create_app, db
from app.models import Member, Court, Reservation


# Hypothesis strategies
valid_dates = st.dates(min_value=date(2024, 1, 1), max_value=date(2030, 12, 31))


@given(test_date=valid_dates)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_26_dates_formatted_german_convention(test_date):
    """Feature: tennis-club-reservation, Property 26: Dates formatted in German convention
    Validates: Requirements 10.4
    
    For any date displayed in the interface, it should be formatted according to 
    German conventions (DD.MM.YYYY).
    """
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create test data
        member = Member(name="Test User", email="test@example.com", role="member")
        member.set_password("password123")
        court = Court(number=1, status='available')
        
        db.session.add_all([member, court])
        db.session.commit()
        
        # Create a reservation with the test date
        reservation = Reservation(
            court_id=court.id,
            date=test_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            booked_for_id=member.id,
            booked_by_id=member.id,
            status='active'
        )
        db.session.add(reservation)
        db.session.commit()
    
    try:
        client = app.test_client()
        
        # Login
        with app.app_context():
            client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            # Get reservations page
            response = client.get('/reservations/')
            
            assert response.status_code == 200, "Should be able to access reservations page"
            
            # Check that date is formatted in German convention (DD.MM.YYYY)
            html = response.data.decode('utf-8')
            
            # Format the date in German convention
            german_date = test_date.strftime('%d.%m.%Y')
            
            # Verify the German formatted date appears in the HTML
            assert german_date in html, \
                f"Date should be formatted as {german_date} (DD.MM.YYYY) in the interface"
    
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
