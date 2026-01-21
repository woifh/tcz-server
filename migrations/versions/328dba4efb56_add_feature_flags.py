"""Add feature flags

Revision ID: 328dba4efb56
Revises: e6f7a8b9c0d1
Create Date: 2026-01-21 19:26:22.945733

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '328dba4efb56'
down_revision = 'e6f7a8b9c0d1'
branch_labels = None
depends_on = None


def upgrade():
    # Create feature_flag table
    op.create_table('feature_flag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('allowed_roles', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('feature_flag', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_feature_flag_key'), ['key'], unique=True)

    # Create feature_flag_audit_log table
    op.create_table('feature_flag_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flag_id', sa.Integer(), nullable=False),
        sa.Column('flag_key', sa.String(length=50), nullable=False),
        sa.Column('operation', sa.String(length=20), nullable=False),
        sa.Column('operation_data', sa.JSON(), nullable=True),
        sa.Column('performed_by_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['performed_by_id'], ['member.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('feature_flag_audit_log', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_feature_flag_audit_log_timestamp'), ['timestamp'], unique=False)

    # Seed initial help_center flag (admin-only during review)
    # Using SQLAlchemy for database-agnostic insert
    from sqlalchemy import text
    from sqlalchemy.engine import Engine

    bind = op.get_bind()
    is_mysql = 'mysql' in bind.dialect.name.lower()

    if is_mysql:
        # MySQL: use backticks for reserved word 'key' and NOW() for datetime
        op.execute(text(
            """
            INSERT INTO feature_flag (`key`, name, description, is_enabled, allowed_roles, created_at, updated_at)
            SELECT 'help_center', 'Hilfe-Center', 'Hilfe-Seiten für Mitglieder', 1, '["administrator"]', NOW(), NOW()
            FROM DUAL
            WHERE NOT EXISTS (SELECT 1 FROM feature_flag WHERE `key` = 'help_center')
            """
        ))
    else:
        # SQLite
        op.execute(text(
            """
            INSERT INTO feature_flag (key, name, description, is_enabled, allowed_roles, created_at, updated_at)
            SELECT 'help_center', 'Hilfe-Center', 'Hilfe-Seiten für Mitglieder', 1, '["administrator"]', datetime('now'), datetime('now')
            WHERE NOT EXISTS (SELECT 1 FROM feature_flag WHERE key = 'help_center')
            """
        ))


def downgrade():
    with op.batch_alter_table('feature_flag_audit_log', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_feature_flag_audit_log_timestamp'))

    op.drop_table('feature_flag_audit_log')

    with op.batch_alter_table('feature_flag', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_feature_flag_key'))

    op.drop_table('feature_flag')
