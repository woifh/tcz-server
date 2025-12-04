"""Reservation routes."""
from flask import Blueprint

bp = Blueprint('reservations', __name__, url_prefix='/reservations')


@bp.route('/', methods=['GET'])
def list_reservations():
    """List reservations - to be implemented."""
    return "Reservations list"


@bp.route('/', methods=['POST'])
def create_reservation():
    """Create reservation - to be implemented."""
    return "Create reservation"


@bp.route('/<int:id>', methods=['PUT'])
def update_reservation(id):
    """Update reservation - to be implemented."""
    return f"Update reservation {id}"


@bp.route('/<int:id>', methods=['DELETE'])
def delete_reservation(id):
    """Delete reservation - to be implemented."""
    return f"Delete reservation {id}"
