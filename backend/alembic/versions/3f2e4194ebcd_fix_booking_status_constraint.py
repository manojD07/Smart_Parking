"""fix_booking_status_constraint

Revision ID: 3f2e4194ebcd
Revises: 2e3e4194ebcd
Create Date: 2025-09-16 22:22:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3f2e4194ebcd'
down_revision = '7d5712ef7fd8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint('check_booking_status', 'bookings', type_='check')
    
    # Create the new constraint with all booking status values
    op.create_check_constraint(
        'check_booking_status',
        'bookings',
        "status IN ('pending', 'confirmed', 'active', 'completed', 'cancelled', 'expired', 'no_show')"
    )


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint('check_booking_status', 'bookings', type_='check')
    
    # Restore the old constraint
    op.create_check_constraint(
        'check_booking_status',
        'bookings',
        "status IN ('active', 'completed', 'cancelled', 'expired', 'no_show')"
    )
