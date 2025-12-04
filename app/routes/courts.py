"""Court and availability routes."""
from flask import Blueprint

bp = Blueprint('courts', __name__, url_prefix='/courts')


@bp.route('/', methods=['GET'])
def list_courts():
    """List courts - to be implemented."""
    return "Courts list"


@bp.route('/availability', methods=['GET'])
def get_availability():
    """Get court availability - to be implemented."""
    return "Court availability"
