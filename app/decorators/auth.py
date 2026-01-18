"""Authorization decorators for route protection."""
from functools import wraps
from flask import flash, redirect, url_for, jsonify, request, current_app
from flask_login import current_user, login_user
import jwt

from app import csrf


def _decode_jwt_token():
    """
    Decode JWT token from Authorization header and return the member.

    Returns:
        tuple: (member, error_response) - member is None if error occurred,
               error_response is None if successful
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, None  # No JWT token present

    token = auth_header[7:]
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=[current_app.config['JWT_ALGORITHM']]
        )
        from app.models import Member
        member = Member.query.get(payload['user_id'])
        return member, None

    except jwt.ExpiredSignatureError:
        return None, (jsonify({'error': 'Token expired'}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({'error': 'Invalid token'}), 401)


def jwt_or_session_required(f):
    """
    Decorator that accepts either JWT Bearer token or session cookie.
    For JWT auth, decodes token, validates user, and calls login_user()
    to ensure current_user works throughout the request.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        member, error = _decode_jwt_token()
        if error:
            return error

        if member:
            if not member.is_active:
                return jsonify({'error': 'Dein Konto wurde deaktiviert'}), 403
            if member.is_sustaining_member():
                return jsonify({'error': 'Fördermitglieder haben keinen Zugang zum Buchungssystem'}), 403
            login_user(member, remember=False)
            return f(*args, **kwargs)

        # Fall back to session-based auth
        if current_user.is_authenticated:
            return f(*args, **kwargs)

        return jsonify({'error': 'Authentifizierung erforderlich'}), 401

    # Exempt from CSRF - Bearer tokens don't need CSRF, and session auth
    # routes using this decorator are API endpoints that accept JSON
    return csrf.exempt(decorated_function)


def jwt_admin_required(f):
    """JWT-only auth + admin role required. For API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        member, error = _decode_jwt_token()
        if error:
            return error
        if not member:
            return jsonify({'error': 'Bearer token required'}), 401

        if not member.is_active:
            return jsonify({'error': 'Invalid token'}), 401
        if not member.is_admin():
            return jsonify({'error': 'Admin access required'}), 403

        login_user(member, remember=False)
        return f(*args, **kwargs)

    return csrf.exempt(decorated_function)


def session_or_jwt_admin_required(f):
    """
    Decorator that accepts either session cookie or JWT Bearer token,
    and requires admin role. For API endpoints accessible from both web and mobile.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        member, error = _decode_jwt_token()
        if error:
            return error

        if member:
            if not member.is_active:
                return jsonify({'error': 'Invalid token'}), 401
            if not member.is_admin():
                return jsonify({'error': 'Admin access required'}), 403
            login_user(member, remember=False)
            return f(*args, **kwargs)

        # Fall back to session-based auth
        if current_user.is_authenticated:
            if not current_user.is_admin():
                return jsonify({'error': 'Admin access required'}), 403
            return f(*args, **kwargs)

        return jsonify({'error': 'Authentifizierung erforderlich'}), 401

    return csrf.exempt(decorated_function)


def jwt_teamster_or_admin_required(f):
    """JWT-only auth + teamster or admin role required. For mobile API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        member, error = _decode_jwt_token()
        if error:
            return error
        if not member:
            return jsonify({'error': 'Bearer token required'}), 401

        if not member.is_active:
            return jsonify({'error': 'Invalid token'}), 401
        if not member.can_manage_blocks():
            return jsonify({'error': 'Teamster or admin access required'}), 403

        login_user(member, remember=False)
        return f(*args, **kwargs)

    return csrf.exempt(decorated_function)


def session_or_jwt_teamster_or_admin_required(f):
    """
    Decorator that accepts either session cookie or JWT Bearer token,
    and requires teamster or admin role. For API endpoints accessible from both web and mobile.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        member, error = _decode_jwt_token()
        if error:
            return error

        if member:
            if not member.is_active:
                return jsonify({'error': 'Invalid token'}), 401
            if not member.can_manage_blocks():
                return jsonify({'error': 'Teamster or admin access required'}), 403
            login_user(member, remember=False)
            return f(*args, **kwargs)

        # Fall back to session-based auth
        if current_user.is_authenticated:
            if not current_user.can_manage_blocks():
                return jsonify({'error': 'Teamster or admin access required'}), 403
            return f(*args, **kwargs)

        return jsonify({'error': 'Authentifizierung erforderlich'}), 401

    return csrf.exempt(decorated_function)


def login_required_json(f):
    """
    Decorator that requires login and returns JSON error for API endpoints.
    Use this for API routes that return JSON.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Authentifizierung erforderlich'}), 401
            flash('Bitte melde dich an, um diese Seite zu sehen.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator that requires admin role.
    Works for both HTML and JSON responses.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Authentifizierung erforderlich'}), 401
            flash('Bitte melde dich an, um diese Seite zu sehen.', 'info')
            return redirect(url_for('auth.login', next=request.url))

        if not current_user.is_admin():
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403
            flash('Du hast keine Berechtigung für diese Aktion', 'error')
            return redirect(url_for('dashboard.index')), 403

        return f(*args, **kwargs)
    return decorated_function


def member_or_admin_required(f):
    """
    Decorator that requires the user to be either the member in question or an admin.
    Expects 'id' parameter in the route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Authentifizierung erforderlich'}), 401
            flash('Bitte melde dich an, um diese Seite zu sehen.', 'info')
            return redirect(url_for('auth.login', next=request.url))

        member_id = kwargs.get('id')
        if member_id and current_user.id != member_id and not current_user.is_admin():
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403
            flash('Du hast keine Berechtigung für diese Aktion', 'error')
            return redirect(url_for('dashboard.index')), 403

        return f(*args, **kwargs)
    return decorated_function


def teamster_or_admin_required(f):
    """
    Decorator that requires teamster or admin role.
    Allows both teamsters and administrators to access block management routes.
    Works for both HTML and JSON responses.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Authentifizierung erforderlich'}), 401
            flash('Bitte melde dich an, um diese Seite zu sehen.', 'info')
            return redirect(url_for('auth.login', next=request.url))

        if not current_user.can_manage_blocks():
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Du hast keine Berechtigung für diese Aktion'}), 403
            flash('Du hast keine Berechtigung für diese Aktion', 'error')
            return redirect(url_for('dashboard.index')), 403

        return f(*args, **kwargs)
    return decorated_function


def block_owner_or_admin_required(f):
    """
    Decorator that requires block ownership or admin role.
    Checks if the current user owns the block (for teamsters) or is an admin.
    Expects 'id' parameter in the route (block ID).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Authentifizierung erforderlich'}), 401
            flash('Bitte melde dich an, um diese Seite zu sehen.', 'info')
            return redirect(url_for('auth.login', next=request.url))

        # Get block_id from route parameters
        block_id = kwargs.get('id')
        if block_id:
            from app.models import Block
            block = Block.query.get_or_404(block_id)

            if not current_user.can_edit_block(block):
                error_message = 'Du kannst nur deine eigenen Sperrungen bearbeiten'
                if request.is_json or request.accept_mimetypes.accept_json:
                    return jsonify({'error': error_message}), 403
                flash(error_message, 'error')
                return redirect(url_for('dashboard.index')), 403

        return f(*args, **kwargs)
    return decorated_function
