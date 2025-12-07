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



class TestSearchMembers:
    """Test search members endpoint."""
    
    def test_search_requires_login(self, client):
        """Test search requires authentication."""
        response = client.get('/members/search?q=test')
        assert response.status_code == 302
    
    def test_search_missing_query(self, client, test_member):
        """Test search without query parameter."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_member.id)
        
        response = client.get('/members/search')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_search_empty_query(self, client, test_member):
        """Test search with empty query."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_member.id)
        
        response = client.get('/members/search?q=')
        assert response.status_code == 400
    
    def test_search_returns_results(self, client, test_member, app):
        """Test search returns matching members."""
        # Create test members
        with app.app_context():
            from app import db
            member1 = Member(firstname="Alice", lastname="Smith", email='alice@example.com', role='member')
            member1.set_password('password123')
            member2 = Member(firstname="Bob", lastname="Johnson", email='bob@example.com', role='member')
            member2.set_password('password123')
            db.session.add_all([member1, member2])
            db.session.commit()
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_member.id)
        
        response = client.get('/members/search?q=alice')
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert 'count' in data
        assert data['count'] >= 1
        assert any(r['name'] == 'Alice Smith' for r in data['results'])
    
    def test_search_excludes_self(self, client, test_member):
        """Test search excludes current member."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_member.id)
        
        response = client.get(f'/members/search?q={test_member.name}')
        assert response.status_code == 200
        data = response.get_json()
        # Should not include self in results
        assert not any(r['id'] == test_member.id for r in data['results'])
    
    def test_search_excludes_favourites(self, client, test_member, app):
        """Test search excludes existing favourites."""
        # Create member and add as favourite
        with app.app_context():
            from app import db
            other_member = Member(firstname="Favourite", lastname="Test", email='favtest@example.com', role='member')
            other_member.set_password('password123')
            db.session.add(other_member)
            db.session.commit()
            other_id = other_member.id
            
            member = Member.query.get(test_member.id)
            other = Member.query.get(other_id)
            member.favourites.append(other)
            db.session.commit()
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_member.id)
        
        response = client.get('/members/search?q=Favourite')
        assert response.status_code == 200
        data = response.get_json()
        # Should not include favourite in results
        assert not any(r['id'] == other_id for r in data['results'])
    
    def test_search_case_insensitive(self, client, test_member, app):
        """Test search is case-insensitive."""
        with app.app_context():
            from app import db
            member = Member(firstname="TestCase", lastname="Member", email='testcase@example.com', role='member')
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_member.id)
        
        # Test different cases
        response1 = client.get('/members/search?q=testcase')
        response2 = client.get('/members/search?q=TESTCASE')
        response3 = client.get('/members/search?q=TestCase')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        data1 = response1.get_json()
        data2 = response2.get_json()
        data3 = response3.get_json()
        
        # All should return the same member
        assert data1['count'] >= 1
        assert data2['count'] >= 1
        assert data3['count'] >= 1
