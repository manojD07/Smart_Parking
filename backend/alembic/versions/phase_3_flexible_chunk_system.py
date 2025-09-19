"""Phase 3: Flexible chunk system with smart duration support

Revision ID: phase_3_flexible_chunk_system
Revises: 4a1b2c3d4e5f_add_inactive_slot_status
Create Date: 2025-09-19 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase_3_flexible_chunk_system'
down_revision = '4a1b2c3d4e5f_add_inactive_slot_status'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade to flexible chunk system."""
    
    # Drop existing restrictive constraints
    print("Dropping existing 30-minute chunk constraints...")
    op.drop_constraint('check_start_time_30_minute_boundary', 'slot_time_chunks', type_='check')
    op.drop_constraint('check_end_time_30_minute_boundary', 'slot_time_chunks', type_='check')
    op.drop_constraint('check_30_minute_duration', 'slot_time_chunks', type_='check')
    
    # Add new smart chunk metadata columns
    print("Adding smart chunk metadata columns...")
    op.add_column('slot_time_chunks', sa.Column('chunk_size_minutes', sa.Integer(), nullable=False, server_default='30'))
    op.add_column('slot_time_chunks', sa.Column('demand_level', sa.String(length=10), nullable=False, server_default='medium'))
    op.add_column('slot_time_chunks', sa.Column('generation_strategy', sa.String(length=20), nullable=False, server_default='auto'))
    
    # Add new flexible constraints
    print("Adding flexible chunk constraints...")
    
    # 1-minute precision constraints
    op.create_check_constraint(
        'check_minute_precision',
        'slot_time_chunks',
        'EXTRACT(second FROM start_time) = 0 AND EXTRACT(microsecond FROM start_time) = 0'
    )
    op.create_check_constraint(
        'check_minute_precision_end',
        'slot_time_chunks',
        'EXTRACT(second FROM end_time) = 0 AND EXTRACT(microsecond FROM end_time) = 0'
    )
    
    # Valid chunk sizes constraint
    op.create_check_constraint(
        'check_valid_chunk_sizes',
        'slot_time_chunks',
        'chunk_size_minutes IN (1, 5, 10, 15, 30, 60, 120, 240)'
    )
    
    # Chunk duration consistency constraint
    op.create_check_constraint(
        'check_chunk_duration_consistency',
        'slot_time_chunks',
        "(end_time - start_time) = (chunk_size_minutes || ' minutes')::INTERVAL"
    )
    
    # Chunk size range constraint
    op.create_check_constraint(
        'check_chunk_size_range',
        'slot_time_chunks',
        'chunk_size_minutes >= 1 AND chunk_size_minutes <= 240'
    )
    
    # Demand level constraint
    op.create_check_constraint(
        'check_demand_level',
        'slot_time_chunks',
        "demand_level IN ('low', 'medium', 'high', 'peak')"
    )
    
    # Generation strategy constraint
    op.create_check_constraint(
        'check_generation_strategy',
        'slot_time_chunks',
        "generation_strategy IN ('auto', 'manual', 'demand_based')"
    )
    
    # Add new performance indexes
    print("Adding performance indexes for smart chunks...")
    op.create_index(
        'idx_slot_chunks_metadata',
        'slot_time_chunks',
        ['chunk_size_minutes', 'demand_level', 'generation_strategy']
    )
    op.create_index(
        'idx_slot_chunks_time_range',
        'slot_time_chunks',
        ['start_time', 'end_time']
    )
    
    # Update existing chunks to have metadata
    print("Updating existing chunks with metadata...")
    op.execute("""
        UPDATE slot_time_chunks 
        SET 
            chunk_size_minutes = 30,
            demand_level = 'medium',
            generation_strategy = 'auto'
        WHERE chunk_size_minutes IS NULL
    """)
    
    # Remove server defaults after data update
    op.alter_column('slot_time_chunks', 'chunk_size_minutes', server_default=None)
    op.alter_column('slot_time_chunks', 'demand_level', server_default=None)
    op.alter_column('slot_time_chunks', 'generation_strategy', server_default=None)
    
    print("Phase 3 flexible chunk system migration completed successfully!")


def downgrade() -> None:
    """Downgrade from flexible chunk system back to 30-minute chunks."""
    
    print("WARNING: Downgrading will lose smart chunk metadata and revert to 30-minute chunks only!")
    
    # Remove new indexes
    op.drop_index('idx_slot_chunks_metadata', table_name='slot_time_chunks')
    op.drop_index('idx_slot_chunks_time_range', table_name='slot_time_chunks')
    
    # Remove new constraints
    op.drop_constraint('check_minute_precision', 'slot_time_chunks', type_='check')
    op.drop_constraint('check_minute_precision_end', 'slot_time_chunks', type_='check')
    op.drop_constraint('check_valid_chunk_sizes', 'slot_time_chunks', type_='check')
    op.drop_constraint('check_chunk_duration_consistency', 'slot_time_chunks', type_='check')
    op.drop_constraint('check_chunk_size_range', 'slot_time_chunks', type_='check')
    op.drop_constraint('check_demand_level', 'slot_time_chunks', type_='check')
    op.drop_constraint('check_generation_strategy', 'slot_time_chunks', type_='check')
    
    # Remove new columns
    op.drop_column('slot_time_chunks', 'generation_strategy')
    op.drop_column('slot_time_chunks', 'demand_level')
    op.drop_column('slot_time_chunks', 'chunk_size_minutes')
    
    # Restore original 30-minute constraints
    op.create_check_constraint(
        'check_start_time_30_minute_boundary',
        'slot_time_chunks',
        'EXTRACT(minute FROM start_time) IN (0, 30)'
    )
    op.create_check_constraint(
        'check_end_time_30_minute_boundary',
        'slot_time_chunks',
        'EXTRACT(minute FROM end_time) IN (0, 30)'
    )
    op.create_check_constraint(
        'check_30_minute_duration',
        'slot_time_chunks',
        "end_time - start_time = INTERVAL '30 minutes'"
    )
    
    print("Downgrade to 30-minute chunk system completed.")
