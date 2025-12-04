"""Authentication routes."""
from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route - to be implemented."""
    return "Login page"


@bp.route('/logout')
def logout():
    """Logout route - to be implemented."""
    return "Logout"
