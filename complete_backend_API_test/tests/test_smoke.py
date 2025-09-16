"""Smoke tests for Smart Parking API."""

import pytest
from utils.api_client import APIClient
from utils.test_helpers import AssertionHelpers
from config import config


@pytest.mark.smoke
class TestSmoke:
    """Basic smoke tests to verify API is functional."""
    
    def test_api_health_check(self, api_client: APIClient):
        """Test API health check endpoint."""
        health = api_client.health_check()
        
        assert health["status"] == "healthy", "API should be healthy"
        assert "timestamp" in health, "Health check should include timestamp"
        assert "version" in health, "Health check should include version"
    
    def test_get_parking_lots(self, api_client: APIClient):
        """Test getting parking lots without authentication."""
        lots = api_client.get_parking_lots()
        
        assert isinstance(lots, list), "Parking lots should be a list"
        assert len(lots) > 0, "Should have at least one parking lot"
        
        # Check first lot structure
        if lots:
            AssertionHelpers.assert_parking_lot_data(lots[0])
    
    def test_get_specific_parking_lot(self, api_client: APIClient):
        """Test getting specific parking lot details."""
        lot = api_client.get_parking_lot(config.TEST_PARKING_LOT_ID)
        
        AssertionHelpers.assert_parking_lot_data(lot)
        assert lot["id"] == config.TEST_PARKING_LOT_ID, "Should return correct lot ID"
    
    def test_get_lot_slots(self, api_client: APIClient):
        """Test getting parking lot slots."""
        slots = api_client.get_lot_slots(config.TEST_PARKING_LOT_ID, limit=5)
        
        assert isinstance(slots, list), "Slots should be a list"
        assert len(slots) > 0, "Should have at least one slot"
        
        # Check first slot structure
        if slots:
            slot = slots[0]
            required_fields = ["id", "lot_id", "slot_number", "slot_type", "status"]
            AssertionHelpers.assert_response_success(slot, required_fields)
    
    def test_get_lot_availability_car(self, api_client: APIClient):
        """Test getting parking lot availability for cars."""
        start_time = api_client.generate_future_datetime(1)
        end_time = api_client.generate_future_datetime(3)
        
        availability = api_client.get_lot_availability(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            start_time=start_time,
            end_time=end_time
        )
        
        AssertionHelpers.assert_availability_data(availability)
    
    def test_get_lot_availability_bike(self, api_client: APIClient):
        """Test getting parking lot availability for bikes."""
        start_time = api_client.generate_future_datetime(1)
        end_time = api_client.generate_future_datetime(3)
        
        availability = api_client.get_lot_availability(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="bike",
            start_time=start_time,
            end_time=end_time
        )
        
        AssertionHelpers.assert_availability_data(availability)
    
    def test_search_parking_lots_by_location(self, api_client: APIClient):
        """Test searching parking lots by location."""
        # NYC coordinates
        lots = api_client.search_parking_lots(
            latitude=40.7128,
            longitude=-74.0060,
            radius_km=50.0
        )
        
        assert isinstance(lots, list), "Search results should be a list"
        
        # If lots are found, validate structure
        for lot in lots:
            AssertionHelpers.assert_parking_lot_data(lot)
    
    def test_user_registration_without_login(self, api_client: APIClient):
        """Test user registration endpoint."""
        unique_email = api_client.generate_unique_email("smoke_test")
        
        user = api_client.register_user(
            email=unique_email,
            password="SmokeTest123!",
            first_name="Smoke",
            last_name="Test",
            phone="+1234567890"
        )
        
        AssertionHelpers.assert_user_data(user)
        assert user["email"] == unique_email, "Should return correct email"
    
    def test_user_login_with_valid_credentials(self, api_client: APIClient):
        """Test user login with valid credentials."""
        # First register a user
        unique_email = api_client.generate_unique_email("login_test")
        password = "LoginTest123!"
        
        api_client.register_user(
            email=unique_email,
            password=password,
            first_name="Login",
            last_name="Test",
            phone="+1234567890"
        )
        
        # Then login
        login_response = api_client.login_user(unique_email, password)
        
        assert "access_token" in login_response, "Login should return access token"
        assert "refresh_token" in login_response, "Login should return refresh token"
        assert "token_type" in login_response, "Login should return token type"
        assert login_response["token_type"] == "bearer", "Token type should be bearer"
    
    def test_unauthorized_access_to_protected_endpoint(self, api_client: APIClient):
        """Test that protected endpoints require authentication."""
        # Try to access my bookings without authentication
        response = api_client._make_request("GET", "/bookings/my", use_auth=False)
        
        assert response.status_code == 401, "Should return 401 for unauthorized access"
    
    @pytest.mark.parametrize("vehicle_type", ["car", "bike"])
    def test_availability_for_different_vehicle_types(self, api_client: APIClient, vehicle_type: str):
        """Test availability endpoint for different vehicle types."""
        start_time = api_client.generate_future_datetime(1)
        end_time = api_client.generate_future_datetime(3)
        
        availability = api_client.get_lot_availability(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type=vehicle_type,
            start_time=start_time,
            end_time=end_time
        )
        
        AssertionHelpers.assert_availability_data(availability)
        
        # Vehicle-specific assertions
        if vehicle_type == "car":
            assert availability["total_slots"] >= 50, "Should have reasonable number of car slots"
        elif vehicle_type == "bike":
            assert availability["total_slots"] >= 25, "Should have reasonable number of bike slots"
