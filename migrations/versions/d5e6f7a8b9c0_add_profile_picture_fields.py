"""Add profile picture fields to member

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-01-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # Add profile picture fields to member table
    op.add_column('member', sa.Column('has_profile_picture', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('member', sa.Column('profile_picture_version', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('member', 'profile_picture_version')
    op.drop_column('member', 'has_profile_picture')
