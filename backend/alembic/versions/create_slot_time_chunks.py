"""Create slot_time_chunks table for hourly booking system

Revision ID: slot_time_chunks_001
Revises: 3f2e4194ebcd
Create Date: 2025-09-17 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'slot_time_chunks_001'
down_revision = '3f2e4194ebcd'
branch_labels = None
depends_on = None


def upgrade():
    # Create slot_time_chunks table
    op.create_table(
        'slot_time_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('slot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('parking_slots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='available'),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reserved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reserved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        # Constraints
        sa.CheckConstraint("status IN ('available', 'booked', 'temp_reserved')", name='check_chunk_status'),
        sa.CheckConstraint('end_time > start_time', name='check_chunk_time_order'),
    )
    
    # Indexes for performance
    op.create_index('idx_slot_chunks_availability', 'slot_time_chunks', ['slot_id', 'start_time', 'end_time', 'status'])
    op.create_index('idx_slot_chunks_booking', 'slot_time_chunks', ['booking_id'])
    op.create_index('idx_slot_chunks_reserved_by', 'slot_time_chunks', ['reserved_by', 'reserved_at'])
    
    # Prevent overlapping chunks for same slot (business rule)
    op.create_index(
        'idx_no_overlapping_chunks', 
        'slot_time_chunks', 
        ['slot_id', 'start_time', 'end_time'],
        unique=True,
        postgresql_where=sa.text("status IN ('booked', 'temp_reserved')")
    )
    
    # Add session tracking to bookings table
    op.add_column('bookings', sa.Column('session_id', sa.String(50), nullable=True))
    op.add_column('bookings', sa.Column('reserved_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('bookings', sa.Column('chunk_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=False))
    
    # Index for session-based queries
    op.create_index('idx_bookings_session', 'bookings', ['session_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_bookings_session')
    op.drop_index('idx_no_overlapping_chunks')
    op.drop_index('idx_slot_chunks_reserved_by')
    op.drop_index('idx_slot_chunks_booking')
    op.drop_index('idx_slot_chunks_availability')
    
    # Drop columns from bookings
    op.drop_column('bookings', 'chunk_ids')
    op.drop_column('bookings', 'reserved_until')
    op.drop_column('bookings', 'session_id')
    
    # Drop table
    op.drop_table('slot_time_chunks')
