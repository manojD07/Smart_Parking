"""Minimal Celery application for Flower monitoring."""

from celery import Celery
import os

# Get Celery configuration from environment
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')

# Create minimal Celery instance for monitoring
celery_app = Celery(
    "smart_parking_minimal",
    broker=broker_url,
    backend=result_backend,
)

# Basic configuration for monitoring
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
