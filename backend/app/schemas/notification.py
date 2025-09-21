"""Notification schemas for API requests and responses."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.notification import NotificationType, NotificationPriority


class NotificationBase(BaseModel):
    """Base notification schema."""
    title: str = Field(..., description="Notification title", max_length=255)
    message: str = Field(..., description="Notification message")
    type: NotificationType = Field(..., description="Type of notification")
    priority: NotificationPriority = Field(NotificationPriority.normal, description="Priority level")
    scheduled_at: Optional[datetime] = Field(None, description="When to send the notification")
    booking_id: Optional[UUID] = Field(None, description="Related booking ID")
    lot_id: Optional[UUID] = Field(None, description="Related parking lot ID")
    metadata: Optional[str] = Field(None, description="Additional metadata as JSON string")


class NotificationCreate(NotificationBase):
    """Schema for creating notifications."""
    user_id: UUID = Field(..., description="User ID to send notification to")
    send_email: bool = Field(False, description="Send via email")
    send_sms: bool = Field(False, description="Send via SMS")
    send_push: bool = Field(False, description="Send via push notification")
    send_websocket: bool = Field(True, description="Send via WebSocket")


class NotificationUpdate(BaseModel):
    """Schema for updating notifications."""
    is_read: Optional[bool] = Field(None, description="Mark as read/unread")
    read_at: Optional[datetime] = Field(None, description="When notification was read")


class NotificationResponse(NotificationBase):
    """Schema for notification API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Notification ID")
    user_id: UUID = Field(..., description="User ID")
    is_read: bool = Field(..., description="Whether notification has been read")
    is_sent: bool = Field(..., description="Whether notification has been sent")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    read_at: Optional[datetime] = Field(None, description="When notification was read")
    created_at: datetime = Field(..., description="When notification was created")
    updated_at: datetime = Field(..., description="When notification was last updated")
    celery_task_id: Optional[str] = Field(None, description="Celery task ID for scheduled notifications")


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list."""
    notifications: List[NotificationResponse] = Field(..., description="List of notifications")
    total: int = Field(..., description="Total number of notifications")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics."""
    total_notifications: int = Field(..., description="Total notifications")
    unread_count: int = Field(..., description="Number of unread notifications")
    read_count: int = Field(..., description="Number of read notifications")
    today_count: int = Field(..., description="Notifications received today")
    this_week_count: int = Field(..., description="Notifications received this week")


class MarkAllReadRequest(BaseModel):
    """Schema for marking all notifications as read."""
    user_id: Optional[UUID] = Field(None, description="User ID (optional, will use current user if not provided)")


class BulkNotificationAction(BaseModel):
    """Schema for bulk notification actions."""
    notification_ids: List[UUID] = Field(..., description="List of notification IDs")
    action: str = Field(..., description="Action to perform: 'read', 'unread', 'delete'")


class NotificationPreferences(BaseModel):
    """Schema for user notification preferences."""
    booking_confirmations: bool = Field(True, description="Receive booking confirmation notifications")
    booking_reminders: bool = Field(True, description="Receive booking reminder notifications")
    checkin_alerts: bool = Field(True, description="Receive check-in related notifications")
    payment_confirmations: bool = Field(True, description="Receive payment confirmation notifications")
    admin_alerts: bool = Field(True, description="Receive admin alerts (for admin users)")
    email_enabled: bool = Field(False, description="Enable email notifications")
    sms_enabled: bool = Field(False, description="Enable SMS notifications")
    push_enabled: bool = Field(False, description="Enable push notifications")
    websocket_enabled: bool = Field(True, description="Enable real-time notifications")


class WebSocketNotificationPayload(BaseModel):
    """Schema for WebSocket notification payload."""
    event_type: str = Field("user_notification", description="WebSocket event type")
    notification: NotificationResponse = Field(..., description="Notification data")
    user_id: UUID = Field(..., description="Target user ID")
    timestamp: datetime = Field(..., description="Event timestamp")
