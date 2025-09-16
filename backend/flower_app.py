"""Standalone Flower monitoring application."""

import os
from celery import Celery

# Create a minimal Celery app just for monitoring
app = Celery('smart_parking_monitor')

# Configure with environment variables
app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/2'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

if __name__ == '__main__':
    app.start()
