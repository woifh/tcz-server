"""add_address_and_phone_to_member

Revision ID: 90886bac5240
Revises: 2468f05ebf4f
Create Date: 2026-01-07 18:57:57.782001

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90886bac5240'
down_revision = '2468f05ebf4f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('member', schema=None) as batch_op:
        batch_op.add_column(sa.Column('street', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('city', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('zip_code', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('member', schema=None) as batch_op:
        batch_op.drop_column('phone')
        batch_op.drop_column('zip_code')
        batch_op.drop_column('city')
        batch_op.drop_column('street')
