"""Property-based tests for authentication functionality."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from flask_login import current_user
from app import create_app, db
from app.models import Member


# Hypothesis strategies for generating test data
valid_emails = st.emails()
valid_passwords = st.text(min_size=8, max_size=50, alphabet=st.characters(min_codepoint=33, max_codepoint=126))
valid_names = st.text(min_size=1, max_size=100, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
    blacklist_characters='\x00'
))


@given(
    name=valid_names,
    email=valid_emails,
    password=valid_passwords
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_28_valid_login_creates_session(name, email, password):
    """Feature: tennis-club-reservation, Property 28: Valid login creates session
    Validates: Requirements 13.1
    
    For any member with valid credentials, logging in should create an authenticated 
    session that allows access to protected features.
    """
    # Create app and client for this test
    app = create_app('testing')
    client = app.test_client()
    
    with app.app_context():
        db.create_all()
        
        # Create a member with the generated credentials
        member = Member(name=name, email=email, role="member")
        member.set_password(password)
        db.session.add(member)
        db.session.commit()
        member_id = member.id
    
    try:
        # Attempt to login with valid credentials
        response = client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=False)
        
        # Should redirect after successful login
        assert response.status_code in [302, 303], \
            f"Expected redirect after login, got {response.status_code}"
        
        # Verify session was created by checking we can access a protected page
        # (The redirect itself indicates successful authentication)
        with client.session_transaction() as sess:
            # Flask-Login stores user_id in session
            assert '_user_id' in sess, "Session should contain user_id after login"
            assert sess['_user_id'] == str(member_id), \
                f"Session user_id should match member id {member_id}"
    
    finally:
        # Cleanup
        with app.app_context():
            db.session.remove()
            db.drop_all()


@given(
    email=valid_emails,
    password=valid_passwords,
    wrong_password=valid_passwords
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_29_invalid_login_rejected(email, password, wrong_password):
    """Feature: tennis-club-reservation, Property 29: Invalid login is rejected
    Validates: Requirements 13.2
    
    For any login attempt with invalid credentials (wrong email or password), 
    the system should reject the login and display an error message.
    """
    # Ensure wrong_password is different from password
    if password == wrong_password:
        wrong_password = password + "different"
    
    # Create app and client for this test
    app = create_app('testing')
    client = app.test_client()
    
    with app.app_context():
        db.create_all()
        
        # Create a member with known credentials
        member = Member(firstname="Test", lastname="User", email=email, role="member")
        member.set_password(password)
        db.session.add(member)
        db.session.commit()
        member_id = member.id
    
    try:
        # Test 1: Wrong password
        response = client.post('/auth/login', data={
            'email': email,
            'password': wrong_password
        }, follow_redirects=True)
        
        # Should not redirect (stays on login page) or shows error
        assert response.status_code == 200, \
            f"Expected 200 for failed login, got {response.status_code}"
        
        # Should display error message in German
        assert 'E-Mail oder Passwort ist falsch' in response.data.decode('utf-8'), \
            "Error message should be displayed for invalid credentials"
        
        # Verify no session was created
        with client.session_transaction() as sess:
            assert '_user_id' not in sess, \
                "Session should not contain user_id after failed login"
        
        # Test 2: Wrong email (non-existent user)
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': password
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'E-Mail oder Passwort ist falsch' in response.data.decode('utf-8')
        
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    finally:
        # Cleanup
        with app.app_context():
            db.session.remove()
            db.drop_all()


@given(
    name=valid_names,
    email=valid_emails,
    password=valid_passwords
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_30_logout_terminates_session(name, email, password):
    """Feature: tennis-club-reservation, Property 30: Logout terminates session
    Validates: Requirements 13.4
    
    For any authenticated member, logging out should terminate the session 
    and prevent access to protected features.
    """
    # Create app and client for this test
    app = create_app('testing')
    client = app.test_client()
    
    with app.app_context():
        db.create_all()
        
        # Create a member
        member = Member(name=name, email=email, role="member")
        member.set_password(password)
        db.session.add(member)
        db.session.commit()
        member_id = member.id
    
    try:
        # First, login
        response = client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=False)
        
        assert response.status_code in [302, 303], "Login should succeed"
        
        # Verify session exists
        with client.session_transaction() as sess:
            assert '_user_id' in sess, "Session should exist after login"
            user_id_before = sess['_user_id']
        
        # Now logout
        response = client.get('/auth/logout', follow_redirects=False)
        
        # Should redirect after logout
        assert response.status_code in [302, 303], \
            f"Expected redirect after logout, got {response.status_code}"
        
        # Verify session was terminated
        with client.session_transaction() as sess:
            assert '_user_id' not in sess, \
                "Session should not contain user_id after logout"
    
    finally:
        # Cleanup
        with app.app_context():
            db.session.remove()
            db.drop_all()



@given(
    protected_route=st.sampled_from([
        '/reservations/',
        '/members/',
        '/courts/',
        '/admin/',
        '/dashboard'
    ])
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_31_unauthenticated_access_restricted(protected_route):
    """Feature: tennis-club-reservation, Property 31: Unauthenticated access is restricted
    Validates: Requirements 13.5
    
    For any protected route (reservations, member management), unauthenticated 
    requests should be rejected and redirected to login.
    """
    app = create_app('testing')
    client = app.test_client()
    
    try:
        # Try to access protected route without authentication
        response = client.get(protected_route, follow_redirects=False)
        
        # Should redirect to login (302/303) or return unauthorized (401)
        assert response.status_code in [302, 303, 401], \
            f"Unauthenticated access to {protected_route} should be restricted, got {response.status_code}"
        
        # If redirected, should redirect to login
        if response.status_code in [302, 303]:
            assert '/auth/login' in response.location or 'login' in response.location.lower(), \
                f"Should redirect to login page, got {response.location}"
    
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
