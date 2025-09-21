"""Background tasks for booking management."""

from datetime import datetime, timedelta, timezone
from typing import List
import structlog

from app.tasks.celery_app import celery_app
from app.core.database import get_sync_session
from app.services.booking import BookingService
from app.core.cache import cache, ParkingCache

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_expired_bookings(self):
    """Process and mark expired bookings."""
    try:
        with next(get_sync_session()) as session:
            # Convert to async context for service
            import asyncio
            
            async def _process():
                from app.repositories.booking import BookingRepository
                from app.models.booking import BookingStatus
                from app.core.database import AsyncSessionLocal
                
                async with AsyncSessionLocal() as async_session:
                    booking_repo = BookingRepository(async_session)
                    
                    # Get expired bookings
                    expired_bookings = await booking_repo.get_expired_bookings()
                    
                    for booking in expired_bookings:
                        booking.status = BookingStatus.EXPIRED.value
                        
                        # Release slot if needed
                        if booking.slot:
                            booking.slot.mark_available()
                        
                        # Invalidate cache for the lot
                        await ParkingCache.invalidate_lot_availability(str(booking.lot_id))
                    
                    await async_session.commit()
                    
                    logger.info("Processed expired bookings", count=len(expired_bookings))
                    return len(expired_bookings)
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(_process())
                return result
            finally:
                loop.close()
                
    except Exception as exc:
        logger.error("Failed to process expired bookings", error=str(exc))
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_no_show_bookings(self, grace_period_minutes: int = 15):
    """Process and mark no-show bookings."""
    try:
        import asyncio
        
        async def _process():
            from app.repositories.booking import BookingRepository
            from app.models.booking import BookingStatus
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as async_session:
                booking_repo = BookingRepository(async_session)
                
                # Get no-show bookings
                no_show_bookings = await booking_repo.get_no_show_bookings(grace_period_minutes)
                
                for booking in no_show_bookings:
                    booking.status = BookingStatus.NO_SHOW.value
                    
                    # Release slot
                    if booking.slot:
                        booking.slot.mark_available()
                    
                    # Invalidate cache for the lot
                    await ParkingCache.invalidate_lot_availability(str(booking.lot_id))
                
                await async_session.commit()
                
                logger.info("Processed no-show bookings", count=len(no_show_bookings))
                return len(no_show_bookings)
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_process())
            return result
        finally:
            loop.close()
                
    except Exception as exc:
        logger.error("Failed to process no-show bookings", error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_scheduled_notification(self, notification_id: str):
    """Send a scheduled notification."""
    try:
        import asyncio
        from uuid import UUID
        
        async def _send_notification():
            from app.services.notification_enhanced import NotificationService
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as async_session:
                notification_service = NotificationService(async_session)
                
                # Get the notification
                notification = await notification_service.get_by_id(UUID(notification_id))
                
                if not notification:
                    logger.warning("Notification not found for sending", notification_id=notification_id)
                    return False
                
                if notification.is_sent:
                    logger.info("Notification already sent", notification_id=notification_id)
                    return True
                
                # Send the notification
                success = await notification_service.send_notification(notification)
                
                logger.info(
                    "Scheduled notification processed",
                    notification_id=notification_id,
                    success=success,
                    type=notification.type.value,
                    user_id=str(notification.user_id)
                )
                
                return success
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_send_notification())
            return result
        finally:
            loop.close()
                
    except Exception as exc:
        logger.error("Failed to send scheduled notification", notification_id=notification_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_booking_reminder(self, booking_id: str, reminder_type: str):
    """Send booking reminder notifications (legacy - kept for compatibility)."""
    try:
        import asyncio
        
        async def _send_reminder():
            from app.repositories.booking import BookingRepository
            from app.services.notification_enhanced import NotificationService
            from app.models.notification import NotificationType
            from app.core.database import AsyncSessionLocal
            from uuid import UUID
            
            async with AsyncSessionLocal() as async_session:
                booking_repo = BookingRepository(async_session)
                notification_service = NotificationService(async_session)
                
                booking = await booking_repo.get_by_id(UUID(booking_id), load_relationships=True)
                
                if not booking:
                    logger.warning("Booking not found for reminder", booking_id=booking_id)
                    return False
                
                # Map reminder type to notification type
                reminder_mapping = {
                    "1_hour_before": NotificationType.booking_reminder_start,
                    "15_minutes_before": NotificationType.checkin_available,
                    "5_minutes_before": NotificationType.booking_reminder_start,
                    "5_minutes_before_end": NotificationType.booking_reminder_end,
                    "check_in_overdue": NotificationType.checkin_overdue
                }
                
                notification_type = reminder_mapping.get(reminder_type, NotificationType.booking_reminder_start)
                
                # Calculate minutes before/after
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                if notification_type == NotificationType.checkin_overdue:
                    minutes = int((now - booking.start_time).total_seconds() / 60)
                else:
                    minutes = int((booking.start_time - now).total_seconds() / 60)
                
                # Send notification using the new service
                await notification_service.send_booking_reminder(booking, notification_type, minutes)
                
                logger.info(
                    "Legacy booking reminder sent via new notification system",
                    booking_id=booking_id,
                    reminder_type=reminder_type,
                    notification_type=notification_type.value
                )
                
                return True
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_send_reminder())
            return result
        finally:
            loop.close()
                
    except Exception as exc:
        logger.error("Failed to send booking reminder", booking_id=booking_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True)
