"""Notification scheduler service for booking lifecycle notifications."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.booking import Booking
from app.models.notification import NotificationType, NotificationPriority
from app.services.notification_enhanced import NotificationService
from app.tasks.booking_tasks import send_scheduled_notification

logger = structlog.get_logger(__name__)


class NotificationScheduler:
    """Service for scheduling booking-related notifications."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService(session)
        self.logger = logger.bind(service="NotificationScheduler")
    
    async def schedule_booking_notifications(self, booking: Booking) -> List[str]:
        """Schedule all notifications for a booking lifecycle."""
        try:
            scheduled_tasks = []
            now = datetime.now(timezone.utc)
            
            self.logger.info(
                "Scheduling booking notifications",
                booking_id=str(booking.id),
                start_time=booking.start_time.isoformat(),
                end_time=booking.end_time.isoformat()
            )
            
            # 1. Immediate confirmation notification
            await self.notification_service.send_booking_confirmation(booking)
            
            # 2. Check-in available (15 minutes before start)
            checkin_time = booking.start_time - timedelta(minutes=15)
            if checkin_time > now:
                notification = await self.notification_service.create_notification(
                    user_id=booking.user_id,
                    notification_type=NotificationType.checkin_available,
                    title="Check-in Available",
                    message=f"You can now check in for your parking booking at {booking.lot.name}.",
                    priority=NotificationPriority.normal,
                    scheduled_at=checkin_time,
                    booking_id=booking.id,
                    lot_id=booking.lot_id,
                    metadata={
                        "booking_reference": booking.booking_reference,
                        "lot_name": booking.lot.name,
                        "minutes_before": 15
                    }
                )
                
                # Schedule Celery task
                task = send_scheduled_notification.apply_async(
                    args=[str(notification.id)],
                    eta=checkin_time
                )
                scheduled_tasks.append(task.id)
                
                # Update notification with task ID
                await self.notification_service.repository.session.execute(
                    f"UPDATE notifications SET celery_task_id = '{task.id}' WHERE id = '{notification.id}'"
                )
                await self.notification_service.repository.session.commit()
            
            # 3. Check-in reminder (5 minutes before start)
            checkin_reminder_time = booking.start_time - timedelta(minutes=5)
            if checkin_reminder_time > now:
                notification = await self.notification_service.create_notification(
                    user_id=booking.user_id,
                    notification_type=NotificationType.checkin_reminder,
                    title="Check-in Reminder",
                    message=f"Your parking booking at {booking.lot.name} starts in 5 minutes. Please check in now to secure your spot.",
                    priority=NotificationPriority.high,
                    scheduled_at=checkin_reminder_time,
                    booking_id=booking.id,
                    lot_id=booking.lot_id,
                    metadata={
                        "booking_reference": booking.booking_reference,
                        "lot_name": booking.lot.name,
                        "minutes_before": 5,
                        "reminder_type": "checkin"
                    }
                )
                
                task = send_scheduled_notification.apply_async(
                    args=[str(notification.id)],
                    eta=checkin_reminder_time
                )
                scheduled_tasks.append(task.id)
                
                # Update notification with task ID
                await self.notification_service.repository.session.execute(
                    f"UPDATE notifications SET celery_task_id = '{task.id}' WHERE id = '{notification.id}'"
                )
                await self.notification_service.repository.session.commit()
            
            # 4. Check-out reminder (5 minutes before end)
            checkout_reminder_time = booking.end_time - timedelta(minutes=5)
            if checkout_reminder_time > now:
                notification = await self.notification_service.create_notification(
                    user_id=booking.user_id,
                    notification_type=NotificationType.checkout_reminder,
                    title="Check-out Reminder",
                    message=f"Your parking booking at {booking.lot.name} ends in 5 minutes. Please check out soon to avoid overstay charges.",
                    priority=NotificationPriority.high,
                    scheduled_at=checkout_reminder_time,
                    booking_id=booking.id,
                    lot_id=booking.lot_id,
                    metadata={
                        "booking_reference": booking.booking_reference,
                        "lot_name": booking.lot.name,
                        "minutes_before": 5,
                        "reminder_type": "checkout"
                    }
                )
                
                task = send_scheduled_notification.apply_async(
                    args=[str(notification.id)],
                    eta=checkout_reminder_time
                )
                scheduled_tasks.append(task.id)
                
                # Update notification with task ID
                await self.notification_service.repository.session.execute(
                    f"UPDATE notifications SET celery_task_id = '{task.id}' WHERE id = '{notification.id}'"
                )
                await self.notification_service.repository.session.commit()
            
            # 5. Check-in overdue (10 minutes after start)
            overdue_time = booking.start_time + timedelta(minutes=10)
            if overdue_time > now:
                notification = await self.notification_service.create_notification(
                    user_id=booking.user_id,
                    notification_type=NotificationType.checkin_overdue,
                    title="Check-in Overdue",
                    message=f"You haven't checked in for your booking at {booking.lot.name}. Please check in soon.",
                    priority=NotificationPriority.critical,
                    scheduled_at=overdue_time,
                    booking_id=booking.id,
                    lot_id=booking.lot_id,
                    metadata={
                        "booking_reference": booking.booking_reference,
                        "lot_name": booking.lot.name,
                        "minutes_after": 10
                    }
                )
                
                task = send_scheduled_notification.apply_async(
                    args=[str(notification.id)],
                    eta=overdue_time
                )
                scheduled_tasks.append(task.id)
                
                # Update notification with task ID
                await self.notification_service.repository.session.execute(
                    f"UPDATE notifications SET celery_task_id = '{task.id}' WHERE id = '{notification.id}'"
                )
                await self.notification_service.repository.session.commit()
            
            self.logger.info(
                "Scheduled booking notifications",
                booking_id=str(booking.id),
                scheduled_count=len(scheduled_tasks),
                task_ids=scheduled_tasks
            )
            
            return scheduled_tasks
            
        except Exception as e:
            self.logger.error("Failed to schedule booking notifications", booking_id=str(booking.id), error=str(e))
            raise
    
    async def cancel_booking_notifications(self, booking_id: UUID) -> int:
        """Cancel all scheduled notifications for a booking."""
        try:
            # Get all scheduled notifications for this booking
            notifications = await self.notification_service.repository.get_notifications_by_booking(booking_id)
            
            cancelled_count = 0
            
            for notification in notifications:
                if notification.celery_task_id and not notification.is_sent:
                    try:
                        # Cancel the Celery task
                        from app.tasks.celery_app import celery_app
                        celery_app.control.revoke(notification.celery_task_id, terminate=True)
                        
                        self.logger.info(
                            "Cancelled Celery task",
                            task_id=notification.celery_task_id,
                            notification_id=str(notification.id)
                        )
                        
                        cancelled_count += 1
                        
                    except Exception as e:
                        self.logger.warning(
                            "Failed to cancel Celery task",
                            task_id=notification.celery_task_id,
                            error=str(e)
                        )
            
            # Cancel scheduled notifications in database
            db_cancelled = await self.notification_service.cancel_scheduled_notifications(booking_id)
            
            self.logger.info(
                "Cancelled booking notifications",
                booking_id=str(booking_id),
                celery_cancelled=cancelled_count,
                db_cancelled=db_cancelled
            )
            
            return max(cancelled_count, db_cancelled)
            
        except Exception as e:
            self.logger.error("Failed to cancel booking notifications", booking_id=str(booking_id), error=str(e))
            raise
    
    async def schedule_payment_confirmation(self, booking: Booking) -> None:
        """Send immediate payment confirmation notification."""
        try:
            await self.notification_service.send_payment_confirmation(booking)
            
            self.logger.info(
                "Sent payment confirmation",
                booking_id=str(booking.id),
                amount=float(booking.total_amount)
            )
            
        except Exception as e:
            self.logger.error("Failed to send payment confirmation", booking_id=str(booking.id), error=str(e))
            raise
    
    async def schedule_booking_cancellation(self, booking: Booking, cancelled_by_admin: bool = False) -> None:
        """Send booking cancellation notification and cancel future notifications."""
        try:
            # Send cancellation notification
            await self.notification_service.send_booking_cancelled(booking, cancelled_by_admin)
            
            # Cancel all future scheduled notifications for this booking
            await self.cancel_booking_notifications(booking.id)
            
            self.logger.info(
                "Processed booking cancellation notifications",
                booking_id=str(booking.id),
                cancelled_by_admin=cancelled_by_admin
            )
            
        except Exception as e:
            self.logger.error("Failed to process booking cancellation", booking_id=str(booking.id), error=str(e))
            raise
    
    async def send_admin_no_show_alert(self, booking: Booking) -> None:
        """Send no-show alert to admin users."""
        try:
            # Get admin users (this would need to be implemented)
            # For now, we'll just log it
            self.logger.warning(
                "No-show detected",
                booking_id=str(booking.id),
                user_id=str(booking.user_id),
                lot_name=booking.lot.name,
                start_time=booking.start_time.isoformat()
            )
            
            # TODO: Implement admin notification when admin user management is available
            # admin_users = await self.get_admin_users()
            # for admin in admin_users:
            #     await self.notification_service.create_notification(...)
            
        except Exception as e:
            self.logger.error("Failed to send admin no-show alert", booking_id=str(booking.id), error=str(e))
            raise
