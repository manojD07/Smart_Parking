"""Repository for notification data access operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload

import structlog

from app.models.notification import Notification, NotificationType, NotificationPriority
from app.repositories.base import BaseRepository

logger = structlog.get_logger(__name__)


class NotificationRepository(BaseRepository[Notification]):
    """Repository for notification operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)
        self.logger = logger.bind(repository="NotificationRepository")

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
        **channels
    ) -> Notification:
        """Create a new notification."""
        try:
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                priority=priority,
                title=title,
                message=message,
                scheduled_at=scheduled_at,
                booking_id=booking_id,
                lot_id=lot_id,
                send_email=channels.get('send_email', False),
                send_sms=channels.get('send_sms', False),
                send_push=channels.get('send_push', False),
                send_websocket=channels.get('send_websocket', True),
                notification_metadata=channels.get('metadata')
            )
            
            self.session.add(notification)
            await self.session.commit()
            await self.session.refresh(notification)
            
            self.logger.info(
                "Notification created",
                notification_id=str(notification.id),
                user_id=str(user_id),
                type=notification_type.value,
                priority=priority.value
            )
            
            return notification
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to create notification", error=str(e))
            raise

    async def get_user_notifications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        include_relationships: bool = True
    ) -> List[Notification]:
        """Get notifications for a user with pagination and filtering."""
        try:
            query = select(Notification).where(Notification.user_id == user_id)
            
            if include_relationships:
                query = query.options(
                    selectinload(Notification.booking),
                    selectinload(Notification.lot),
                    selectinload(Notification.user)
                )
            
            # Apply filters
            if unread_only:
                query = query.where(Notification.is_read == False)
            
            if notification_type:
                query = query.where(Notification.type == notification_type)
            
            # Order by creation date (newest first)
            query = query.order_by(desc(Notification.created_at))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            notifications = result.scalars().all()
            
            self.logger.debug(
                "Retrieved user notifications",
                user_id=str(user_id),
                count=len(notifications),
                unread_only=unread_only
            )
            
            return list(notifications)
            
        except Exception as e:
            self.logger.error("Failed to get user notifications", error=str(e))
            raise

    async def get_notification_stats(self, user_id: UUID) -> Dict[str, int]:
        """Get notification statistics for a user."""
        try:
            # Total notifications
            total_query = select(func.count(Notification.id)).where(
                Notification.user_id == user_id
            )
            total_result = await self.session.execute(total_query)
            total_notifications = total_result.scalar() or 0
            
            # Unread notifications
            unread_query = select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
            unread_result = await self.session.execute(unread_query)
            unread_count = unread_result.scalar() or 0
            
            # Today's notifications
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_query = select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= today
                )
            )
            today_result = await self.session.execute(today_query)
            today_count = today_result.scalar() or 0
            
            # This week's notifications (last 7 days)
            week_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = week_ago.replace(day=week_ago.day - 7)
            week_query = select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= week_ago
                )
            )
            week_result = await self.session.execute(week_query)
            week_count = week_result.scalar() or 0
            
            stats = {
                "total_notifications": total_notifications,
                "unread_count": unread_count,
                "read_count": total_notifications - unread_count,
                "today_count": today_count,
                "this_week_count": week_count
            }
            
            self.logger.debug("Retrieved notification stats", user_id=str(user_id), stats=stats)
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get notification stats", error=str(e))
            raise

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read."""
        try:
            query = (
                update(Notification)
                .where(
                    and_(
                        Notification.id == notification_id,
                        Notification.user_id == user_id
                    )
                )
                .values(
                    is_read=True,
                    read_at=datetime.now(timezone.utc)
                )
            )
            
            result = await self.session.execute(query)
            await self.session.commit()
            
            success = result.rowcount > 0
            
            if success:
                self.logger.info(
                    "Notification marked as read",
                    notification_id=str(notification_id),
                    user_id=str(user_id)
                )
            else:
                self.logger.warning(
                    "Notification not found or not owned by user",
                    notification_id=str(notification_id),
                    user_id=str(user_id)
                )
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to mark notification as read", error=str(e))
            raise

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        try:
            query = (
                update(Notification)
                .where(
                    and_(
                        Notification.user_id == user_id,
                        Notification.is_read == False
                    )
                )
                .values(
                    is_read=True,
                    read_at=datetime.now(timezone.utc)
                )
            )
            
            result = await self.session.execute(query)
            await self.session.commit()
            
            updated_count = result.rowcount
            
            self.logger.info(
                "Marked all notifications as read",
                user_id=str(user_id),
                updated_count=updated_count
            )
            
            return updated_count
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to mark all notifications as read", error=str(e))
            raise

    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """Delete a notification."""
        try:
            query = delete(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
            
            result = await self.session.execute(query)
            await self.session.commit()
            
            success = result.rowcount > 0
            
            if success:
                self.logger.info(
                    "Notification deleted",
                    notification_id=str(notification_id),
                    user_id=str(user_id)
                )
            else:
                self.logger.warning(
                    "Notification not found or not owned by user",
                    notification_id=str(notification_id),
                    user_id=str(user_id)
                )
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to delete notification", error=str(e))
            raise

    async def get_scheduled_notifications(
        self,
        before_time: Optional[datetime] = None
    ) -> List[Notification]:
        """Get notifications that are scheduled to be sent."""
        try:
            query = select(Notification).where(
                and_(
                    Notification.scheduled_at.is_not(None),
                    Notification.is_sent == False
                )
            )
            
            if before_time:
                query = query.where(Notification.scheduled_at <= before_time)
            
            query = query.order_by(Notification.scheduled_at)
            
            result = await self.session.execute(query)
            notifications = result.scalars().all()
            
            self.logger.debug(
                "Retrieved scheduled notifications",
                count=len(notifications),
                before_time=before_time.isoformat() if before_time else None
            )
            
            return list(notifications)
            
        except Exception as e:
            self.logger.error("Failed to get scheduled notifications", error=str(e))
            raise

    async def mark_as_sent(self, notification_id: UUID, celery_task_id: Optional[str] = None) -> bool:
        """Mark a notification as sent."""
        try:
            update_values = {
                "is_sent": True,
                "sent_at": datetime.now(timezone.utc)
            }
            
            if celery_task_id:
                update_values["celery_task_id"] = celery_task_id
            
            query = (
                update(Notification)
                .where(Notification.id == notification_id)
                .values(**update_values)
            )
            
            result = await self.session.execute(query)
            await self.session.commit()
            
            success = result.rowcount > 0
            
            if success:
                self.logger.info(
                    "Notification marked as sent",
                    notification_id=str(notification_id),
                    celery_task_id=celery_task_id
                )
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to mark notification as sent", error=str(e))
            raise

    async def get_notifications_by_booking(self, booking_id: UUID) -> List[Notification]:
        """Get all notifications for a specific booking."""
        try:
            query = (
                select(Notification)
                .where(Notification.booking_id == booking_id)
                .order_by(desc(Notification.created_at))
            )
            
            result = await self.session.execute(query)
            notifications = result.scalars().all()
            
            self.logger.debug(
                "Retrieved notifications by booking",
                booking_id=str(booking_id),
                count=len(notifications)
            )
            
            return list(notifications)
            
        except Exception as e:
            self.logger.error("Failed to get notifications by booking", error=str(e))
            raise

    async def cancel_scheduled_notifications(self, booking_id: UUID) -> int:
        """Cancel all scheduled notifications for a booking."""
        try:
            query = (
                update(Notification)
                .where(
                    and_(
                        Notification.booking_id == booking_id,
                        Notification.is_sent == False,
                        Notification.scheduled_at.is_not(None)
                    )
                )
                .values(
                    scheduled_at=None,
                    celery_task_id=None
                )
            )
            
            result = await self.session.execute(query)
            await self.session.commit()
            
            cancelled_count = result.rowcount
            
            self.logger.info(
                "Cancelled scheduled notifications",
                booking_id=str(booking_id),
                cancelled_count=cancelled_count
            )
            
            return cancelled_count
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to cancel scheduled notifications", error=str(e))
            raise
