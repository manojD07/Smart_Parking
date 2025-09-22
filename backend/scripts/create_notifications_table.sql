-- Create notifications table manually
-- This is a fallback if Alembic migration fails

-- Create enums
DO $$ BEGIN
    CREATE TYPE notificationtype AS ENUM (
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
        'admin_high_occupancy'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notificationpriority AS ENUM (
        'low',
        'normal',
        'high',
        'critical'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    type notificationtype NOT NULL,
    priority notificationpriority DEFAULT 'normal',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    is_sent BOOLEAN DEFAULT FALSE,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    send_email BOOLEAN DEFAULT FALSE,
    send_sms BOOLEAN DEFAULT FALSE,
    send_push BOOLEAN DEFAULT FALSE,
    send_websocket BOOLEAN DEFAULT TRUE,
    booking_id UUID REFERENCES bookings(id),
    lot_id UUID REFERENCES parking_lots(id),
    celery_task_id VARCHAR(255),
    notification_metadata TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled_at ON notifications(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_booking_id ON notifications(booking_id);

-- Update alembic version to include this migration
INSERT INTO alembic_version (version_num) VALUES ('add_notifications_table') 
ON CONFLICT (version_num) DO NOTHING;
