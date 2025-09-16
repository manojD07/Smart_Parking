"""Celery application configuration."""

from celery import Celery, signals
from celery.schedules import crontab
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Create Celery instance
celery_app = Celery(
    "smart_parking",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.booking_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=False,
    
    # Task routing
    task_routes={
        "app.tasks.booking_tasks.*": {"queue": "booking"},
        "app.tasks.maintenance_tasks.*": {"queue": "maintenance"},
    },
    
    # Task execution
    task_always_eager=settings.environment == "testing",
    task_eager_propagates=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Task retries
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Process expired bookings every 5 minutes
        "process-expired-bookings": {
            "task": "app.tasks.booking_tasks.process_expired_bookings",
            "schedule": crontab(minute="*/5"),
            "options": {"queue": "booking"}
        },
        
        # Process no-show bookings every 10 minutes
        "process-no-show-bookings": {
            "task": "app.tasks.booking_tasks.process_no_show_bookings",
            "schedule": crontab(minute="*/10"),
            "options": {"queue": "booking"}
        },
        
        # Update slot statistics every hour
        "update-slot-statistics": {
            "task": "app.tasks.maintenance_tasks.update_slot_statistics",
            "schedule": crontab(minute=0),  # Every hour
            "options": {"queue": "maintenance"}
        },
        
        # Cleanup old logs daily at 2 AM
        "cleanup-old-logs": {
            "task": "app.tasks.maintenance_tasks.cleanup_old_logs",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
            "options": {"queue": "maintenance"}
        },
        
        # Generate daily reports at 1 AM
        "generate-daily-reports": {
            "task": "app.tasks.maintenance_tasks.generate_daily_reports",
            "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
            "options": {"queue": "maintenance"}
        },
    },
)


# Task error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing."""
    logger.info(f"Request: {self.request!r}")
    return f"Hello from Celery! Request: {self.request!r}"


# Signal handlers
@signals.worker_ready.connect
def worker_ready(sender, **kwargs):
    """Worker ready signal handler."""
    logger.info("Celery worker is ready", worker_name=sender.hostname)


@signals.worker_shutdown.connect
def worker_shutdown(sender, **kwargs):
    """Worker shutdown signal handler."""
    logger.info("Celery worker is shutting down", worker_name=sender.hostname)


@signals.task_prerun.connect
def task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Task prerun signal handler."""
    logger.info("Task starting", task_id=task_id, task_name=task.name)


@signals.task_postrun.connect
def task_postrun(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Task postrun signal handler."""
    logger.info("Task completed", task_id=task_id, task_name=task.name, state=state)


@signals.task_failure.connect
def task_failure(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Task failure signal handler."""
    logger.error(
        "Task failed",
        task_id=task_id,
        task_name=sender.name,
        exception=str(exception),
        traceback=traceback
    )
