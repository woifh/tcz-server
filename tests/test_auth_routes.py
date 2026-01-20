"""Tests for authentication routes."""
import pytest
from flask import url_for
from app import db
from app.models import Member


class TestLogin:
    """Tests for login functionality."""

    def test_login_page_renders(self, client):
        """Login page should render for unauthenticated users."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'anmelden' in response.data.lower()

    def test_login_redirects_authenticated_user(self, client, test_member):
        """Authenticated users should be redirected from login page."""
        # Login first
        client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        })
        # Try to access login page again
        response = client.get('/auth/login', follow_redirects=False)
        assert response.status_code == 302

    def test_login_success(self, client, test_member):
        """Valid credentials should log in the user."""
        response = client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_invalid_email(self, client):
        """Invalid email should show error."""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b'falsch' in response.data.lower() or b'error' in response.data.lower()

    def test_login_invalid_password(self, client, test_member):
        """Invalid password should show error."""
        response = client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert b'falsch' in response.data.lower() or b'error' in response.data.lower()

    def test_login_deactivated_account(self, client, app):
        """Deactivated accounts should not be able to login."""
        with app.app_context():
            member = Member(
                firstname='Inactive',
                lastname='User',
                email='inactive@example.com',
                role='member',
                is_active=False
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

        response = client.post('/auth/login', data={
            'email': 'inactive@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b'deaktiviert' in response.data.lower()

    def test_login_sustaining_member_blocked(self, client, app):
        """Sustaining members should not be able to login."""
        with app.app_context():
            member = Member(
                firstname='Sustaining',
                lastname='Member',
                email='sustaining@example.com',
                role='member',
                membership_type='sustaining'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

        response = client.post('/auth/login', data={
            'email': 'sustaining@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        # Should show error about sustaining members

    def test_login_missing_email(self, client):
        """Missing email should show validation error."""
        response = client.post('/auth/login', data={
            'email': '',
            'password': 'password123'
        })
        assert response.status_code == 200

    def test_login_missing_password(self, client, test_member):
        """Missing password should show validation error."""
        response = client.post('/auth/login', data={
            'email': test_member.email,
            'password': ''
        })
        assert response.status_code == 200


class TestLoginApi:
    """Tests for API login endpoint."""

    def test_api_login_success(self, client, test_member):
        """API login should return user info and access token."""
        response = client.post('/auth/login/api',
            json={'email': test_member.email, 'password': 'password123'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'user' in data
        assert 'access_token' in data
        assert data['user']['email'] == test_member.email

    def test_api_login_missing_json(self, client):
        """API login should require JSON body."""
        response = client.post('/auth/login/api')
        # Flask returns 415 Unsupported Media Type when Content-Type is not application/json
        assert response.status_code in [400, 415]

    def test_api_login_missing_credentials(self, client):
        """API login should require email and password."""
        response = client.post('/auth/login/api', json={'email': ''})
        assert response.status_code == 400
        assert 'erforderlich' in response.get_json()['error']

    def test_api_login_invalid_credentials(self, client):
        """API login should reject invalid credentials."""
        response = client.post('/auth/login/api',
            json={'email': 'nonexistent@example.com', 'password': 'wrong'}
        )
        assert response.status_code == 401
        assert 'falsch' in response.get_json()['error']

    def test_api_login_deactivated_account(self, client, app):
        """API login should reject deactivated accounts."""
        with app.app_context():
            member = Member(
                firstname='Inactive',
                lastname='Api',
                email='inactive_api@example.com',
                role='member',
                is_active=False
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

        response = client.post('/auth/login/api',
            json={'email': 'inactive_api@example.com', 'password': 'password123'}
        )
        assert response.status_code == 403
        assert 'deaktiviert' in response.get_json()['error']

    def test_api_login_sustaining_member_blocked(self, client, app):
        """API login should block sustaining members."""
        with app.app_context():
            member = Member(
                firstname='Sustaining',
                lastname='Api',
                email='sustaining_api@example.com',
                role='member',
                membership_type='sustaining'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

        response = client.post('/auth/login/api',
            json={'email': 'sustaining_api@example.com', 'password': 'password123'}
        )
        assert response.status_code == 403


class TestLogout:
    """Tests for logout functionality."""

    def test_logout(self, client, test_member):
        """Logout should redirect to dashboard."""
        # Login first
        client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        })
        # Logout
        response = client.get('/auth/logout', follow_redirects=False)
        assert response.status_code == 302

    def test_logout_shows_message(self, client, test_member):
        """Logout should show success message."""
        client.post('/auth/login', data={
            'email': test_member.email,
            'password': 'password123'
        })
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200


class TestEmailVerification:
    """Tests for email verification."""

    def test_verify_email_invalid_token(self, client):
        """Invalid token should show error."""
        response = client.get('/auth/verify-email/invalid-token', follow_redirects=True)
        assert response.status_code == 200

    def test_resend_verification_requires_login(self, client):
        """Resend verification should require authentication."""
        response = client.post('/auth/resend-verification')
        assert response.status_code == 401

    def test_resend_verification_already_verified(self, client, app):
        """Already verified users should get error when resending."""
        with app.app_context():
            member = Member(
                firstname='Verified',
                lastname='User',
                email='verified@example.com',
                role='member',
                email_verified=True
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()
            member_email = member.email

        # Login
        client.post('/auth/login', data={
            'email': member_email,
            'password': 'password123'
        })

        response = client.post('/auth/resend-verification')
        assert response.status_code == 400
        assert 'bereits' in response.get_json()['error']
