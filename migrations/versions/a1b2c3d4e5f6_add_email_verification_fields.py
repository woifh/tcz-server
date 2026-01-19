"""Add email verification fields to Member

Revision ID: a1b2c3d4e5f6
Revises: 2696aa995541
Create Date: 2026-01-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '2696aa995541'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('member', schema=None) as batch_op:
        # Add email_verified with default False (existing members start unverified)
        batch_op.add_column(sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('email_verified_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('member', schema=None) as batch_op:
        batch_op.drop_column('email_verified_at')
        batch_op.drop_column('email_verified')
