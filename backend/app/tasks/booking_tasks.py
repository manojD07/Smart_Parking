"""Background tasks for booking management."""

from datetime import datetime, timedelta
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
def send_booking_reminder(self, booking_id: str, reminder_type: str):
    """Send booking reminder notifications."""
    try:
        import asyncio
        
        async def _send_reminder():
            from app.repositories.booking import BookingRepository
            from app.core.database import AsyncSessionLocal
            from uuid import UUID
            
            async with AsyncSessionLocal() as async_session:
                booking_repo = BookingRepository(async_session)
                booking = await booking_repo.get_by_id(UUID(booking_id), load_relationships=True)
                
                if not booking:
                    logger.warning("Booking not found for reminder", booking_id=booking_id)
                    return False
                
                # Here you would integrate with email/SMS service
                # For now, just log the reminder
                logger.info(
                    "Sending booking reminder",
                    booking_id=booking_id,
                    user_email=booking.user.email,
                    reminder_type=reminder_type,
                    start_time=booking.start_time
                )
                
                # TODO: Implement actual notification sending
                # - Email service integration
                # - SMS service integration
                # - Push notification service
                
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
    """Schedule reminder notifications for a booking."""
    try:
        from uuid import UUID
        import asyncio
        
        async def _schedule():
            from app.repositories.booking import BookingRepository
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as async_session:
                booking_repo = BookingRepository(async_session)
                booking = await booking_repo.get_by_id(UUID(booking_id))
                
                if not booking:
                    logger.warning("Booking not found for scheduling reminders", booking_id=booking_id)
                    return
                
                # Schedule reminders
                now = datetime.utcnow()
                
                # 1 hour before reminder
                reminder_1h = booking.start_time - timedelta(hours=1)
                if reminder_1h > now:
                    send_booking_reminder.apply_async(
                        args=[booking_id, "1_hour_before"],
                        eta=reminder_1h
                    )
                
                # 15 minutes before reminder
                reminder_15m = booking.start_time - timedelta(minutes=15)
                if reminder_15m > now:
                    send_booking_reminder.apply_async(
                        args=[booking_id, "15_minutes_before"],
                        eta=reminder_15m
                    )
                
                logger.info("Scheduled booking reminders", booking_id=booking_id)
        
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
                now = datetime.utcnow()
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
