"""Remove unique_booking constraint and add partial unique index for active reservations

Revision ID: b1c2d3e4f5g6
Revises: a38dd0c89b2f
Create Date: 2025-12-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5g6'
down_revision = 'a38dd0c89b2f'
branch_labels = None
depends_on = None


def upgrade():
    """Remove the unique_booking constraint that blocks cancelled reservations.
    
    MySQL doesn't support partial indexes, so we remove the constraint entirely.
    The application logic will handle preventing duplicate active reservations.
    """
    # Drop the unique constraint
    with op.batch_alter_table('reservation', schema=None) as batch_op:
        batch_op.drop_constraint('unique_booking', type_='unique')


def downgrade():
    """Restore the unique_booking constraint."""
    with op.batch_alter_table('reservation', schema=None) as batch_op:
        batch_op.create_unique_constraint('unique_booking', ['court_id', 'date', 'start_time'])
