"""Add notifications table

Revision ID: add_notifications_table
Revises: phase_3_flexible_chunk_system
Create Date: 2024-12-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_notifications_table'
down_revision: Union[str, None] = '7d5712ef7fd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notification_type enum
    notification_type_enum = postgresql.ENUM(
        'booking_confirmation',
        'booking_reminder_start',
        'booking_reminder_end',
        'checkin_available',
        'checkin_overdue',
        'booking_cancelled',
        'payment_confirmation',
        'booking_expired',
        'admin_no_show',
        'admin_system_issue',
        'admin_daily_report',
        'admin_maintenance',
        'admin_high_occupancy',
        name='notificationtype',
        create_type=False
    )
    notification_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create notification_priority enum
    notification_priority_enum = postgresql.ENUM(
        'low',
        'normal',
        'high',
        'critical',
        name='notificationpriority',
        create_type=False
    )
    notification_priority_enum.create(op.get_bind(), checkfirst=True)
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('booking_confirmation', 'booking_reminder_start', 'booking_reminder_end', 'checkin_available', 'checkin_overdue', 'booking_cancelled', 'payment_confirmation', 'booking_expired', 'admin_no_show', 'admin_system_issue', 'admin_daily_report', 'admin_maintenance', 'admin_high_occupancy', name='notificationtype'), nullable=False),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'critical', name='notificationpriority'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('is_sent', sa.Boolean(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('send_email', sa.Boolean(), nullable=True),
        sa.Column('send_sms', sa.Boolean(), nullable=True),
        sa.Column('send_push', sa.Boolean(), nullable=True),
        sa.Column('send_websocket', sa.Boolean(), nullable=True),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('notification_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ),
        sa.ForeignKeyConstraint(['lot_id'], ['parking_lots.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('idx_notifications_type', 'notifications', ['type'], unique=False)
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'], unique=False)
    op.create_index('idx_notifications_scheduled_at', 'notifications', ['scheduled_at'], unique=False)
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'], unique=False)
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read'], unique=False)
    op.create_index('idx_notifications_booking_id', 'notifications', ['booking_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_notifications_booking_id', table_name='notifications')
    op.drop_index('idx_notifications_user_read', table_name='notifications')
    op.drop_index('idx_notifications_created_at', table_name='notifications')
    op.drop_index('idx_notifications_scheduled_at', table_name='notifications')
    op.drop_index('idx_notifications_is_read', table_name='notifications')
    op.drop_index('idx_notifications_type', table_name='notifications')
    op.drop_index('idx_notifications_user_id', table_name='notifications')
    
    # Drop table
    op.drop_table('notifications')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS notificationpriority')
    op.execute('DROP TYPE IF EXISTS notificationtype')
