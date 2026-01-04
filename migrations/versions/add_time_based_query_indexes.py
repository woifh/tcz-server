"""Add composite indexes for time-based active booking session queries

Revision ID: f1g2h3i4j5k6
Revises: e2f3g4h5i6j7
Create Date: 2026-01-04 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1g2h3i4j5k6'
down_revision = 'e2f3g4h5i6j7'
branch_labels = None
depends_on = None


def upgrade():
    """Add composite indexes for optimizing time-based active booking session queries."""
    
    # Composite index for active reservation lookup by member and time-based filtering
    # This optimizes queries like: get_member_active_booking_sessions()
    op.create_index(
        'idx_reservation_active_lookup',
        'reservation',
        ['booked_for_id', 'status', 'date', 'end_time'],
        unique=False
    )
    
    # Composite index for short notice booking lookup with time-based filtering
    # This optimizes queries like: get_member_active_short_notice_bookings()
    op.create_index(
        'idx_reservation_short_notice_lookup',
        'reservation',
        ['booked_for_id', 'status', 'is_short_notice', 'date', 'end_time'],
        unique=False
    )
    
    # Composite index for booked_by queries (covers both booked_for and booked_by scenarios)
    op.create_index(
        'idx_reservation_booked_by_active_lookup',
        'reservation',
        ['booked_by_id', 'status', 'date', 'end_time'],
        unique=False
    )


def downgrade():
    """Remove the composite indexes."""
    
    op.drop_index('idx_reservation_booked_by_active_lookup', table_name='reservation')
    op.drop_index('idx_reservation_short_notice_lookup', table_name='reservation')
    op.drop_index('idx_reservation_active_lookup', table_name='reservation')