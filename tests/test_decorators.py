"""Tests for authorization decorators."""
import pytest
from flask import Flask, jsonify
from flask_login import login_user, logout_user
from app.decorators import login_required_json, admin_required, member_or_admin_required
from app.models import Member


@pytest.fixture
def test_app(app):
    """Create test routes."""
    
    @app.route('/test/json-protected')
    @login_required_json
    def json_protected():
        return jsonify({'message': 'success'})
    
    @app.route('/test/admin-only')
    @admin_required
    def admin_only():
        return jsonify({'message': 'admin access'})
    
    @app.route('/test/member/<int:id>')
    @member_or_admin_required
    def member_route(id):
        return jsonify({'message': f'member {id}'})
    
    return app


class TestLoginRequiredJson:
    """Test login_required_json decorator."""
    
    def test_unauthenticated_json_request(self, client, test_app):
        """Test unauthenticated JSON request returns 401."""
        response = client.get('/test/json-protected', 
                            headers={'Accept': 'application/json'})
        assert response.status_code == 401
        assert b'Authentifizierung erforderlich' in response.data
    
    def test_authenticated_request_succeeds(self, client, test_app, test_member):
        """Test authenticated request succeeds."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/test/json-protected')
            assert response.status_code == 200
            assert b'success' in response.data


class TestAdminRequired:
    """Test admin_required decorator."""
    
    def test_unauthenticated_returns_401(self, client, test_app):
        """Test unauthenticated request returns 401."""
        response = client.get('/test/admin-only',
                            headers={'Accept': 'application/json'})
        assert response.status_code == 401
    
    def test_non_admin_returns_403(self, client, test_app, test_member):
        """Test non-admin user returns 403."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/test/admin-only',
                                headers={'Accept': 'application/json'})
            assert response.status_code == 403
            assert b'keine Berechtigung' in response.data
    
    def test_admin_succeeds(self, client, test_app, test_admin):
        """Test admin user succeeds."""
        with client:
            client.post('/auth/login', data={
                'email': test_admin.email,
                'password': 'admin123'
            })
            response = client.get('/test/admin-only')
            assert response.status_code == 200
            assert b'admin access' in response.data


class TestMemberOrAdminRequired:
    """Test member_or_admin_required decorator."""
    
    def test_unauthenticated_returns_401(self, client, test_app):
        """Test unauthenticated request returns 401."""
        response = client.get('/test/member/1',
                            headers={'Accept': 'application/json'})
        assert response.status_code == 401
    
    def test_own_member_id_succeeds(self, client, test_app, test_member):
        """Test accessing own member ID succeeds."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get(f'/test/member/{test_member.id}')
            assert response.status_code == 200
    
    def test_different_member_id_returns_403(self, client, test_app, test_member):
        """Test accessing different member ID returns 403."""
        with client:
            client.post('/auth/login', data={
                'email': test_member.email,
                'password': 'password123'
            })
            response = client.get('/test/member/999',
                                headers={'Accept': 'application/json'})
            assert response.status_code == 403
    
    def test_admin_can_access_any_member(self, client, test_app, test_admin, test_member):
        """Test admin can access any member ID."""
        with client:
            client.post('/auth/login', data={
                'email': test_admin.email,
                'password': 'admin123'
            })
            response = client.get(f'/test/member/{test_member.id}')
            assert response.status_code == 200
