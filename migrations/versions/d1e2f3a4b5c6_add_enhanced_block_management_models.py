"""Add enhanced block management models

Revision ID: d1e2f3a4b5c6
Revises: c97a5390ecac
Create Date: 2025-01-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'c97a5390ecac'
branch_labels = None
depends_on = None


def upgrade():
    # Create block_reason table
    op.create_table('block_reason',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['member.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    with op.batch_alter_table('block_reason', schema=None) as batch_op:
        batch_op.create_index('idx_block_reason_active', ['is_active'], unique=False)
        batch_op.create_index('idx_block_reason_name', ['name'], unique=False)

    # Create block_series table
    op.create_table('block_series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('recurrence_pattern', sa.String(length=20), nullable=False),
        sa.Column('recurrence_days', sa.JSON(), nullable=True),
        sa.Column('reason_id', sa.Integer(), nullable=False),
        sa.Column('sub_reason', sa.String(length=255), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['member.id'], ),
        sa.ForeignKeyConstraint(['reason_id'], ['block_reason.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('block_series', schema=None) as batch_op:
        batch_op.create_index('idx_block_series_dates', ['start_date', 'end_date'], unique=False)
        batch_op.create_index('idx_block_series_reason', ['reason_id'], unique=False)

    # Create sub_reason_template table
    op.create_table('sub_reason_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reason_id', sa.Integer(), nullable=False),
        sa.Column('template_name', sa.String(length=100), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['member.id'], ),
        sa.ForeignKeyConstraint(['reason_id'], ['block_reason.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('sub_reason_template', schema=None) as batch_op:
        batch_op.create_index('idx_sub_reason_template_reason', ['reason_id'], unique=False)

    # Create block_template table
    op.create_table('block_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('court_selection', sa.JSON(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('reason_id', sa.Integer(), nullable=False),
        sa.Column('sub_reason', sa.String(length=255), nullable=True),
        sa.Column('recurrence_pattern', sa.String(length=20), nullable=True),
        sa.Column('recurrence_days', sa.JSON(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['member.id'], ),
        sa.ForeignKeyConstraint(['reason_id'], ['block_reason.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    with op.batch_alter_table('block_template', schema=None) as batch_op:
        batch_op.create_index('idx_block_template_name', ['name'], unique=False)
        batch_op.create_index('idx_block_template_reason', ['reason_id'], unique=False)

    # Create block_audit_log table
    op.create_table('block_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(length=20), nullable=False),
        sa.Column('block_id', sa.Integer(), nullable=True),
        sa.Column('series_id', sa.Integer(), nullable=True),
        sa.Column('operation_data', sa.JSON(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['member.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('block_audit_log', schema=None) as batch_op:
        batch_op.create_index('idx_block_audit_admin', ['admin_id'], unique=False)
        batch_op.create_index('idx_block_audit_operation', ['operation'], unique=False)
        batch_op.create_index('idx_block_audit_timestamp', ['timestamp'], unique=False)

    # Populate default block reasons
    op.execute("""
        INSERT INTO block_reason (name, is_active, created_by_id, created_at) 
        SELECT 'Maintenance', 1, 1, datetime('now') WHERE EXISTS (SELECT 1 FROM member WHERE id = 1)
    """)
    op.execute("""
        INSERT INTO block_reason (name, is_active, created_by_id, created_at) 
        SELECT 'Weather', 1, 1, datetime('now') WHERE EXISTS (SELECT 1 FROM member WHERE id = 1)
    """)
    op.execute("""
        INSERT INTO block_reason (name, is_active, created_by_id, created_at) 
        SELECT 'Tournament', 1, 1, datetime('now') WHERE EXISTS (SELECT 1 FROM member WHERE id = 1)
    """)
    op.execute("""
        INSERT INTO block_reason (name, is_active, created_by_id, created_at) 
        SELECT 'Championship', 1, 1, datetime('now') WHERE EXISTS (SELECT 1 FROM member WHERE id = 1)
    """)
    op.execute("""
        INSERT INTO block_reason (name, is_active, created_by_id, created_at) 
        SELECT 'Tennis Course', 1, 1, datetime('now') WHERE EXISTS (SELECT 1 FROM member WHERE id = 1)
    """)

    # Update block table - add new columns
    with op.batch_alter_table('block', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reason_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('sub_reason', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('series_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_modified', sa.Boolean(), nullable=False, server_default='0'))

    # Migrate existing block reasons to new structure
    op.execute("""
        UPDATE block SET reason_id = (
            SELECT id FROM block_reason WHERE 
            CASE 
                WHEN block.reason = 'rain' THEN block_reason.name = 'Weather'
                WHEN block.reason = 'maintenance' THEN block_reason.name = 'Maintenance'
                WHEN block.reason = 'tournament' THEN block_reason.name = 'Tournament'
                WHEN block.reason = 'championship' THEN block_reason.name = 'Championship'
                ELSE block_reason.name = 'Maintenance'
            END
            LIMIT 1
        )
    """)

    # Make reason_id not nullable after migration
    with op.batch_alter_table('block', schema=None) as batch_op:
        batch_op.alter_column('reason_id', nullable=False)
        batch_op.create_foreign_key('fk_block_reason_id', 'block_reason', ['reason_id'], ['id'])
        batch_op.create_foreign_key('fk_block_series_id', 'block_series', ['series_id'], ['id'], ondelete='CASCADE')
        batch_op.create_index('idx_block_reason', ['reason_id'], unique=False)
        batch_op.create_index('idx_block_series', ['series_id'], unique=False)

    # Drop old reason column after migration
    with op.batch_alter_table('block', schema=None) as batch_op:
        batch_op.drop_column('reason')


def downgrade():
    # Add back old reason column
    with op.batch_alter_table('block', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reason', sa.String(length=50), nullable=True))

    # Migrate reason_id back to reason string
    op.execute("""
        UPDATE block SET reason = (
            SELECT 
            CASE 
                WHEN block_reason.name = 'Weather' THEN 'rain'
                WHEN block_reason.name = 'Maintenance' THEN 'maintenance'
                WHEN block_reason.name = 'Tournament' THEN 'tournament'
                WHEN block_reason.name = 'Championship' THEN 'championship'
                ELSE 'maintenance'
            END
            FROM block_reason WHERE block_reason.id = block.reason_id
        )
    """)

    # Make reason not nullable and drop new columns
    with op.batch_alter_table('block', schema=None) as batch_op:
        batch_op.alter_column('reason', nullable=False)
        batch_op.drop_index('idx_block_series')
        batch_op.drop_index('idx_block_reason')
        batch_op.drop_constraint('fk_block_series_id', type_='foreignkey')
        batch_op.drop_constraint('fk_block_reason_id', type_='foreignkey')
        batch_op.drop_column('is_modified')
        batch_op.drop_column('series_id')
        batch_op.drop_column('sub_reason')
        batch_op.drop_column('reason_id')

    # Drop new tables
    with op.batch_alter_table('block_audit_log', schema=None) as batch_op:
        batch_op.drop_index('idx_block_audit_timestamp')
        batch_op.drop_index('idx_block_audit_operation')
        batch_op.drop_index('idx_block_audit_admin')
    op.drop_table('block_audit_log')

    with op.batch_alter_table('block_template', schema=None) as batch_op:
        batch_op.drop_index('idx_block_template_reason')
        batch_op.drop_index('idx_block_template_name')
    op.drop_table('block_template')

    with op.batch_alter_table('sub_reason_template', schema=None) as batch_op:
        batch_op.drop_index('idx_sub_reason_template_reason')
    op.drop_table('sub_reason_template')

    with op.batch_alter_table('block_series', schema=None) as batch_op:
        batch_op.drop_index('idx_block_series_reason')
        batch_op.drop_index('idx_block_series_dates')
    op.drop_table('block_series')

    with op.batch_alter_table('block_reason', schema=None) as batch_op:
        batch_op.drop_index('idx_block_reason_name')
        batch_op.drop_index('idx_block_reason_active')
    op.drop_table('block_reason')