def schedule_booking_reminders(self, booking_id: str):
    """Schedule reminder notifications for a booking using the new notification system."""
    try:
        from uuid import UUID
        import asyncio
        
        async def _schedule():
            from app.repositories.booking import BookingRepository
            from app.services.notification_scheduler import NotificationScheduler
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as async_session:
                booking_repo = BookingRepository(async_session)
                notification_scheduler = NotificationScheduler(async_session)
                
                booking = await booking_repo.get_by_id(UUID(booking_id), load_relationships=True)
                
                if not booking:
                    logger.warning("Booking not found for scheduling reminders", booking_id=booking_id)
                    return
                
                # Use the new notification scheduler
                task_ids = await notification_scheduler.schedule_booking_notifications(booking)
                
                logger.info(
                    "Scheduled booking notifications using new system",
                    booking_id=booking_id,
                    task_count=len(task_ids),
                    task_ids=task_ids
                )
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_schedule())
        finally:
            loop.close()
                
    except Exception as exc:
        logger.error("Failed to schedule booking reminders", booking_id=booking_id, error=str(exc))
        raise


@celery_app.task(bind=True)
def cancel_booking_notifications(self, booking_id: str):
    """Cancel all scheduled notifications for a booking."""
    try:
        from uuid import UUID
        import asyncio
        
        async def _cancel():
            from app.services.notification_scheduler import NotificationScheduler
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as async_session:
                notification_scheduler = NotificationScheduler(async_session)
                
                cancelled_count = await notification_scheduler.cancel_booking_notifications(UUID(booking_id))
                
                logger.info(
                    "Cancelled booking notifications",
                    booking_id=booking_id,
                    cancelled_count=cancelled_count
                )
                
                return cancelled_count
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_cancel())
            return result
        finally:
            loop.close()
                
    except Exception as exc:
        logger.error("Failed to cancel booking notifications", booking_id=booking_id, error=str(exc))
        raise


