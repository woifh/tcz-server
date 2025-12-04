"""Authorization decorators for route protection."""
from functools import wraps
from flask import flash, redirect, url_for, jsonify, request
from flask_login import current_user


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
            flash('Bitte melden Sie sich an, um auf diese Seite zuzugreifen.', 'info')
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
            flash('Bitte melden Sie sich an, um auf diese Seite zuzugreifen.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_admin():
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403
            flash('Sie haben keine Berechtigung für diese Aktion', 'error')
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
            flash('Bitte melden Sie sich an, um auf diese Seite zuzugreifen.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        
        member_id = kwargs.get('id')
        if member_id and current_user.id != member_id and not current_user.is_admin():
            if request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'error': 'Sie haben keine Berechtigung für diese Aktion'}), 403
            flash('Sie haben keine Berechtigung für diese Aktion', 'error')
            return redirect(url_for('dashboard.index')), 403
        
        return f(*args, **kwargs)
    return decorated_function
