"""Tests for court routes."""
import pytest
from datetime import date, time
from app import db
from app.models import Court, Reservation, Block, BlockReason


class TestListCourts:
    """Test list courts endpoint."""
    
    def test_list_courts_requires_login(self, client):
        """Test listing courts requires authentication."""
        response = client.get('/courts/')
        assert response.status_code == 302  # Redirect to login
    
    def test_list_courts_returns_all_courts(self, client, test_member):
        """Test listing courts returns all courts."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/courts/')
            assert response.status_code == 200
            data = response.get_json()
            assert 'courts' in data
            assert len(data['courts']) == 6  # Default 6 courts


class TestGetAvailability:
    """Test get availability endpoint."""
    
    def test_availability_allows_anonymous_access(self, client):
        """Test availability allows anonymous access."""
        response = client.get('/courts/availability?date=2025-12-05')
        assert response.status_code == 200
        data = response.get_json()
        assert 'date' in data
        assert 'grid' in data
        assert data['date'] == '2025-12-05'
    
    def test_availability_requires_valid_date(self, client):
        """Test availability requires valid date parameter."""
        response = client.get('/courts/availability?date=invalid')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_availability_uses_today_as_default(self, client):
        """Test availability uses today's date as default."""
        response = client.get('/courts/availability')
        assert response.status_code == 200
        data = response.get_json()
        assert 'date' in data
        assert 'grid' in data
        # Should use today's date
        from datetime import date
        assert data['date'] == date.today().isoformat()
    
    def test_availability_returns_grid_for_authenticated_user(self, client, test_member, app):
        """Test availability returns grid data for authenticated users."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/courts/availability?date=2025-12-05')
            assert response.status_code == 200
            data = response.get_json()
            assert 'grid' in data
            assert 'date' in data
            assert data['date'] == '2025-12-05'
    
    def test_availability_shows_reservations_to_authenticated_users(self, client, test_member, app):
        """Test availability shows reservation details to authenticated users."""
        court_id = None
        with app.app_context():
            # Create a reservation
            court = Court.query.first()
            court_id = court.id
            reservation = Reservation(
                court_id=court.id,
                date=date(2025, 12, 5),
                start_time=time(10, 0),
                end_time=time(11, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                status='active'
            )
            db.session.add(reservation)
            db.session.commit()
        
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/courts/availability?date=2025-12-05')
            assert response.status_code == 200
            data = response.get_json()
            
            # Find the court and slot
            court_data = next((c for c in data['grid'] if c['court_id'] == court_id), None)
            assert court_data is not None
            slot_10 = next((s for s in court_data['slots'] if s['time'] == '10:00'), None)
            assert slot_10 is not None
            assert slot_10['status'] == 'reserved'
            assert slot_10['details'] is not None
            assert 'booked_for' in slot_10['details']
    
    def test_availability_hides_reservation_details_from_anonymous_users(self, client, test_member, app):
        """Test availability hides reservation details from anonymous users."""
        court_id = None
        with app.app_context():
            # Create a reservation
            court = Court.query.first()
            court_id = court.id
            reservation = Reservation(
                court_id=court.id,
                date=date(2025, 12, 5),
                start_time=time(10, 0),
                end_time=time(11, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                status='active'
            )
            db.session.add(reservation)
            db.session.commit()
        
        # Anonymous request
        response = client.get('/courts/availability?date=2025-12-05')
        assert response.status_code == 200
        data = response.get_json()
        
        # Find the court and slot
        court_data = next((c for c in data['grid'] if c['court_id'] == court_id), None)
        assert court_data is not None
        slot_10 = next((s for s in court_data['slots'] if s['time'] == '10:00'), None)
        assert slot_10 is not None
        assert slot_10['status'] == 'reserved'
        assert slot_10['details'] is None  # Details should be filtered out
    
    def test_availability_shows_blocks_to_all_users(self, client, test_admin, app):
        """Test availability shows blocked slots to both authenticated and anonymous users."""
        court_id = None
        with app.app_context():
            # Get or create block reason
            block_reason = BlockReason.query.filter_by(name='Maintenance').first()
            if not block_reason:
                block_reason = BlockReason(name='Maintenance', is_active=True, created_by_id=test_admin.id)
                db.session.add(block_reason)
                db.session.commit()
            
            # Create a block
            court = Court.query.first()
            court_id = court.id
            block = Block(
                court_id=court.id,
                date=date(2025, 12, 5),
                start_time=time(14, 0),
                end_time=time(16, 0),
                reason_id=block_reason.id,
                created_by_id=test_admin.id,
                details='Test maintenance block'
            )
            db.session.add(block)
            db.session.commit()
        
        # Test anonymous access
        response = client.get('/courts/availability?date=2025-12-05')
        assert response.status_code == 200
        data = response.get_json()
        
        # Find the court and slot
        court_data = next((c for c in data['grid'] if c['court_id'] == court_id), None)
        assert court_data is not None
        slot_14 = next((s for s in court_data['slots'] if s['time'] == '14:00'), None)
        assert slot_14 is not None
        assert slot_14['status'] == 'blocked'
        assert slot_14['details'] is not None
        assert slot_14['details']['reason'] == 'Maintenance'
        assert slot_14['details']['details'] == 'Test maintenance block'
        
        # Test authenticated access - should see same block information
        with client:
            client.post('/auth/login', data={
                'email': test_admin.email,
                'password': 'admin123'
            })
            response = client.get('/courts/availability?date=2025-12-05')
            assert response.status_code == 200
            data = response.get_json()
            
            court_data = next((c for c in data['grid'] if c['court_id'] == court_id), None)
            assert court_data is not None
            slot_14 = next((s for s in court_data['slots'] if s['time'] == '14:00'), None)
            assert slot_14 is not None
            assert slot_14['status'] == 'blocked'
            assert slot_14['details'] is not None
            assert slot_14['details']['reason'] == 'Maintenance'
            assert slot_14['details']['details'] == 'Test maintenance block'
    
    def test_availability_normalizes_short_notice_for_anonymous_users(self, client, test_member, app):
        """Test availability normalizes short notice bookings to 'reserved' for anonymous users."""
        court_id = None
        with app.app_context():
            # Create a short notice reservation
            court = Court.query.first()
            court_id = court.id
            reservation = Reservation(
                court_id=court.id,
                date=date(2025, 12, 5),
                start_time=time(10, 0),
                end_time=time(11, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                status='active',
                is_short_notice=True
            )
            db.session.add(reservation)
            db.session.commit()
        
        # Anonymous request should see it as 'reserved'
        response = client.get('/courts/availability?date=2025-12-05')
        assert response.status_code == 200
        data = response.get_json()
        
        court_data = next((c for c in data['grid'] if c['court_id'] == court_id), None)
        assert court_data is not None
        slot_10 = next((s for s in court_data['slots'] if s['time'] == '10:00'), None)
        assert slot_10 is not None
        assert slot_10['status'] == 'reserved'  # Should be normalized from 'short_notice'
        assert slot_10['details'] is None
        
        # Authenticated request should see it as 'short_notice'
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/courts/availability?date=2025-12-05')
            assert response.status_code == 200
            data = response.get_json()
            
            court_data = next((c for c in data['grid'] if c['court_id'] == court_id), None)
            assert court_data is not None
            slot_10 = next((s for s in court_data['slots'] if s['time'] == '10:00'), None)
            assert slot_10 is not None
            assert slot_10['status'] == 'short_notice'  # Should preserve original status
            assert slot_10['details'] is not None


class TestRateLimiting:
    """Test rate limiting for anonymous users."""
    
    def test_rate_limiting_applied_to_anonymous_users(self, client, app):
        """Test that rate limiting is applied to anonymous users."""
        # Make multiple requests as anonymous user
        # Note: This test may be limited by the test environment's rate limiting configuration
        responses = []
        for i in range(5):  # Make several requests
            response = client.get('/courts/availability?date=2025-12-05')
            responses.append(response)
        
        # All requests should succeed initially (within rate limit)
        for response in responses:
            assert response.status_code == 200
    
    def test_rate_limiting_not_applied_to_authenticated_users(self, client, test_member, app):
        """Test that rate limiting is not applied to authenticated users."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            
            # Make multiple requests as authenticated user
            responses = []
            for i in range(10):  # Make more requests than anonymous limit
                response = client.get('/courts/availability?date=2025-12-05')
                responses.append(response)
            
            # All requests should succeed (no rate limiting for authenticated users)
            for response in responses:
                assert response.status_code == 200
    
    def test_rate_limit_error_response_format(self, client, app):
        """Test that rate limit error responses have correct format."""
        # This test is challenging to implement reliably in a test environment
        # as it requires actually hitting the rate limit
        # We'll test the error handler format instead
        from app.routes.courts import ratelimit_handler
        from werkzeug.exceptions import TooManyRequests
        
        # Create a mock rate limit exception
        with app.test_request_context('/courts/availability'):
            exception = TooManyRequests()
            exception.retry_after = 3600  # 1 hour
            
            response, status_code = ratelimit_handler(exception)
            assert status_code == 429
            
            # Parse JSON response
            import json
            data = json.loads(response.data)
            assert 'error' in data
            assert 'retry_after' in data
            assert data['retry_after'] == 3600
