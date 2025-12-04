"""Member management routes."""
from flask import Blueprint

bp = Blueprint('members', __name__, url_prefix='/members')


@bp.route('/', methods=['GET'])
def list_members():
    """List members - to be implemented."""
    return "Members list"


@bp.route('/', methods=['POST'])
def create_member():
    """Create member - to be implemented."""
    return "Create member"


@bp.route('/<int:id>', methods=['PUT'])
def update_member(id):
    """Update member - to be implemented."""
    return f"Update member {id}"


@bp.route('/<int:id>', methods=['DELETE'])
def delete_member(id):
    """Delete member - to be implemented."""
    return f"Delete member {id}"


@bp.route('/<int:id>/favourites', methods=['POST'])
def add_favourite(id):
    """Add favourite - to be implemented."""
    return f"Add favourite for member {id}"


@bp.route('/<int:id>/favourites/<int:fav_id>', methods=['DELETE'])
def remove_favourite(id, fav_id):
    """Remove favourite - to be implemented."""
    return f"Remove favourite {fav_id} for member {id}"
