"""Dashboard route."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index():
    """Root route - redirect based on authentication status."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    else:
        return redirect(url_for('dashboard.anonymous_overview'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - main authenticated dashboard."""
    return render_template('dashboard.html')


@bp.route('/overview')
def anonymous_overview():
    """Anonymous court overview for non-authenticated users."""
    return render_template('anonymous_overview.html')
