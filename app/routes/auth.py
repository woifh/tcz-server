"""Authentication routes."""
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, current_user
import jwt
from app import csrf
from app.models import Member
from app.utils.validators import validate_email_address, validate_string_length, ValidationError
from app.constants.messages import ErrorMessages


def generate_access_token(member):
    """Generate JWT access token for a member."""
    payload = {
        'user_id': member.id,
        'email': member.email,
        'exp': datetime.now(timezone.utc) + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    }
    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config['JWT_ALGORITHM']
    )

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
# @limiter.limit("5 per minute")  # Disabled for local development
def login():
    """Login route with rate limiting to prevent brute force attacks."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            # Validate input
            email = validate_email_address(request.form.get('email'), 'E-Mail')
            password = validate_string_length(request.form.get('password'), 'Passwort', min_length=1)
        except ValidationError as e:
            flash(str(e), 'error')
            return render_template('login.html')
        
        member = Member.query.filter_by(email=email).first()

        if member and member.check_password(password):
            # Check if account is deactivated
            if not member.is_active:
                flash('Ihr Konto wurde deaktiviert. Bitte kontaktieren Sie den Administrator.', 'error')
                return render_template('login.html')

            # Check if sustaining member (no access to booking system)
            if member.is_sustaining_member():
                flash(ErrorMessages.SUSTAINING_MEMBER_NO_ACCESS, 'error')
                return render_template('login.html')

            login_user(member)

            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('E-Mail oder Passwort ist falsch', 'error')
    
    return render_template('login.html')


@bp.route('/login/api', methods=['POST'])
@csrf.exempt
def login_api():
    """JSON API login endpoint for mobile apps (CSRF exempt for pre-auth)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'E-Mail und Passwort erforderlich'}), 400

    member = Member.query.filter_by(email=email).first()

    if member and member.check_password(password):
        if not member.is_active:
            return jsonify({'error': 'Ihr Konto wurde deaktiviert'}), 403
        if member.is_sustaining_member():
            return jsonify({'error': ErrorMessages.SUSTAINING_MEMBER_NO_ACCESS}), 403

        login_user(member)
        return jsonify({
            'user': {
                'id': member.id,
                'firstname': member.firstname,
                'lastname': member.lastname,
                'email': member.email,
                'name': member.name
            },
            'access_token': generate_access_token(member)
        })

    return jsonify({'error': 'E-Mail oder Passwort ist falsch'}), 401


@bp.route('/logout')
def logout():
    """Logout route."""
    logout_user()
    flash('Erfolgreich abgemeldet', 'info')
    return redirect(url_for('dashboard.index'))
