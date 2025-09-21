#!/usr/bin/env python3
"""Add sample notifications for testing the notification system."""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from uuid import UUID
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import AsyncSessionLocal
from app.models.notification import NotificationType, NotificationPriority
from app.services.notification_enhanced import NotificationService
from app.repositories.user import UserRepository


async def create_sample_notifications():
    """Create sample notifications for testing."""
    async with AsyncSessionLocal() as session:
        try:
            # Get a test user
            user_repo = UserRepository(session)
            users = await user_repo.get_multi(limit=1)
            
            if not users:
                print("❌ No users found. Please create a user first.")
                return
            
            user = users[0]
            print(f"📧 Creating sample notifications for user: {user.email}")
            
            # Create notification service
            notification_service = NotificationService(session)
            
            # Sample notifications
            sample_notifications = [
                {
                    "type": NotificationType.BOOKING_CONFIRMATION,
                    "priority": NotificationPriority.NORMAL,
                    "title": "Booking Confirmed",
                    "message": "Your parking booking at Downtown Plaza has been confirmed. Booking ID: SP-2024-001",
                    "metadata": {
                        "booking_reference": "SP-2024-001",
                        "lot_name": "Downtown Plaza",
                        "total_amount": 25.50
                    }
                },
                {
                    "type": NotificationType.BOOKING_REMINDER_START,
                    "priority": NotificationPriority.HIGH,
                    "title": "Booking Starts Soon",
                    "message": "Your parking booking at Mall Parking starts in 5 minutes. Please check in soon.",
                    "metadata": {
                        "booking_reference": "SP-2024-002",
                        "lot_name": "Mall Parking",
                        "minutes_before": 5
                    }
                },
                {
                    "type": NotificationType.CHECKIN_AVAILABLE,
                    "priority": NotificationPriority.NORMAL,
                    "title": "Check-in Available",
                    "message": "You can now check in for your parking booking at Business District. Check-in is available 15 minutes before your booking starts.",
                    "metadata": {
                        "booking_reference": "SP-2024-003",
                        "lot_name": "Business District",
                        "minutes_before": 15
                    }
                },
                {
                    "type": NotificationType.PAYMENT_CONFIRMATION,
                    "priority": NotificationPriority.NORMAL,
                    "title": "Payment Confirmed",
                    "message": "Payment of $18.75 for your booking at Airport Parking has been processed successfully.",
                    "metadata": {
                        "booking_reference": "SP-2024-004",
                        "lot_name": "Airport Parking",
                        "amount": 18.75,
                        "payment_time": datetime.now(timezone.utc).isoformat()
                    }
                },
                {
                    "type": NotificationType.CHECKIN_OVERDUE,
                    "priority": NotificationPriority.CRITICAL,
                    "title": "Check-in Overdue",
                    "message": "You haven't checked in for your booking at City Center Parking. Your booking started 10 minutes ago.",
                    "metadata": {
                        "booking_reference": "SP-2024-005",
                        "lot_name": "City Center Parking",
                        "minutes_after": 10
                    }
                }
            ]
            
            created_count = 0
            
            for notification_data in sample_notifications:
                try:
                    notification = await notification_service.create_notification(
                        user_id=user.id,
                        notification_type=notification_data["type"],
                        title=notification_data["title"],
                        message=notification_data["message"],
                        priority=notification_data["priority"],
                        metadata=notification_data["metadata"]
                    )
                    
                    print(f"✅ Created notification: {notification.title}")
                    created_count += 1
                    
                except Exception as e:
                    print(f"❌ Failed to create notification: {notification_data['title']} - {e}")
            
            print(f"\n🎉 Successfully created {created_count} sample notifications!")
            print(f"👤 User: {user.email}")
            print(f"📱 You can now test the notification system in the frontend.")
            
        except Exception as e:
            print(f"❌ Error creating sample notifications: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("🔔 Creating sample notifications for testing...")
    asyncio.run(create_sample_notifications())
