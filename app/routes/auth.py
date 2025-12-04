"""Authentication routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.models import Member

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
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
    return redirect(url_for('auth.login'))