@celery_app.task(bind=True)
def check_started_bookings_for_checkin_prompt(self):
    """Check for bookings that have started and need check-in prompts."""
    try:
        import asyncio
        from datetime import datetime, timezone, timedelta
        
        async def _check_started_bookings():
            from app.repositories.booking import BookingRepository
            from app.services.notification_enhanced import NotificationService
            from app.models.notification import NotificationType, NotificationPriority
            from app.models.booking import BookingStatus
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as async_session:
                booking_repo = BookingRepository(async_session)
                notification_service = NotificationService(async_session)
                
                # Get current time
                now = datetime.now(timezone.utc)
                
                # Find bookings that:
                # 1. Have started (start_time <= now)
                # 2. Are confirmed but not checked in
                # 3. Started within the last 15 minutes (to avoid spam)
                started_cutoff = now - timedelta(minutes=15)
                
                # Get bookings that need check-in prompts
                from sqlalchemy import select, and_
                from app.models.booking import Booking
                
                query = select(Booking).where(
                    and_(
                        Booking.start_time <= now,
                        Booking.start_time >= started_cutoff,
                        Booking.status == BookingStatus.CONFIRMED.value,
                        Booking.check_in_time.is_(None)  # Not checked in yet
                    )
                )
                
                result = await async_session.execute(query)
                started_bookings = result.scalars().all()
                
                logger.info(
                    "Checking started bookings for check-in prompts",
                    found_bookings=len(started_bookings),
                    check_time=now.isoformat()
                )
                
                notifications_sent = 0
                
                for booking in started_bookings:
                    try:
                        # Check if we already sent a check-in prompt for this booking
                        existing_notifications = await notification_service.repository.get_notifications_by_booking(booking.id)
                        
                        # Check if we already have a check-in overdue notification
                        has_checkin_prompt = any(
                            n.type == NotificationType.checkin_overdue and n.is_sent
                            for n in existing_notifications
                        )
                        
                        if not has_checkin_prompt:
                            # Calculate how many minutes since booking started
                            minutes_since_start = int((now - booking.start_time).total_seconds() / 60)
                            
                            # Get booking with relationships
                            booking_with_relations = await booking_repo.get_by_id(booking.id, load_relationships=True)
                            
                            if booking_with_relations:
                                await notification_service.create_notification(
                                    user_id=booking.user_id,
                                    notification_type=NotificationType.checkin_overdue,
                                    title="Check-in Required",
                                    message=f"Your booking at {booking_with_relations.lot.name} has started. Please check in now to secure your parking spot.",
                                    priority=NotificationPriority.high,
                                    booking_id=booking.id,
                                    lot_id=booking.lot_id,
                                    metadata={
                                        "booking_reference": booking.booking_reference,
                                        "lot_name": booking_with_relations.lot.name,
                                        "minutes_since_start": minutes_since_start,
                                        "start_time": booking.start_time.isoformat(),
                                        "end_time": booking.end_time.isoformat()
                                    }
                                )
                                
                                notifications_sent += 1
                                
                                logger.info(
                                    "Check-in prompt notification sent",
                                    booking_id=booking.id,
                                    minutes_since_start=minutes_since_start,
                                    user_id=booking.user_id
                                )
                        
                    except Exception as e:
                        logger.error(
                            "Failed to send check-in prompt notification",
                            booking_id=booking.id,
                            error=str(e)
                        )
                
                logger.info(
                    "Check-in prompt task completed",
                    total_started_bookings=len(started_bookings),
                    notifications_sent=notifications_sent
                )
                
                return notifications_sent
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_check_started_bookings())
            return result
        finally:
            loop.close()
                
    except Exception as exc:
        logger.error("Failed to check started bookings for check-in prompts", error=str(exc))
        raise


@celery_app.task(bind=True, max_retries=3)
def update_lot_availability_cache(self, lot_id: str):
    """Update cached availability data for a parking lot."""
    try:
        import asyncio
        
        async def _update_cache():
            from app.repositories.parking import ParkingLotRepository
            from app.core.database import AsyncSessionLocal
            from app.models.parking import VehicleType
            from uuid import UUID
            from datetime import datetime, timedelta
            
            async with AsyncSessionLocal() as async_session:
                lot_repo = ParkingLotRepository(async_session)
                
                # Calculate current availability
                now = datetime.now(timezone.utc)
                end_time = now + timedelta(hours=1)  # Next hour
                
                availability_data = {}
                
                for vehicle_type in [VehicleType.CAR, VehicleType.BIKE]:
                    availability = await lot_repo._calculate_availability(
                        UUID(lot_id), vehicle_type, now, end_time
                    )
                    availability_data[vehicle_type.value] = availability
                
                # Cache the data
                await ParkingCache.set_lot_availability(lot_id, availability_data, ttl=60)
                
                logger.info("Updated lot availability cache", lot_id=lot_id)
                return availability_data
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_update_cache())
            return result
        finally:
            loop.close()
                
    except Exception as exc:
        logger.error("Failed to update lot availability cache", lot_id=lot_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@celery_app.task
def generate_booking_report(start_date: str, end_date: str, lot_id: str = None):
    """Generate booking report for a date range."""
    try:
        import asyncio
        from datetime import datetime
        
        async def _generate_report():
            from app.repositories.booking import BookingRepository
            from app.core.database import AsyncSessionLocal
            from uuid import UUID
            
            async with AsyncSessionLocal() as async_session:
                booking_repo = BookingRepository(async_session)
                
                start_dt = datetime.fromisoformat(start_date)
                end_dt = datetime.fromisoformat(end_date)
                lot_uuid = UUID(lot_id) if lot_id else None
                
                # Get booking statistics
                stats = await booking_repo.get_booking_statistics(
                    start_dt, end_dt, lot_uuid
                )
                
                # Here you would typically:
                # 1. Format the report
                # 2. Save to file storage
                # 3. Send email to admins
                # 4. Store in database
                
                logger.info(
                    "Generated booking report",
                    start_date=start_date,
                    end_date=end_date,
                    lot_id=lot_id,
                    total_bookings=stats.get('total_bookings', 0),
                    total_revenue=stats.get('total_revenue', 0)
                )
                
                return stats
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_generate_report())
            return result
        finally:
            loop.close()
                
    except Exception as exc:
        logger.error("Failed to generate booking report", error=str(exc))
        raise
