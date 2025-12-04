"""Dashboard route."""
from flask import Blueprint

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index():
    """Main dashboard - to be implemented."""
    return "Dashboard"


@bp.route('/dashboard')
def dashboard():
    """User dashboard - to be implemented."""
    return "User Dashboard"
