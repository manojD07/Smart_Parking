"""Complete user journey end-to-end tests."""

import pytest
from utils.api_client import APIClient
from utils.test_helpers import TestDataManager, AssertionHelpers, TestScenarios
from config import config


@pytest.mark.user_journey
class TestCompleteUserJourney:
    """Test complete user journeys from registration to booking completion."""
    
    def test_new_user_complete_journey(self, api_client: APIClient, test_data_manager: TestDataManager):
        """Test complete journey for a new user: register, login, browse, book, cancel."""
        # Step 1: Generate test data
        user_data = test_data_manager.generate_test_user_data("journey_test")
        
        # Step 2: Complete user registration and login
        print("\n📝 Step 1: User Registration & Login")
        registration_result = TestScenarios.complete_user_registration_flow(api_client, user_data)
        
        user = registration_result["user"]
        access_token = registration_result["access_token"]
        
        print(f"✅ User registered and logged in: {user['email']}")
        
        # Step 3: Browse parking lots
        print("\n🅿️ Step 2: Browse Parking Lots")
        lots = api_client.get_parking_lots(limit=10)
        assert len(lots) > 0, "Should find parking lots"
        
        target_lot = lots[0]
        lot_id = target_lot["id"]
        print(f"✅ Found {len(lots)} parking lots, selected: {target_lot['name']}")
        
        # Step 4: Check lot details and availability
        print("\n🔍 Step 3: Check Lot Details & Availability")
        lot_details = api_client.get_parking_lot(lot_id)
        AssertionHelpers.assert_parking_lot_data(lot_details)
        
        # Check availability for cars
        start_time = api_client.generate_future_datetime(2)
        end_time = api_client.generate_future_datetime(4)
        
        availability = api_client.get_lot_availability(
            lot_id=lot_id,
            vehicle_type="car",
            start_time=start_time,
            end_time=end_time
        )
        AssertionHelpers.assert_availability_data(availability)
        
        assert availability["available_slots"] > 0, "Should have available slots for booking"
        print(f"✅ Lot has {availability['available_slots']} available car slots")
        
        # Step 5: Get pricing preview
        print("\n💰 Step 4: Get Pricing Preview")
        pricing = api_client.get_pricing_preview(
            lot_id=lot_id,
            vehicle_type="car",
            start_time=start_time,
            end_time=end_time
        )
        
        assert "total_amount" in pricing, "Pricing should include total amount"
        assert pricing["total_amount"] > 0, "Pricing should be positive"
        print(f"✅ Booking cost: ${pricing['total_amount']} for {pricing.get('duration_hours', 2)} hours")
        
        # Step 6: Create booking
        print("\n📅 Step 5: Create Booking")
        booking_data = {
            "lot_id": lot_id,
            "vehicle_type": "car",
            "vehicle_number": api_client.generate_unique_vehicle_number("JOURNEY"),
            "start_time": start_time,
            "end_time": end_time
        }
        
        booking = api_client.create_booking(**booking_data)
        AssertionHelpers.assert_booking_data(booking)
        
        booking_id = booking["id"]
        booking_ref = booking["booking_reference"]
        print(f"✅ Booking created: {booking_ref} (ID: {booking_id})")
        
        # Step 7: Verify booking in user's bookings list
        print("\n📋 Step 6: Verify Booking in User's List")
        my_bookings = api_client.get_my_bookings()
        booking_ids = [b["id"] for b in my_bookings]
        
        assert booking_id in booking_ids, "Created booking should appear in user's bookings"
        print(f"✅ Booking appears in user's bookings list ({len(my_bookings)} total bookings)")
        
        # Step 8: Get specific booking details
        print("\n📄 Step 7: Get Booking Details")
        booking_details = api_client.get_booking(booking_id)
        AssertionHelpers.assert_booking_data(booking_details)
        
        assert booking_details["id"] == booking_id, "Retrieved booking should match"
        assert booking_details["status"] == "active", "Booking should be active"
        print(f"✅ Booking details retrieved: Status = {booking_details['status']}")
        
        # Step 9: Cancel booking
        print("\n❌ Step 8: Cancel Booking")
        cancel_response = api_client.cancel_booking(booking_id)
        assert "message" in cancel_response, "Cancel response should include message"
        print(f"✅ Booking cancelled: {cancel_response.get('message', 'Success')}")
        
        # Step 10: Verify cancellation
        print("\n✅ Step 9: Verify Cancellation")
        cancelled_booking = api_client.get_booking(booking_id)
        assert cancelled_booking["status"] == "cancelled", "Booking should be cancelled"
        print(f"✅ Booking status confirmed: {cancelled_booking['status']}")
        
        # Step 11: Check updated bookings list
        print("\n📊 Step 10: Final Verification")
        final_bookings = api_client.get_my_bookings()
        cancelled_bookings = [b for b in final_bookings if b["status"] == "cancelled"]
        
        assert len(cancelled_bookings) > 0, "Should have cancelled bookings"
        print(f"✅ Journey complete! User has {len(final_bookings)} total bookings, {len(cancelled_bookings)} cancelled")
    
    def test_multiple_bookings_scenario(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test user creating multiple bookings for different time slots."""
        print("\n🔄 Testing Multiple Bookings Scenario")
        
        # Create 3 bookings for different time slots
        booking_ids = []
        
        for i in range(3):
            print(f"\n📅 Creating booking {i+1}/3")
            
            booking_data = test_data_manager.generate_booking_data(
                lot_id=config.TEST_PARKING_LOT_ID,
                vehicle_type="car" if i % 2 == 0 else "bike",
                hours_from_now=i + 1,
                duration_hours=2
            )
            
            booking = authenticated_client.create_booking(**booking_data)
            AssertionHelpers.assert_booking_data(booking)
            booking_ids.append(booking["id"])
            
            print(f"✅ Booking {i+1} created: {booking['booking_reference']}")
        
        # Verify all bookings exist
        print(f"\n📋 Verifying {len(booking_ids)} bookings exist")
        my_bookings = authenticated_client.get_my_bookings()
        my_booking_ids = [b["id"] for b in my_bookings]
        
        for booking_id in booking_ids:
            assert booking_id in my_booking_ids, f"Booking {booking_id} should exist"
        
        print(f"✅ All {len(booking_ids)} bookings verified in user's list")
        
        # Cancel all bookings
        print(f"\n❌ Cancelling all {len(booking_ids)} bookings")
        for i, booking_id in enumerate(booking_ids):
            cancel_response = authenticated_client.cancel_booking(booking_id)
            assert "message" in cancel_response, f"Cancel response {i+1} should include message"
            print(f"✅ Booking {i+1} cancelled")
        
        # Verify all are cancelled
        final_bookings = authenticated_client.get_my_bookings()
        active_bookings = [b for b in final_bookings if b["status"] == "active"]
        cancelled_bookings = [b for b in final_bookings if b["status"] == "cancelled"]
        
        assert len(cancelled_bookings) >= 3, "Should have at least 3 cancelled bookings"
        print(f"✅ Final status: {len(cancelled_bookings)} cancelled, {len(active_bookings)} active")
    
    def test_car_and_bike_booking_journey(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test booking both car and bike slots."""
        print("\n🚗🚲 Testing Car and Bike Booking Journey")
        
        vehicle_types = ["car", "bike"]
        bookings_created = []
        
        for vehicle_type in vehicle_types:
            print(f"\n📅 Creating {vehicle_type} booking")
            
            # Check availability first
            start_time = authenticated_client.generate_future_datetime(1)
            end_time = authenticated_client.generate_future_datetime(3)
            
            availability = authenticated_client.get_lot_availability(
                lot_id=config.TEST_PARKING_LOT_ID,
                vehicle_type=vehicle_type,
                start_time=start_time,
                end_time=end_time
            )
            
            assert availability["available_slots"] > 0, f"Should have available {vehicle_type} slots"
            print(f"✅ {availability['available_slots']} {vehicle_type} slots available")
            
            # Get pricing
            pricing = authenticated_client.get_pricing_preview(
                lot_id=config.TEST_PARKING_LOT_ID,
                vehicle_type=vehicle_type,
                start_time=start_time,
                end_time=end_time
            )
            
            print(f"💰 {vehicle_type.title()} pricing: ${pricing['total_amount']}")
            
            # Create booking
            booking_data = {
                "lot_id": config.TEST_PARKING_LOT_ID,
                "vehicle_type": vehicle_type,
                "vehicle_number": authenticated_client.generate_unique_vehicle_number(vehicle_type.upper()),
                "start_time": start_time,
                "end_time": end_time
            }
            
            booking = authenticated_client.create_booking(**booking_data)
            AssertionHelpers.assert_booking_data(booking)
            bookings_created.append(booking)
            
            print(f"✅ {vehicle_type.title()} booking created: {booking['booking_reference']}")
        
        # Verify both bookings exist
        my_bookings = authenticated_client.get_my_bookings()
        created_refs = [b["booking_reference"] for b in bookings_created]
        my_refs = [b["booking_reference"] for b in my_bookings]
        
        for ref in created_refs:
            assert ref in my_refs, f"Booking {ref} should exist in user's bookings"
        
        print(f"✅ Both car and bike bookings verified")
        
        # Compare pricing between car and bike
        car_booking = next(b for b in bookings_created if b["vehicle_type"] == "car")
        bike_booking = next(b for b in bookings_created if b["vehicle_type"] == "bike")
        
        car_amount = float(car_booking["total_amount"])
        bike_amount = float(bike_booking["total_amount"])
        
        print(f"💰 Car booking: ${car_amount}, Bike booking: ${bike_amount}")
        
        # Typically car should be more expensive than bike
        if car_amount > bike_amount:
            print("✅ Car booking is more expensive than bike booking (as expected)")
        
        # Clean up - cancel both bookings
        for booking in bookings_created:
            authenticated_client.cancel_booking(booking["id"])
            print(f"❌ Cancelled {booking['vehicle_type']} booking: {booking['booking_reference']}")
    
    def test_booking_validation_edge_cases(self, authenticated_client: APIClient):
        """Test booking validation with edge cases."""
        print("\n🔍 Testing Booking Validation Edge Cases")
        
        # Test 1: Past start time (should fail)
        print("\n❌ Test 1: Booking with past start time")
        past_booking_data = {
            "lot_id": config.TEST_PARKING_LOT_ID,
            "vehicle_type": "car",
            "vehicle_number": "PAST123",
            "start_time": "2023-01-01T10:00:00Z",  # Past date
            "end_time": "2023-01-01T12:00:00Z"
        }
        
        response = authenticated_client._make_request(
            "POST", "/bookings/", data=past_booking_data, use_auth=True
        )
        assert response.status_code == 422, "Past booking should be rejected"
        print("✅ Past booking correctly rejected")
        
        # Test 2: End time before start time (should fail)
        print("\n❌ Test 2: End time before start time")
        start_time = authenticated_client.generate_future_datetime(2)
        end_time = authenticated_client.generate_future_datetime(1)  # Earlier than start
        
        invalid_time_data = {
            "lot_id": config.TEST_PARKING_LOT_ID,
            "vehicle_type": "car",
            "vehicle_number": "INVALID123",
            "start_time": start_time,
            "end_time": end_time
        }
        
        response = authenticated_client._make_request(
            "POST", "/bookings/", data=invalid_time_data, use_auth=True
        )
        assert response.status_code == 422, "Invalid time range should be rejected"
        print("✅ Invalid time range correctly rejected")
        
        # Test 3: Valid booking (should succeed)
        print("\n✅ Test 3: Valid booking")
        valid_start = authenticated_client.generate_future_datetime(1)
        valid_end = authenticated_client.generate_future_datetime(3)
        
        valid_booking_data = {
            "lot_id": config.TEST_PARKING_LOT_ID,
            "vehicle_type": "car",
            "vehicle_number": "VALID123",
            "start_time": valid_start,
            "end_time": valid_end
        }
        
        booking = authenticated_client.create_booking(**valid_booking_data)
        AssertionHelpers.assert_booking_data(booking)
        print(f"✅ Valid booking created: {booking['booking_reference']}")
        
        # Clean up
        authenticated_client.cancel_booking(booking["id"])
        print("🧹 Test booking cleaned up")
