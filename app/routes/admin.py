"""Admin routes for blocks and overrides."""
from flask import Blueprint

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/blocks', methods=['GET'])
def list_blocks():
    """List blocks - to be implemented."""
    return "Blocks list"


@bp.route('/blocks', methods=['POST'])
def create_block():
    """Create block - to be implemented."""
    return "Create block"


@bp.route('/blocks/<int:id>', methods=['DELETE'])
def delete_block(id):
    """Delete block - to be implemented."""
    return f"Delete block {id}"


@bp.route('/reservations/<int:id>', methods=['DELETE'])
def admin_delete_reservation(id):
    """Admin delete reservation - to be implemented."""
    return f"Admin delete reservation {id}"
