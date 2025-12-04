"""Dashboard route."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    """Main dashboard."""
    return render_template('dashboard.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard (redirect to index)."""
    return redirect(url_for('dashboard.index'))
