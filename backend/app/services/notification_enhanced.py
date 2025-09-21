"""Enhanced notification service for comprehensive notification management."""

from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
import json
import structlog

from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.booking import Booking
from app.models.user import User
from app.repositories.notification import NotificationRepository
from app.services.base import BaseService

logger = structlog.get_logger(__name__)


class NotificationService(BaseService[Notification, NotificationRepository]):
    """Enhanced service for handling all notification operations."""
    
    def __init__(self, session: AsyncSession):
        repository = NotificationRepository(session)
        super().__init__(repository)
        self.session = session
        self.logger = logger.bind(service="NotificationService")
    
    async def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.normal,
        scheduled_at: Optional[datetime] = None,
        booking_id: Optional[UUID] = None,
        lot_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **channels
    ) -> Notification:
        """Create a new notification."""
        try:
            # Convert metadata to JSON string if provided
            metadata_str = json.dumps(metadata) if metadata else None
            
            notification = await self.repository.create_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                scheduled_at=scheduled_at,
                booking_id=booking_id,
                lot_id=lot_id,
                metadata=metadata_str,
                **channels
            )
            
            # If not scheduled, send immediately
            if not scheduled_at:
                await self.send_notification(notification)
            
            return notification
            
        except Exception as e:
            self.logger.error("Failed to create notification", error=str(e))
            raise
    
    async def send_notification(self, notification: Notification) -> bool:
        """Send notification through enabled channels."""
        try:
            success = True
            
            # For Phase 1 & 2: Only WebSocket/UI notifications
            if notification.send_websocket:
                success &= await self._send_websocket_notification(notification)
            
            # Placeholder for future email/SMS integration
            if notification.send_email:
                self.logger.info("Email notification queued", notification_id=str(notification.id))
                # success &= await self._send_email_notification(notification)
            
            if notification.send_sms:
                self.logger.info("SMS notification queued", notification_id=str(notification.id))
                # success &= await self._send_sms_notification(notification)
            
            if notification.send_push:
                self.logger.info("Push notification queued", notification_id=str(notification.id))
                # success &= await self._send_push_notification(notification)
            
            # Mark as sent if successful
            if success:
                await self.repository.mark_as_sent(notification.id)
            
            return success
            
        except Exception as e:
            self.logger.error("Failed to send notification", error=str(e))
            return False
    
    async def _send_websocket_notification(self, notification: Notification) -> bool:
        """Send notification via WebSocket."""
        try:
            # Import here to avoid circular imports
            from app.websockets.manager import websocket_manager
            
            # Prepare notification data for WebSocket
            notification_data = {
                "id": str(notification.id),
                "type": notification.type.value,
                "priority": notification.priority.value,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
                "booking_id": str(notification.booking_id) if notification.booking_id else None,
                "lot_id": str(notification.lot_id) if notification.lot_id else None,
                "metadata": notification.notification_metadata
            }
            
            # Send via WebSocket manager
            await websocket_manager.send_user_notification(
                user_id=str(notification.user_id),
                notification_data=notification_data
            )
            
            self.logger.info(
                "WebSocket notification sent",
                notification_id=str(notification.id),
                user_id=str(notification.user_id)
            )
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to send WebSocket notification", error=str(e))
            return False
    
    async def get_user_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None
    ) -> List[Notification]:
        """Get notifications for a user."""
        return await self.repository.get_user_notifications(
            user_id=user_id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            notification_type=notification_type
        )
    
    async def get_notification_stats(self, user_id: UUID) -> Dict[str, int]:
        """Get notification statistics for a user."""
        return await self.repository.get_notification_stats(user_id)
    
    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read."""
        return await self.repository.mark_as_read(notification_id, user_id)
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        return await self.repository.mark_all_as_read(user_id)
    
    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """Delete a notification."""
        return await self.repository.delete_notification(notification_id, user_id)
    
    # Booking-specific notification methods
    
    async def send_booking_confirmation(self, booking: Booking) -> Notification:
        """Send booking confirmation notification."""
        try:
            title = "Booking Confirmed"
            message = f"Your parking booking for {booking.lot.name} has been confirmed. Booking ID: {booking.booking_reference}"
            
            return await self.create_notification(
                user_id=booking.user_id,
                notification_type=NotificationType.booking_confirmation,
                title=title,
                message=message,
                priority=NotificationPriority.normal,
                booking_id=booking.id,
                lot_id=booking.lot_id,
                metadata={
                    "booking_reference": booking.booking_reference,
                    "start_time": booking.start_time.isoformat(),
                    "end_time": booking.end_time.isoformat(),
                    "lot_name": booking.lot.name,
                    "total_amount": float(booking.total_amount)
                }
            )
            
        except Exception as e:
            self.logger.error("Failed to send booking confirmation", booking_id=str(booking.id), error=str(e))
            raise
    
    async def send_booking_reminder(
        self, 
        booking: Booking, 
        reminder_type: NotificationType,
        minutes_before: int
    ) -> Notification:
        """Send booking reminder notification."""
        try:
            titles = {
                NotificationType.checkin_available: "Check-in Available",
                NotificationType.booking_reminder_start: "Booking Starts Soon",
                NotificationType.booking_reminder_end: "Booking Ends Soon",
                NotificationType.checkin_overdue: "Check-in Overdue"
            }
            
            messages = {
                NotificationType.checkin_available: f"You can now check in for your parking booking at {booking.lot.name}. Check-in is available 15 minutes before your booking starts.",
                NotificationType.booking_reminder_start: f"Your parking booking at {booking.lot.name} starts in {minutes_before} minutes. Please check in soon.",
                NotificationType.booking_reminder_end: f"Your parking booking at {booking.lot.name} ends in {minutes_before} minutes. Please prepare to check out.",
                NotificationType.checkin_overdue: f"You haven't checked in for your booking at {booking.lot.name}. Your booking started {abs(minutes_before)} minutes ago."
            }
            
            priority = NotificationPriority.high if reminder_type == NotificationType.checkin_overdue else NotificationPriority.normal
            
            return await self.create_notification(
                user_id=booking.user_id,
                notification_type=reminder_type,
                title=titles[reminder_type],
                message=messages[reminder_type],
                priority=priority,
                booking_id=booking.id,
                lot_id=booking.lot_id,
                metadata={
                    "booking_reference": booking.booking_reference,
                    "minutes_before": minutes_before,
                    "lot_name": booking.lot.name,
                    "start_time": booking.start_time.isoformat(),
                    "end_time": booking.end_time.isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error("Failed to send booking reminder", booking_id=str(booking.id), error=str(e))
            raise
    
    async def send_booking_cancelled(self, booking: Booking, cancelled_by_admin: bool = False) -> Notification:
        """Send booking cancellation notification."""
        try:
            title = "Booking Cancelled"
            
            if cancelled_by_admin:
                message = f"Your booking at {booking.lot.name} has been cancelled by an administrator. You will receive a full refund."
                priority = NotificationPriority.high
            else:
                message = f"Your booking at {booking.lot.name} has been cancelled successfully. Refund will be processed shortly."
                priority = NotificationPriority.normal
            
            return await self.create_notification(
                user_id=booking.user_id,
                notification_type=NotificationType.booking_cancelled,
                title=title,
                message=message,
                priority=priority,
                booking_id=booking.id,
                lot_id=booking.lot_id,
                metadata={
                    "booking_reference": booking.booking_reference,
                    "cancelled_by_admin": cancelled_by_admin,
                    "lot_name": booking.lot.name,
                    "refund_amount": float(booking.total_amount)
                }
            )
            
        except Exception as e:
            self.logger.error("Failed to send booking cancellation", booking_id=str(booking.id), error=str(e))
            raise
    
    async def send_payment_confirmation(self, booking: Booking) -> Notification:
        """Send payment confirmation notification."""
        try:
            title = "Payment Confirmed"
            message = f"Payment of ${booking.total_amount:.2f} for your booking at {booking.lot.name} has been processed successfully."
            
            return await self.create_notification(
                user_id=booking.user_id,
                notification_type=NotificationType.payment_confirmation,
                title=title,
                message=message,
                priority=NotificationPriority.normal,
                booking_id=booking.id,
                lot_id=booking.lot_id,
                metadata={
                    "booking_reference": booking.booking_reference,
                    "amount": float(booking.total_amount),
                    "lot_name": booking.lot.name,
                    "payment_time": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error("Failed to send payment confirmation", booking_id=str(booking.id), error=str(e))
            raise
    
    async def cancel_scheduled_notifications(self, booking_id: UUID) -> int:
        """Cancel all scheduled notifications for a booking."""
        return await self.repository.cancel_scheduled_notifications(booking_id)
    
    # Placeholder methods for future email/SMS integration
    
    async def _send_email_notification(self, notification: Notification) -> bool:
        """Send email notification (placeholder for Phase 3)."""
        self.logger.info("Email notification would be sent here", notification_id=str(notification.id))
        return True
    
    async def _send_sms_notification(self, notification: Notification) -> bool:
        """Send SMS notification (placeholder for Phase 3)."""
        self.logger.info("SMS notification would be sent here", notification_id=str(notification.id))
        return True
    
    async def _send_push_notification(self, notification: Notification) -> bool:
        """Send push notification (placeholder for Phase 3)."""
        self.logger.info("Push notification would be sent here", notification_id=str(notification.id))
        return True
