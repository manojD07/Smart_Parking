"""Test helper utilities."""

import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import json

from utils.api_client import APIClient
from config import config


class TestDataManager:
    """Manages test data creation and cleanup."""
    
    def __init__(self):
        """Initialize test data manager."""
        self.created_users: List[str] = []
        self.created_bookings: List[str] = []
        self.created_lots: List[str] = []
    
    def generate_test_user_data(self, prefix: str = "e2e_test") -> Dict[str, str]:
        """Generate test user data."""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "email": f"{prefix}_{unique_id}@smartparking.com",
            "password": "TestPassword123!",
            "first_name": f"Test{unique_id[:4]}",
            "last_name": f"User{unique_id[4:]}",
            "phone": f"+123456{unique_id[:4]}"
        }
    
    def generate_booking_data(
        self, 
        lot_id: str,
        vehicle_type: str = "car",
        hours_from_now: int = 1,
        duration_hours: int = 2
    ) -> Dict[str, Any]:
        """Generate booking test data."""
        start_time = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
        end_time = start_time + timedelta(hours=duration_hours)
        
        unique_id = str(uuid.uuid4())[:6].upper()
        vehicle_number = f"TEST{unique_id}"
        
        return {
            "lot_id": lot_id,
            "vehicle_type": vehicle_type,
            "vehicle_number": vehicle_number,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    def generate_parking_lot_data(self, name_suffix: str = None) -> Dict[str, Any]:
        """Generate parking lot test data."""
        if not name_suffix:
            name_suffix = str(uuid.uuid4())[:8]
        
        return {
            "name": f"Test Parking Lot {name_suffix}",
            "address": f"123 Test Street, Test City, TC {uuid.uuid4()[:5]}",
            "latitude": 40.7128 + (uuid.uuid4().int % 1000) / 100000,  # NYC area
            "longitude": -74.0060 + (uuid.uuid4().int % 1000) / 100000,
            "total_car_slots": 50,
            "total_bike_slots": 25,
            "hourly_rate_car": 5.0,
            "hourly_rate_bike": 2.5
        }
    
    def track_user(self, user_id: str):
        """Track created user for cleanup."""
        self.created_users.append(user_id)
    
    def track_booking(self, booking_id: str):
        """Track created booking for cleanup."""
        self.created_bookings.append(booking_id)
    
    def track_lot(self, lot_id: str):
        """Track created lot for cleanup."""
        self.created_lots.append(lot_id)


class AssertionHelpers:
    """Custom assertion helpers for API testing."""
    
    @staticmethod
    def assert_response_success(response_data: Dict[str, Any], expected_keys: List[str] = None):
        """Assert response is successful and contains expected keys."""
        assert response_data is not None, "Response data should not be None"
        
        if expected_keys:
            for key in expected_keys:
                assert key in response_data, f"Expected key '{key}' not found in response"
    
    @staticmethod
    def assert_booking_data(booking: Dict[str, Any]):
        """Assert booking contains required fields."""
        required_fields = [
            "id", "user_id", "lot_id", "vehicle_type", "vehicle_number",
            "start_time", "end_time", "total_amount", "status", "booking_reference"
        ]
        AssertionHelpers.assert_response_success(booking, required_fields)
        
        # Validate booking reference format (8 alphanumeric characters)
        booking_ref = booking.get("booking_reference", "")
        assert len(booking_ref) == 8, f"Booking reference should be 8 characters, got {len(booking_ref)}"
        assert booking_ref.isalnum(), "Booking reference should be alphanumeric"
    
    @staticmethod
    def assert_user_data(user: Dict[str, Any]):
        """Assert user contains required fields."""
        required_fields = [
            "id", "email", "first_name", "last_name", "is_admin", "is_active", "created_at"
        ]
        AssertionHelpers.assert_response_success(user, required_fields)
        
        assert "@" in user.get("email", ""), "Email should be valid"
        assert user.get("is_active") is True, "User should be active"
    
    @staticmethod
    def assert_parking_lot_data(lot: Dict[str, Any]):
        """Assert parking lot contains required fields."""
        required_fields = [
            "id", "name", "address", "latitude", "longitude", 
            "total_car_slots", "total_bike_slots", "is_active"
        ]
        AssertionHelpers.assert_response_success(lot, required_fields)
        
        assert lot.get("total_car_slots", 0) >= 0, "Car slots should be non-negative"
        assert lot.get("total_bike_slots", 0) >= 0, "Bike slots should be non-negative"
        assert -90 <= lot.get("latitude", 0) <= 90, "Latitude should be valid"
        assert -180 <= lot.get("longitude", 0) <= 180, "Longitude should be valid"
    
    @staticmethod
    def assert_availability_data(availability: Dict[str, Any]):
        """Assert availability contains required fields."""
        required_fields = ["total_slots", "occupied_slots", "available_slots", "occupancy_rate"]
        AssertionHelpers.assert_response_success(availability, required_fields)
        
        total = availability.get("total_slots", 0)
        occupied = availability.get("occupied_slots", 0)
        available = availability.get("available_slots", 0)
        rate = availability.get("occupancy_rate", 0)
        
        assert total >= 0, "Total slots should be non-negative"
        assert occupied >= 0, "Occupied slots should be non-negative"
        assert available >= 0, "Available slots should be non-negative"
        assert total == occupied + available, "Total should equal occupied + available"
        assert 0 <= rate <= 100, "Occupancy rate should be between 0-100"


class TestScenarios:
    """Common test scenarios and workflows."""
    
    @staticmethod
    def complete_user_registration_flow(client: APIClient, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Complete user registration and login flow."""
        # Register user
        response = client.register_user(
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            phone=user_data["phone"]
        )
        
        AssertionHelpers.assert_user_data(response)
        
        # Login user
        login_response = client.login_user(user_data["email"], user_data["password"])
        assert "access_token" in login_response, "Login should return access token"
        
        return {
            "user": response,
            "login": login_response,
            "access_token": login_response["access_token"]
        }
    
    @staticmethod
    def complete_booking_flow(
        client: APIClient, 
        booking_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Complete booking creation, verification, and cancellation flow."""
        # Get pricing preview
        pricing = client.get_pricing_preview(
            lot_id=booking_data["lot_id"],
            vehicle_type=booking_data["vehicle_type"],
            start_time=booking_data["start_time"],
            end_time=booking_data["end_time"]
        )
        
        assert "total_amount" in pricing, "Pricing preview should include total amount"
        
        # Create booking
        booking = client.create_booking(**booking_data)
        AssertionHelpers.assert_booking_data(booking)
        
        booking_id = booking["id"]
        
        # Verify booking exists in user's bookings
        my_bookings = client.get_my_bookings()
        booking_ids = [b["id"] for b in my_bookings]
        assert booking_id in booking_ids, "Created booking should appear in user's bookings"
        
        # Get specific booking
        specific_booking = client.get_booking(booking_id)
        AssertionHelpers.assert_booking_data(specific_booking)
        assert specific_booking["id"] == booking_id, "Retrieved booking should match created booking"
        
        # Cancel booking
        cancel_response = client.cancel_booking(booking_id)
        assert "message" in cancel_response, "Cancel response should include message"
        
        # Verify booking is cancelled
        cancelled_booking = client.get_booking(booking_id)
        assert cancelled_booking["status"] == "cancelled", "Booking should be cancelled"
        
        return {
            "pricing": pricing,
            "booking": booking,
            "cancel_response": cancel_response,
            "final_booking": cancelled_booking
        }


def wait_for_api_ready(max_attempts: int = 30, delay: float = 1.0) -> bool:
    """Wait for API to be ready."""
    client = APIClient()
    
    for attempt in range(max_attempts):
        try:
            health = client.health_check()
            if health.get("status") == "healthy":
                return True
        except Exception:
            pass
        
        time.sleep(delay)
    
    return False


def generate_test_report(test_results: Dict[str, Any]) -> str:
    """Generate formatted test report."""
    report = []
    report.append("=" * 60)
    report.append("SMART PARKING E2E TEST REPORT")
    report.append("=" * 60)
    report.append(f"Test Run: {datetime.now(timezone.utc).isoformat()}")
    report.append(f"API Base URL: {config.API_BASE_URL}")
    report.append("")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
        duration = result.get("duration", 0)
        report.append(f"{status} {test_name} ({duration:.2f}s)")
        
        if not result.get("passed", False) and "error" in result:
            report.append(f"    Error: {result['error']}")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)
