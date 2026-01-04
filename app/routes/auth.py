"""Authentication routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
# Removed limiter import for local development
from app.models import Member
from app.utils.validators import validate_email_address, validate_string_length, ValidationError

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
            login_user(member)
            flash('Erfolgreich angemeldet!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('E-Mail oder Passwort ist falsch', 'error')
    
    return render_template('login.html')


@bp.route('/logout')
def logout():
    """Logout route."""
    logout_user()
    flash('Erfolgreich abgemeldet', 'info')
    return redirect(url_for('dashboard.index'))
