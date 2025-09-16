"""
Comprehensive tests for admin and check-in/check-out APIs.

This test module covers:
- Admin dashboard functionality
- Admin check-in by booking reference
- User check-in by booking ID
- User check-out by booking ID
- Admin reports and statistics
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone, date
from uuid import uuid4
from decimal import Decimal
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.models.user import User
from app.models.parking import ParkingLot, ParkingSlot, VehicleType
from app.models.booking import Booking, BookingStatus
from app.core.database import get_async_session
from app.services.auth import AuthService
from app.services.parking import ParkingService
from app.services.booking import BookingService


class TestAdminCheckinAPI:
    """Test class for admin and check-in/check-out functionality."""

    @pytest.fixture(autouse=True)
    async def setup_test_data(self, db_session, client):
        """Set up test data for each test."""
        self.session = db_session
        self.client = client
        
        # Create admin user
        self.admin_user = User(
            email="admin@test.com",
            first_name="Admin",
            last_name="User", 
            phone="9999999999",
            is_admin=True,
            is_active=True
        )
        self.admin_user.set_password("Admin123456!")
        self.session.add(self.admin_user)
        
        # Create regular user
        self.regular_user = User(
            email="user@test.com",
            first_name="Test",
            last_name="User",
            phone="1234567890",
            is_admin=False,
            is_active=True
        )
        self.regular_user.set_password("User123456!")
        self.session.add(self.regular_user)
        
        # Create parking lot
        self.parking_lot = ParkingLot(
            name="Test Parking Lot",
            address="123 Test Street",
            latitude=40.7128,
            longitude=-74.0060,
            total_car_slots=20,
            total_bike_slots=10,
            hourly_rate_car=Decimal("5.00"),
            hourly_rate_bike=Decimal("2.00"),
            is_active=True
        )
        self.session.add(self.parking_lot)
        
        # Create parking slots
        self.car_slot = ParkingSlot(
            lot=self.parking_lot,
            slot_number="C001",
            vehicle_type=VehicleType.CAR,
            is_occupied=False,
            is_active=True
        )
        self.session.add(self.car_slot)
        
        self.bike_slot = ParkingSlot(
            lot=self.parking_lot,
            slot_number="B001", 
            vehicle_type=VehicleType.BIKE,
            is_occupied=False,
            is_active=True
        )
        self.session.add(self.bike_slot)
        
        await self.session.commit()
        await self.session.refresh(self.admin_user)
        await self.session.refresh(self.regular_user)
        await self.session.refresh(self.parking_lot)
        await self.session.refresh(self.car_slot)
        await self.session.refresh(self.bike_slot)
        
        # Get authentication tokens
        auth_service = AuthService(self.session)
        self.admin_token = await auth_service.create_access_token(self.admin_user.id)
        self.user_token = await auth_service.create_access_token(self.regular_user.id)

    async def test_admin_dashboard_success(self):
        """Test successful admin dashboard access."""
        response = await self.client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check dashboard structure
        assert "overview" in data
        assert "today_statistics" in data
        
        overview = data["overview"]
        assert "total_users" in overview
        assert "total_parking_lots" in overview
        assert "today_bookings" in overview
        assert "today_revenue" in overview
        
        # Check values
        assert overview["total_users"] >= 2  # At least admin and regular user
        assert overview["total_parking_lots"] >= 1  # At least our test lot

    async def test_admin_dashboard_unauthorized(self):
        """Test admin dashboard access with regular user token."""
        response = await self.client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_admin_dashboard_no_token(self):
        """Test admin dashboard access without token."""
        response = await self.client.get("/api/v1/admin/dashboard")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_admin_revenue_report_success(self):
        """Test admin revenue report access."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        response = await self.client.get(
            f"/api/v1/admin/reports/revenue?start_date={yesterday}&end_date={today}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check report structure
        assert "total_revenue" in data
        assert "total_bookings" in data
        assert "period" in data

    async def test_admin_revenue_report_unauthorized(self):
        """Test admin revenue report with regular user."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        response = await self.client.get(
            f"/api/v1/admin/reports/revenue?start_date={yesterday}&end_date={today}",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_create_booking_for_checkin_tests(self):
        """Helper method to create a booking for check-in tests."""
        start_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        end_time = start_time + timedelta(hours=2)
        
        # Create booking directly via service
        booking_service = BookingService(self.session)
        self.test_booking = await booking_service.create_booking(
            user_id=self.regular_user.id,
            lot_id=self.parking_lot.id,
            vehicle_type=VehicleType.CAR,
            vehicle_number="TEST123",
            start_time=start_time,
            end_time=end_time
        )
        
        await self.session.commit()
        await self.session.refresh(self.test_booking)
        return self.test_booking

    async def test_admin_checkin_by_reference_success(self):
        """Test admin check-in by booking reference."""
        # Create a booking first
        booking = await self.create_booking_for_checkin_tests()
        
        response = await self.client.post(
            f"/api/v1/bookings/checkin/{booking.booking_reference}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Booking checked in successfully"

    async def test_admin_checkin_by_reference_not_found(self):
        """Test admin check-in with invalid booking reference."""
        response = await self.client.post(
            "/api/v1/bookings/checkin/INVALID123",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_admin_checkin_by_reference_unauthorized(self):
        """Test admin check-in with regular user token."""
        booking = await self.create_booking_for_checkin_tests()
        
        response = await self.client.post(
            f"/api/v1/bookings/checkin/{booking.booking_reference}",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_user_checkin_by_booking_id_success(self):
        """Test user check-in by booking ID."""
        booking = await self.create_booking_for_checkin_tests()
        
        response = await self.client.post(
            f"/api/v1/bookings/{booking.id}/checkin",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Checked in successfully"

    async def test_user_checkin_wrong_user(self):
        """Test user check-in with different user's booking."""
        booking = await self.create_booking_for_checkin_tests()
        
        # Create another user
        other_user = User(
            email="other@test.com",
            first_name="Other",
            last_name="User",
            phone="5555555555",
            is_admin=False,
            is_active=True
        )
        other_user.set_password("Other123456!")
        self.session.add(other_user)
        await self.session.commit()
        await self.session.refresh(other_user)
        
        auth_service = AuthService(self.session)
        other_token = await auth_service.create_access_token(other_user.id)
        
        response = await self.client.post(
            f"/api/v1/bookings/{booking.id}/checkin",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    async def test_user_checkin_invalid_booking_id(self):
        """Test user check-in with invalid booking ID."""
        invalid_id = str(uuid4())
        
        response = await self.client.post(
            f"/api/v1/bookings/{invalid_id}/checkin",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_user_checkout_success(self):
        """Test user check-out from booking."""
        # Create and check-in booking first
        booking = await self.create_booking_for_checkin_tests()
        
        # Check in first
        await self.client.post(
            f"/api/v1/bookings/{booking.id}/checkin",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        # Now check out
        response = await self.client.post(
            f"/api/v1/bookings/{booking.id}/checkout",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Checked out successfully"

    async def test_user_checkout_not_checked_in(self):
        """Test user check-out without check-in."""
        booking = await self.create_booking_for_checkin_tests()
        
        response = await self.client.post(
            f"/api/v1/bookings/{booking.id}/checkout",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        # Should fail because not checked in yet
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_user_checkout_wrong_user(self):
        """Test user check-out with different user's booking."""
        booking = await self.create_booking_for_checkin_tests()
        
        # Create another user
        other_user = User(
            email="checkout_other@test.com",
            first_name="Checkout",
            last_name="Other",
            phone="6666666666",
            is_admin=False,
            is_active=True
        )
        other_user.set_password("Checkout123456!")
        self.session.add(other_user)
        await self.session.commit()
        await self.session.refresh(other_user)
        
        auth_service = AuthService(self.session)
        other_token = await auth_service.create_access_token(other_user.id)
        
        response = await self.client.post(
            f"/api/v1/bookings/{booking.id}/checkout",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    async def test_get_booking_by_reference_admin(self):
        """Test getting booking by reference as admin."""
        booking = await self.create_booking_for_checkin_tests()
        
        response = await self.client.get(
            f"/api/v1/bookings/reference/{booking.booking_reference}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(booking.id)
        assert data["booking_reference"] == booking.booking_reference

    async def test_get_booking_by_reference_user_own_booking(self):
        """Test getting own booking by reference as regular user."""
        booking = await self.create_booking_for_checkin_tests()
        
        response = await self.client.get(
            f"/api/v1/bookings/reference/{booking.booking_reference}",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(booking.id)

    async def test_get_booking_by_reference_user_others_booking(self):
        """Test getting other user's booking by reference."""
        booking = await self.create_booking_for_checkin_tests()
        
        # Create another user
        other_user = User(
            email="ref_other@test.com",
            first_name="Ref",
            last_name="Other",
            phone="7777777777",
            is_admin=False,
            is_active=True
        )
        other_user.set_password("RefOther123456!")
        self.session.add(other_user)
        await self.session.commit()
        await self.session.refresh(other_user)
        
        auth_service = AuthService(self.session)
        other_token = await auth_service.create_access_token(other_user.id)
        
        response = await self.client.get(
            f"/api/v1/bookings/reference/{booking.booking_reference}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_booking_by_reference_not_found(self):
        """Test getting non-existent booking by reference."""
        response = await self.client.get(
            "/api/v1/bookings/reference/NONEXISTENT123",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_checkin_checkout_flow_complete(self):
        """Test complete check-in/check-out flow."""
        # 1. Create booking
        booking = await self.create_booking_for_checkin_tests()
        
        # 2. Get booking details
        response = await self.client.get(
            f"/api/v1/bookings/{booking.id}",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.CONFIRMED.value
        assert data["check_in_time"] is None
        assert data["check_out_time"] is None
        
        # 3. Check in
        response = await self.client.post(
            f"/api/v1/bookings/{booking.id}/checkin",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 4. Verify checked in status
        response = await self.client.get(
            f"/api/v1/bookings/{booking.id}",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.CHECKED_IN.value
        assert data["check_in_time"] is not None
        assert data["check_out_time"] is None
        
        # 5. Check out
        response = await self.client.post(
            f"/api/v1/bookings/{booking.id}/checkout",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 6. Verify checked out status
        response = await self.client.get(
            f"/api/v1/bookings/{booking.id}",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.COMPLETED.value
        assert data["check_in_time"] is not None
        assert data["check_out_time"] is not None

    async def test_admin_checkin_any_booking_flow(self):
        """Test admin can check in any user's booking."""
        # 1. Create booking as regular user
        booking = await self.create_booking_for_checkin_tests()
        
        # 2. Admin checks in using booking reference
        response = await self.client.post(
            f"/api/v1/bookings/checkin/{booking.booking_reference}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 3. Verify status changed
        response = await self.client.get(
            f"/api/v1/bookings/{booking.id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.CHECKED_IN.value


class TestAdminCheckinIntegration:
    """Integration tests for admin and checkin functionality."""

    @pytest.fixture(autouse=True)
    async def setup_integration_data(self, db_session, client):
        """Set up integration test data."""
        self.session = db_session
        self.client = client

    async def test_full_parking_workflow_with_admin_assistance(self):
        """Test complete parking workflow with admin assistance."""
        # This test simulates a real-world scenario where admin helps with check-in
        
        # 1. Create users and parking infrastructure
        admin_user = User(
            email="workflow_admin@test.com",
            first_name="Workflow",
            last_name="Admin",
            phone="8888888888",
            is_admin=True,
            is_active=True
        )
        admin_user.set_password("WorkflowAdmin123!")
        self.session.add(admin_user)
        
        customer_user = User(
            email="customer@test.com",
            first_name="Customer",
            last_name="User",
            phone="3333333333",
            is_admin=False,
            is_active=True
        )
        customer_user.set_password("Customer123!")
        self.session.add(customer_user)
        
        parking_lot = ParkingLot(
            name="Integration Test Lot",
            address="456 Integration Street", 
            latitude=40.7589,
            longitude=-73.9851,
            total_car_slots=5,
            total_bike_slots=3,
            hourly_rate_car=Decimal("8.00"),
            hourly_rate_bike=Decimal("3.00"),
            is_active=True
        )
        self.session.add(parking_lot)
        
        await self.session.commit()
        await self.session.refresh(admin_user)
        await self.session.refresh(customer_user)
        await self.session.refresh(parking_lot)
        
        # Get tokens
        auth_service = AuthService(self.session)
        admin_token = await auth_service.create_access_token(admin_user.id)
        customer_token = await auth_service.create_access_token(customer_user.id)
        
        # 2. Customer creates booking
        start_time = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        end_time = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
        
        booking_data = {
            "lot_id": str(parking_lot.id),
            "vehicle_type": "car",
            "vehicle_number": "INTEG123",
            "start_time": start_time,
            "end_time": end_time
        }
        
        response = await self.client.post(
            "/api/v1/bookings/",
            headers={"Authorization": f"Bearer {customer_token}"},
            json=booking_data
        )
        assert response.status_code == status.HTTP_201_CREATED
        booking_response = response.json()
        booking_reference = booking_response["booking_reference"]
        
        # 3. Admin views dashboard to see today's bookings
        response = await self.client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        dashboard = response.json()
        assert dashboard["today_statistics"]["total_bookings"] >= 1
        
        # 4. Customer arrives but can't find mobile app, admin helps with check-in
        response = await self.client.post(
            f"/api/v1/bookings/checkin/{booking_reference}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 5. Later, customer checks out normally via their own account
        response = await self.client.post(
            f"/api/v1/bookings/{booking_response['id']}/checkout",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 6. Admin generates revenue report including this booking
        today = date.today()
        response = await self.client.get(
            f"/api/v1/admin/reports/revenue?start_date={today}&end_date={today}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        report = response.json()
        assert float(report["total_revenue"]) > 0
        
        print("✅ Complete workflow test passed!")


if __name__ == "__main__":
    # For running individual tests during development
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    async def run_single_test():
        """Run a single test for development."""
        # This would need proper test setup
        print("Individual test runner - use pytest instead")
    
    asyncio.run(run_single_test())
