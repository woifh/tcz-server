"""Tests for court routes."""
import pytest
from datetime import date, time
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
    
    def test_availability_requires_login(self, client):
        """Test availability requires authentication."""
        response = client.get('/courts/availability?date=2025-12-05')
        assert response.status_code == 302
    
    def test_availability_requires_date(self, client, test_member):
        """Test availability requires date parameter."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/courts/availability')
            assert response.status_code == 400
    
    def test_availability_invalid_date(self, client, test_member):
        """Test availability with invalid date format."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/courts/availability?date=invalid')
            assert response.status_code == 400
    
    def test_availability_returns_grid(self, client, test_member, app):
        """Test availability returns grid data."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/courts/availability?date=2025-12-05')
            assert response.status_code == 200
            data = response.get_json()
            assert 'availability' in data
            assert 'date' in data
            assert data['date'] == '2025-12-05'
    
    def test_availability_shows_reservations(self, client, test_member, app, db):
        """Test availability shows existing reservations."""
        with app.app_context():
            # Create a reservation
            court = Court.query.first()
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
            
            # Check that the slot is marked as reserved
            availability = data['availability']
            assert str(court.id) in availability
            assert '10:00' in availability[str(court.id)]
            assert availability[str(court.id)]['10:00']['status'] == 'reserved'
    
    def test_availability_shows_blocks(self, client, test_admin, app, db):
        """Test availability shows blocked slots."""
        with app.app_context():
            # Get or create block reason
            block_reason = BlockReason.query.filter_by(name='Maintenance').first()
            if not block_reason:
                block_reason = BlockReason(name='Maintenance', is_active=True, created_by_id=test_admin.id)
                db.session.add(block_reason)
                db.session.commit()
            
            # Create a block
            court = Court.query.first()
            block = Block(
                court_id=court.id,
                date=date(2025, 12, 5),
                start_time=time(14, 0),
                end_time=time(16, 0),
                reason_id=block_reason.id,
                created_by_id=test_admin.id
            )
            db.session.add(block)
            db.session.commit()
        
        with client:
            client.post('/auth/login', data={
                'email': test_admin.email,
                'password': 'admin123'
            })
            response = client.get('/courts/availability?date=2025-12-05')
            assert response.status_code == 200
            data = response.get_json()
            
            # Check that the slots are marked as blocked
            availability = data['availability']
            assert str(court.id) in availability
            assert '14:00' in availability[str(court.id)]
            assert availability[str(court.id)]['14:00']['status'] == 'blocked'
