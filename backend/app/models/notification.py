"""Notification models for the Smart Parking System."""

from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.base import BaseModel


class NotificationType(enum.Enum):
    """Types of notifications in the system."""
    booking_confirmation = "booking_confirmation"
    booking_reminder_start = "booking_reminder_start"
    booking_reminder_end = "booking_reminder_end"
    checkin_available = "checkin_available"
    checkin_reminder = "checkin_reminder"  # 5 min before start
    checkout_reminder = "checkout_reminder"  # 5 min before end
    checkin_overdue = "checkin_overdue"
    booking_cancelled = "booking_cancelled"
    payment_confirmation = "payment_confirmation"
    booking_expired = "booking_expired"
    admin_no_show = "admin_no_show"
    admin_system_issue = "admin_system_issue"
    admin_daily_report = "admin_daily_report"
    admin_maintenance = "admin_maintenance"
    admin_high_occupancy = "admin_high_occupancy"


class NotificationPriority(enum.Enum):
    """Priority levels for notifications."""
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class Notification(BaseModel):
    """User notification model."""
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.normal)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status tracking
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    
    # Timing
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Notification channels (for future use)
    send_email = Column(Boolean, default=False)  # UI only for now
    send_sms = Column(Boolean, default=False)    # UI only for now
    send_push = Column(Boolean, default=False)   # UI only for now
    send_websocket = Column(Boolean, default=True)  # Always enabled for UI
    
    # Related entities
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=True)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("parking_lots.id"), nullable=True)
    
    # Celery task tracking
    celery_task_id = Column(String(255), nullable=True)
    
    # Additional metadata
    notification_metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    booking = relationship("Booking", back_populates="notifications")
    lot = relationship("ParkingLot")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, user_id={self.user_id}, is_read={self.is_read})>"
    
    def to_dict(self):
        """Convert notification to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "is_sent": self.is_sent,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "booking_id": str(self.booking_id) if self.booking_id else None,
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "metadata": self.notification_metadata
        }
