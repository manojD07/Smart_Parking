"""Extended booking endpoint tests for 100% coverage."""

import pytest
from utils.api_client import APIClient
from utils.test_helpers import TestDataManager, AssertionHelpers
from config import config


@pytest.mark.regression
class TestExtendedBookings:
    """Test all booking endpoints for complete coverage."""
    
    def test_checkin_checkout_workflow(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test complete checkin/checkout workflow."""
        print("\n🎫 Testing Check-in/Check-out Workflow")
        
        # Create a booking
        booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            hours_from_now=0,  # Start time is now (can check-in immediately)
            duration_hours=2
        )
        
        booking = authenticated_client.create_booking(**booking_data)
        booking_id = booking["id"]
        booking_ref = booking["booking_reference"]
        
        print(f"✅ Booking created: {booking_ref}")
        
        # Test check-in
        print("\n📍 Testing Check-in")
        checkin_result = authenticated_client.checkin_booking(booking_id)
        assert "message" in checkin_result, "Check-in should return success message"
        print(f"✅ Check-in successful: {checkin_result.get('message')}")
        
        # Verify booking status after check-in
        updated_booking = authenticated_client.get_booking(booking_id)
        assert updated_booking["check_in_time"] is not None, "Check-in time should be recorded"
        print(f"✅ Check-in time recorded: {updated_booking['check_in_time']}")
        
        # Test check-out
        print("\n📍 Testing Check-out")
        checkout_result = authenticated_client.checkout_booking(booking_id)
        assert "message" in checkout_result, "Check-out should return success message"
        print(f"✅ Check-out successful: {checkout_result.get('message')}")
        
        # Verify booking status after check-out
        final_booking = authenticated_client.get_booking(booking_id)
        assert final_booking["check_out_time"] is not None, "Check-out time should be recorded"
        assert final_booking["status"] == "completed", "Booking should be completed after checkout"
        
        print(f"✅ Check-out time recorded: {final_booking['check_out_time']}")
        print(f"✅ Final booking status: {final_booking['status']}")
    
    def test_booking_reference_lookup(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test booking lookup by reference code."""
        print("\n🔍 Testing Booking Reference Lookup")
        
        # Create a booking
        booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="bike",
            hours_from_now=1,
            duration_hours=2
        )
        
        booking = authenticated_client.create_booking(**booking_data)
        booking_id = booking["id"]
        booking_ref = booking["booking_reference"]
        
        print(f"✅ Booking created with reference: {booking_ref}")
        
        # Look up booking by reference
        found_booking = authenticated_client.get_booking_by_reference(booking_ref)
        
        # Verify it's the same booking
        assert found_booking["id"] == booking_id, "Should find the correct booking"
        assert found_booking["booking_reference"] == booking_ref, "Reference should match"
        assert found_booking["vehicle_number"] == booking["vehicle_number"], "Details should match"
        
        print(f"✅ Booking found by reference: {found_booking['id']}")
        print(f"   Vehicle: {found_booking['vehicle_number']}")
        print(f"   Status: {found_booking['status']}")
        
        # Clean up
        authenticated_client.cancel_booking(booking_id)
        print("🧹 Test booking cleaned up")
    
    def test_booking_search_functionality(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test booking search with various filters."""
        print("\n🔎 Testing Booking Search Functionality")
        
        # Create multiple test bookings with different attributes
        bookings_created = []
        
        # Booking 1: Car booking
        car_booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            hours_from_now=1,
            duration_hours=2
        )
        car_booking = authenticated_client.create_booking(**car_booking_data)
        bookings_created.append(car_booking["id"])
        
        # Booking 2: Bike booking  
        bike_booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="bike",
            hours_from_now=2,
            duration_hours=1
        )
        bike_booking = authenticated_client.create_booking(**bike_booking_data)
        bookings_created.append(bike_booking["id"])
        
        print(f"✅ Created {len(bookings_created)} test bookings")
        
        # Test 1: Search all bookings
        print("\n📋 Test 1: Search all bookings")
        all_bookings = authenticated_client.search_bookings()
        booking_ids = [b["id"] for b in all_bookings]
        
        for booking_id in bookings_created:
            assert booking_id in booking_ids, f"Booking {booking_id} should be found in search"
        
        print(f"✅ Found {len(all_bookings)} total bookings")
        
        # Test 2: Search by lot ID
        print("\n📋 Test 2: Search by lot ID")
        lot_bookings = authenticated_client.search_bookings(lot_id=config.TEST_PARKING_LOT_ID)
        
        assert len(lot_bookings) >= 2, "Should find bookings for the test lot"
        for booking in lot_bookings:
            assert booking["lot_id"] == config.TEST_PARKING_LOT_ID, "All bookings should be for the specified lot"
        
        print(f"✅ Found {len(lot_bookings)} bookings for test lot")
        
        # Test 3: Search by status
        print("\n📋 Test 3: Search by status")
        active_bookings = authenticated_client.search_bookings(status="active")
        
        for booking in active_bookings:
            assert booking["status"] == "active", "All bookings should be active"
        
        print(f"✅ Found {len(active_bookings)} active bookings")
        
        # Test 4: Search with pagination
        print("\n📋 Test 4: Search with pagination")
        paginated_bookings = authenticated_client.search_bookings(limit=1)
        
        assert len(paginated_bookings) <= 1, "Should respect limit parameter"
        print(f"✅ Pagination works: returned {len(paginated_bookings)} booking(s)")
        
        # Clean up
        for booking_id in bookings_created:
            try:
                authenticated_client.cancel_booking(booking_id)
            except Exception as e:
                print(f"   Warning: Could not cancel booking {booking_id}: {e}")
        
        print("🧹 Test bookings cleaned up")
    
    def test_booking_edge_cases(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test booking edge cases and error scenarios."""
        print("\n⚠️ Testing Booking Edge Cases")
        
        # Test 1: Check-in non-existent booking
        print("\n❌ Test 1: Check-in non-existent booking")
        fake_booking_id = "00000000-0000-0000-0000-000000000000"
        
        response = authenticated_client._make_request(
            "POST", f"/bookings/{fake_booking_id}/checkin", use_auth=True
        )
        assert response.status_code == 404, "Non-existent booking check-in should fail"
        print("✅ Non-existent booking check-in correctly rejected")
        
        # Test 2: Check-out without check-in
        print("\n❌ Test 2: Check-out without check-in")
        booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            hours_from_now=1,
            duration_hours=2
        )
        
        booking = authenticated_client.create_booking(**booking_data)
        booking_id = booking["id"]
        
        response = authenticated_client._make_request(
            "POST", f"/bookings/{booking_id}/checkout", use_auth=True
        )
        # This should fail because user hasn't checked in yet
        assert response.status_code in [400, 422], "Check-out without check-in should fail"
        print("✅ Check-out without check-in correctly rejected")
        
        # Test 3: Double check-in
        print("\n❌ Test 3: Double check-in")
        # First check-in (should succeed)
        checkin_result = authenticated_client.checkin_booking(booking_id)
        assert "message" in checkin_result, "First check-in should succeed"
        
        # Second check-in (should fail)
        response = authenticated_client._make_request(
            "POST", f"/bookings/{booking_id}/checkin", use_auth=True
        )
        assert response.status_code in [400, 422], "Double check-in should fail"
        print("✅ Double check-in correctly rejected")
        
        # Test 4: Look up booking with invalid reference
        print("\n❌ Test 4: Invalid booking reference lookup")
        response = authenticated_client._make_request(
            "GET", "/bookings/reference/INVALID123", use_auth=True
        )
        assert response.status_code == 404, "Invalid reference should return 404"
        print("✅ Invalid booking reference correctly rejected")
        
        # Clean up
        authenticated_client.cancel_booking(booking_id)
        print("🧹 Test booking cleaned up")
    
    def test_booking_permissions(self, test_data_manager: TestDataManager):
        """Test booking permissions and access control."""
        print("\n🔒 Testing Booking Permissions")
        
        # Create two separate users
        user1_data = test_data_manager.generate_test_user_data("perm_user1")
        user2_data = test_data_manager.generate_test_user_data("perm_user2")
        
        client1 = APIClient()
        client2 = APIClient()
        
        try:
            # Register and login both users
            client1.register_user(**user1_data)
            client1.login_user(user1_data["email"], user1_data["password"])
            
            client2.register_user(**user2_data)
            client2.login_user(user2_data["email"], user2_data["password"])
            
            print("✅ Two users created and authenticated")
            
            # User 1 creates a booking
            booking_data = test_data_manager.generate_booking_data(
                lot_id=config.TEST_PARKING_LOT_ID,
                vehicle_type="car",
                hours_from_now=1,
                duration_hours=2
            )
            
            booking = client1.create_booking(**booking_data)
            booking_id = booking["id"]
            booking_ref = booking["booking_reference"]
            
            print(f"✅ User 1 created booking: {booking_ref}")
            
            # Test 1: User 2 tries to access User 1's booking (should fail)
            print("\n❌ Test 1: Cross-user booking access")
            response = client2._make_request("GET", f"/bookings/{booking_id}", use_auth=True)
            assert response.status_code == 403, "User should not access other user's booking"
            print("✅ Cross-user booking access correctly denied")
            
            # Test 2: User 2 tries to cancel User 1's booking (should fail)
            print("\n❌ Test 2: Cross-user booking cancellation")
            response = client2._make_request("PUT", f"/bookings/{booking_id}/cancel", use_auth=True)
            assert response.status_code == 403, "User should not cancel other user's booking"
            print("✅ Cross-user booking cancellation correctly denied")
            
            # Test 3: User 2 tries to check-in to User 1's booking (should fail)
            print("\n❌ Test 3: Cross-user booking check-in")
            response = client2._make_request("POST", f"/bookings/{booking_id}/checkin", use_auth=True)
            assert response.status_code == 403, "User should not check-in to other user's booking"
            print("✅ Cross-user booking check-in correctly denied")
            
            # Test 4: User 1 can access their own booking (should succeed)
            print("\n✅ Test 4: Owner booking access")
            own_booking = client1.get_booking(booking_id)
            assert own_booking["id"] == booking_id, "User should access their own booking"
            print("✅ Owner booking access works correctly")
            
            # Clean up
            client1.cancel_booking(booking_id)
            print("🧹 Test booking cleaned up")
            
        finally:
            client1.cleanup()
            client2.cleanup()
    
    def test_booking_lifecycle_completeness(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test complete booking lifecycle with all endpoints."""
        print("\n🔄 Testing Complete Booking Lifecycle")
        
        # Step 1: Get pricing preview
        booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            hours_from_now=1,
            duration_hours=3
        )
        
        pricing = authenticated_client.get_pricing_preview(**booking_data)
        assert "total_amount" in pricing, "Pricing preview should work"
        print(f"✅ Step 1: Pricing preview - ${pricing['total_amount']}")
        
        # Step 2: Create booking
        booking = authenticated_client.create_booking(**booking_data)
        booking_id = booking["id"]
        booking_ref = booking["booking_reference"]
        print(f"✅ Step 2: Booking created - {booking_ref}")
        
        # Step 3: Find booking in user's list
        my_bookings = authenticated_client.get_my_bookings()
        booking_ids = [b["id"] for b in my_bookings]
        assert booking_id in booking_ids, "Booking should appear in user's list"
        print("✅ Step 3: Booking found in user's list")
        
        # Step 4: Look up by reference
        ref_booking = authenticated_client.get_booking_by_reference(booking_ref)
        assert ref_booking["id"] == booking_id, "Reference lookup should work"
        print("✅ Step 4: Booking found by reference")
        
        # Step 5: Search for booking
        search_results = authenticated_client.search_bookings(lot_id=config.TEST_PARKING_LOT_ID)
        search_ids = [b["id"] for b in search_results]
        assert booking_id in search_ids, "Booking should be found in search"
        print("✅ Step 5: Booking found in search results")
        
        # Step 6: Check-in (modify to allow current time check-in)
        checkin_result = authenticated_client.checkin_booking(booking_id)
        print(f"✅ Step 6: Check-in completed")
        
        # Step 7: Check-out
        checkout_result = authenticated_client.checkout_booking(booking_id)
        print(f"✅ Step 7: Check-out completed")
        
        # Step 8: Verify final status
        final_booking = authenticated_client.get_booking(booking_id)
        assert final_booking["status"] == "completed", "Booking should be completed"
        assert final_booking["check_in_time"] is not None, "Check-in time should be recorded"
        assert final_booking["check_out_time"] is not None, "Check-out time should be recorded"
        
        print("✅ Step 8: Booking lifecycle completed successfully")
        print(f"   Final status: {final_booking['status']}")
        print(f"   Duration: {booking_data['start_time']} to {booking_data['end_time']}")
        print(f"   Total amount: ${final_booking['total_amount']}")
