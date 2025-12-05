"""Tests for member routes."""
import pytest
from app.models import Member
from app import db


class TestListMembers:
    """Test list all members endpoint."""
    
    def test_list_members_requires_login(self, client):
        """Test listing members requires authentication."""
        response = client.get('/members/all')
        assert response.status_code == 302
    
    def test_list_members_returns_all(self, client, test_member, test_admin, app, db):
        """Test listing members returns all members."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/members/all')
            assert response.status_code == 200
            data = response.get_json()
            assert 'members' in data
            assert len(data['members']) >= 2  # At least test_member and test_admin


class TestGetFavourites:
    """Test get favourites endpoint."""
    
    def test_get_favourites_requires_login(self, client):
        """Test getting favourites requires authentication."""
        response = client.get('/members/1/favourites')
        assert response.status_code == 302
    
    def test_get_own_favourites(self, client, test_member, app, db):
        """Test getting own favourites."""
        # Create another member to favourite
        with app.app_context():
            other_member = Member(
                name='Other Member',
                email='other@example.com',
                role='member'
            )
            other_member.set_password('password123')
            db.session.add(other_member)
            db.session.commit()
            other_id = other_member.id
            
            # Add favourite using the relationship
            member = Member.query.get(test_member.id)
            other = Member.query.get(other_id)
            member.favourites.append(other)
            db.session.commit()
        
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get(f'/members/{test_member.id}/favourites')
            assert response.status_code == 200
            data = response.get_json()
            assert 'favourites' in data
            assert len(data['favourites']) == 1
            assert data['favourites'][0]['name'] == 'Other Member'
    
    def test_cannot_get_other_favourites(self, client, test_member, test_admin):
        """Test cannot get other member's favourites."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get(f'/members/{test_admin.id}/favourites',
                                headers={'Accept': 'application/json'})
            assert response.status_code == 403
    
    def test_admin_can_get_any_favourites(self, client, test_admin, test_member):
        """Test admin can get any member's favourites."""
        with client:
            client.post('/auth/login', data={
                'email': test_admin.email,
                'password': 'admin123'
            })
            response = client.get(f'/members/{test_member.id}/favourites')
            assert response.status_code == 200


class TestAddFavourite:
    """Test add favourite endpoint."""
    
    def test_add_favourite_requires_login(self, client):
        """Test adding favourite requires authentication."""
        response = client.post('/members/1/favourites',
                             json={'favourite_id': 2})
        assert response.status_code == 302
    
    def test_add_favourite_success(self, client, test_member, app, db):
        """Test adding favourite successfully."""
        # Create another member
        with app.app_context():
            other_member = Member(
                name='Favourite Member',
                email='fav@example.com',
                role='member'
            )
            other_member.set_password('password123')
            db.session.add(other_member)
            db.session.commit()
            other_id = other_member.id
        
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.post(f'/members/{test_member.id}/favourites',
                                 json={'favourite_id': other_id})
            assert response.status_code == 201
            data = response.get_json()
            assert 'message' in data
    
    def test_add_favourite_missing_id(self, client, test_member):
        """Test adding favourite without favourite_id."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.post(f'/members/{test_member.id}/favourites',
                                 json={})
            assert response.status_code == 400
    
    def test_cannot_add_favourite_for_other(self, client, test_member, test_admin):
        """Test cannot add favourite for another member."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.post(f'/members/{test_admin.id}/favourites',
                                 json={'favourite_id': test_member.id})
            assert response.status_code == 403


class TestRemoveFavourite:
    """Test remove favourite endpoint."""
    
    def test_remove_favourite_requires_login(self, client):
        """Test removing favourite requires authentication."""
        response = client.delete('/members/1/favourites/2')
        assert response.status_code == 302
    
    def test_remove_favourite_success(self, client, test_member, app, db):
        """Test removing favourite successfully."""
        # Create favourite
        with app.app_context():
            other_member = Member(
                name='To Remove',
                email='remove@example.com',
                role='member'
            )
            other_member.set_password('password123')
            db.session.add(other_member)
            db.session.commit()
            other_id = other_member.id
            
            member = Member.query.get(test_member.id)
            other = Member.query.get(other_id)
            member.favourites.append(other)
            db.session.commit()
        
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.delete(f'/members/{test_member.id}/favourites/{other_id}')
            assert response.status_code == 200
    
    def test_remove_nonexistent_favourite(self, client, test_member):
        """Test removing non-existent favourite."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.delete(f'/members/{test_member.id}/favourites/999')
            assert response.status_code == 404
