"""Add is_short_notice field to reservation table

Revision ID: c97a5390ecac
Revises: 088504aa5508
Create Date: 2025-12-09 20:37:58.760527

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c97a5390ecac'
down_revision = '088504aa5508'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_short_notice column to reservation table
    op.add_column('reservation', sa.Column('is_short_notice', sa.Boolean(), nullable=False, server_default='0'))
    
    # Add index on is_short_notice field for performance
    op.create_index('idx_reservation_short_notice', 'reservation', ['is_short_notice'])


def downgrade():
    # Remove index
    op.drop_index('idx_reservation_short_notice', table_name='reservation')
    
    # Remove is_short_notice column
    op.drop_column('reservation', 'is_short_notice')
