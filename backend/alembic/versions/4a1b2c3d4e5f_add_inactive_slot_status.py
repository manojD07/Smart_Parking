"""Add INACTIVE status to slot status enum

Revision ID: 4a1b2c3d4e5f
Revises: 3f2e4194ebcd
Create Date: 2025-09-18 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4a1b2c3d4e5f'
down_revision = '3f2e4194ebcd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add INACTIVE status to parking_slots status constraint."""
    # Drop existing constraint if it exists
    op.execute("""
        ALTER TABLE parking_slots 
        DROP CONSTRAINT IF EXISTS check_slot_status;
    """)
    
    # Add new constraint with INACTIVE status
    op.execute("""
        ALTER TABLE parking_slots 
        ADD CONSTRAINT check_slot_status 
        CHECK (status IN ('available', 'occupied', 'reserved', 'maintenance', 'inactive'));
    """)


def downgrade() -> None:
    """Remove INACTIVE status from parking_slots status constraint."""
    # Drop constraint with INACTIVE
    op.execute("""
        ALTER TABLE parking_slots 
        DROP CONSTRAINT IF EXISTS check_slot_status;
    """)
    
    # Restore original constraint without INACTIVE
    op.execute("""
        ALTER TABLE parking_slots 
        ADD CONSTRAINT check_slot_status 
        CHECK (status IN ('available', 'occupied', 'reserved', 'maintenance'));
    """)
