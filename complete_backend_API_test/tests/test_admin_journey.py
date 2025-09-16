"""Admin journey end-to-end tests."""

import pytest
from utils.api_client import APIClient
from utils.test_helpers import TestDataManager, AssertionHelpers
from config import config


@pytest.mark.admin_journey
class TestAdminJourney:
    """Test admin-specific functionality and journeys."""
    
    def test_admin_parking_lot_management(self, admin_client: APIClient, sample_lot_data: dict):
        """Test admin can create and manage parking lots."""
        print("\n🔧 Testing Admin Parking Lot Management")
        
        # Create new parking lot
        print("\n📍 Creating new parking lot")
        created_lot = admin_client.create_parking_lot(sample_lot_data)
        
        AssertionHelpers.assert_parking_lot_data(created_lot)
        lot_id = created_lot["id"]
        
        print(f"✅ Parking lot created: {created_lot['name']} (ID: {lot_id})")
        
        # Verify lot appears in general listing
        print("\n📋 Verifying lot appears in public listing")
        all_lots = admin_client.get_parking_lots()
        lot_ids = [lot["id"] for lot in all_lots]
        
        assert lot_id in lot_ids, "Created lot should appear in public listing"
        print(f"✅ New lot appears in public listing ({len(all_lots)} total lots)")
        
        # Get specific lot details
        print("\n🔍 Getting specific lot details")
        lot_details = admin_client.get_parking_lot(lot_id)
        
        AssertionHelpers.assert_parking_lot_data(lot_details)
        assert lot_details["id"] == lot_id, "Retrieved lot should match created lot"
        assert lot_details["name"] == sample_lot_data["name"], "Lot name should match"
        
        print(f"✅ Lot details retrieved: {lot_details['name']}")
        
        # Check lot has slots
        print("\n🅿️ Checking lot slots")
        slots = admin_client.get_lot_slots(lot_id, limit=10)
        
        assert isinstance(slots, list), "Slots should be a list"
        assert len(slots) > 0, "New lot should have slots"
        
        car_slots = [s for s in slots if s["slot_type"] == "car"]
        bike_slots = [s for s in slots if s["slot_type"] == "bike"]
        
        print(f"✅ Lot has {len(car_slots)} car slots and {len(bike_slots)} bike slots")
        
        # Test lot availability
        print("\n📊 Testing lot availability")
        start_time = admin_client.generate_future_datetime(1)
        end_time = admin_client.generate_future_datetime(3)
        
        availability = admin_client.get_lot_availability(
            lot_id=lot_id,
            vehicle_type="car",
            start_time=start_time,
            end_time=end_time
        )
        
        AssertionHelpers.assert_availability_data(availability)
        print(f"✅ Availability: {availability['available_slots']}/{availability['total_slots']} car slots")
    
    def test_admin_lot_statistics(self, admin_client: APIClient):
        """Test admin can view parking lot statistics."""
        print("\n📈 Testing Admin Lot Statistics")
        
        # Get statistics for test lot
        stats = admin_client.get_lot_statistics(config.TEST_PARKING_LOT_ID)
        
        # Verify statistics structure
        expected_fields = [
            "lot_id", "total_bookings", "active_bookings", "completed_bookings",
            "cancelled_bookings", "total_revenue", "occupancy_rate"
        ]
        
        AssertionHelpers.assert_response_success(stats, expected_fields)
        
        # Verify data types and ranges
        assert isinstance(stats["total_bookings"], int), "Total bookings should be integer"
        assert isinstance(stats["active_bookings"], int), "Active bookings should be integer"
        assert isinstance(stats["completed_bookings"], int), "Completed bookings should be integer"
        assert isinstance(stats["cancelled_bookings"], int), "Cancelled bookings should be integer"
        assert isinstance(stats["total_revenue"], (int, float)), "Total revenue should be numeric"
        assert isinstance(stats["occupancy_rate"], (int, float)), "Occupancy rate should be numeric"
        
        # Verify logical constraints
        total_calculated = (
            stats["active_bookings"] + 
            stats["completed_bookings"] + 
            stats["cancelled_bookings"]
        )
        assert total_calculated <= stats["total_bookings"], "Sum of status bookings should not exceed total"
        
        assert 0 <= stats["occupancy_rate"] <= 100, "Occupancy rate should be 0-100%"
        assert stats["total_revenue"] >= 0, "Total revenue should be non-negative"
        
        print(f"✅ Lot statistics:")
        print(f"   📊 Total bookings: {stats['total_bookings']}")
        print(f"   🟢 Active: {stats['active_bookings']}")
        print(f"   ✅ Completed: {stats['completed_bookings']}")
        print(f"   ❌ Cancelled: {stats['cancelled_bookings']}")
        print(f"   💰 Revenue: ${stats['total_revenue']}")
        print(f"   📈 Occupancy: {stats['occupancy_rate']:.1f}%")
    
    def test_admin_can_view_all_bookings_data(self, admin_client: APIClient):
        """Test that admin can access comprehensive booking data."""
        print("\n👁️ Testing Admin Access to Booking Data")
        
        # Admin should be able to get detailed lot information
        lot_details = admin_client.get_parking_lot(config.TEST_PARKING_LOT_ID)
        AssertionHelpers.assert_parking_lot_data(lot_details)
        
        print(f"✅ Admin can access lot details: {lot_details['name']}")
        
        # Admin should be able to get comprehensive slot information
        all_slots = admin_client.get_lot_slots(config.TEST_PARKING_LOT_ID, limit=100)
        
        car_slots = [s for s in all_slots if s["slot_type"] == "car"]
        bike_slots = [s for s in all_slots if s["slot_type"] == "bike"]
        occupied_slots = [s for s in all_slots if s["is_occupied"]]
        available_slots = [s for s in all_slots if not s["is_occupied"]]
        
        print(f"✅ Slot overview:")
        print(f"   🚗 Car slots: {len(car_slots)}")
        print(f"   🚲 Bike slots: {len(bike_slots)}")
        print(f"   🔴 Occupied: {len(occupied_slots)}")
        print(f"   🟢 Available: {len(available_slots)}")
        
        # Verify slot data integrity
        assert len(car_slots) + len(bike_slots) == len(all_slots), "All slots should be categorized"
        assert len(occupied_slots) + len(available_slots) == len(all_slots), "All slots should have status"
    
    def test_admin_parking_lot_creation_validation(self, admin_client: APIClient, test_data_manager: TestDataManager):
        """Test validation of parking lot creation by admin."""
        print("\n✅ Testing Parking Lot Creation Validation")
        
        # Test 1: Valid parking lot creation
        print("\n✅ Test 1: Valid parking lot")
        valid_lot_data = test_data_manager.generate_parking_lot_data("valid_test")
        
        created_lot = admin_client.create_parking_lot(valid_lot_data)
        AssertionHelpers.assert_parking_lot_data(created_lot)
        
        print(f"✅ Valid lot created: {created_lot['name']}")
        
        # Test 2: Invalid lot data (should be caught by validation)
        print("\n❌ Test 2: Invalid coordinates")
        invalid_lot_data = test_data_manager.generate_parking_lot_data("invalid_test")
        invalid_lot_data["latitude"] = 999  # Invalid latitude
        invalid_lot_data["longitude"] = 999  # Invalid longitude
        
        response = admin_client._make_request(
            "POST", "/parking/admin/lots", data=invalid_lot_data, use_auth=True
        )
        
        # Should be rejected (422 for validation error)
        assert response.status_code == 422, "Invalid coordinates should be rejected"
        print("✅ Invalid coordinates correctly rejected")
        
        # Test 3: Negative slot counts
        print("\n❌ Test 3: Negative slot counts")
        negative_slots_data = test_data_manager.generate_parking_lot_data("negative_test")
        negative_slots_data["total_car_slots"] = -10
        negative_slots_data["total_bike_slots"] = -5
        
        response = admin_client._make_request(
            "POST", "/parking/admin/lots", data=negative_slots_data, use_auth=True
        )
        
        assert response.status_code == 422, "Negative slots should be rejected"
        print("✅ Negative slot counts correctly rejected")
    
    def test_regular_user_cannot_access_admin_endpoints(self, authenticated_client: APIClient, sample_lot_data: dict):
        """Test that regular users cannot access admin endpoints."""
        print("\n🔒 Testing Admin Endpoint Security")
        
        # Test 1: Try to create parking lot as regular user
        print("\n❌ Test 1: Regular user tries to create parking lot")
        response = authenticated_client._make_request(
            "POST", "/parking/admin/lots", data=sample_lot_data, use_auth=True
        )
        
        assert response.status_code == 403, "Regular user should be forbidden from creating lots"
        print("✅ Regular user correctly forbidden from creating lots")
        
        # Test 2: Try to access lot statistics as regular user
        print("\n❌ Test 2: Regular user tries to access lot statistics")
        response = authenticated_client._make_request(
            "GET", f"/parking/admin/lots/{config.TEST_PARKING_LOT_ID}/statistics", use_auth=True
        )
        
        assert response.status_code == 403, "Regular user should be forbidden from accessing statistics"
        print("✅ Regular user correctly forbidden from accessing statistics")
    
    def test_admin_comprehensive_workflow(self, admin_client: APIClient, test_data_manager: TestDataManager):
        """Test comprehensive admin workflow."""
        print("\n🔄 Testing Comprehensive Admin Workflow")
        
        # Step 1: Create new parking lot
        print("\n📍 Step 1: Create parking lot")
        lot_data = test_data_manager.generate_parking_lot_data("workflow_test")
        
        created_lot = admin_client.create_parking_lot(lot_data)
        lot_id = created_lot["id"]
        
        print(f"✅ Created lot: {created_lot['name']} (ID: {lot_id})")
        
        # Step 2: Verify lot is accessible to public
        print("\n🔍 Step 2: Verify public accessibility")
        public_client = APIClient()
        
        try:
            public_lot = public_client.get_parking_lot(lot_id)
            assert public_lot["id"] == lot_id, "Public should be able to access new lot"
            print("✅ Lot is publicly accessible")
        finally:
            public_client.cleanup()
        
        # Step 3: Check initial statistics
        print("\n📊 Step 3: Check initial statistics")
        initial_stats = admin_client.get_lot_statistics(lot_id)
        
        assert initial_stats["total_bookings"] == 0, "New lot should have no bookings"
        assert initial_stats["total_revenue"] == 0, "New lot should have no revenue"
        print("✅ Initial statistics are correct (zero bookings/revenue)")
        
        # Step 4: Simulate user creating booking for this lot
        print("\n👤 Step 4: Simulate user booking")
        user_client = APIClient()
        
        try:
            # Create and login test user
            user_data = test_data_manager.generate_test_user_data("workflow_user")
            user_client.register_user(**user_data)
            user_client.login_user(user_data["email"], user_data["password"])
            
            # Create booking
            booking_data = test_data_manager.generate_booking_data(
                lot_id=lot_id,
                vehicle_type="car",
                hours_from_now=1,
                duration_hours=2
            )
            
            booking = user_client.create_booking(**booking_data)
            booking_id = booking["id"]
            
            print(f"✅ User booking created: {booking['booking_reference']}")
            
            # Step 5: Check updated statistics
            print("\n📈 Step 5: Check updated statistics")
            updated_stats = admin_client.get_lot_statistics(lot_id)
            
            assert updated_stats["total_bookings"] >= 1, "Should have at least one booking"
            assert updated_stats["active_bookings"] >= 1, "Should have at least one active booking"
            assert updated_stats["total_revenue"] > 0, "Should have some revenue"
            
            print(f"✅ Updated statistics:")
            print(f"   📊 Total bookings: {updated_stats['total_bookings']}")
            print(f"   💰 Revenue: ${updated_stats['total_revenue']}")
            
            # Clean up booking
            user_client.cancel_booking(booking_id)
            print("🧹 User booking cleaned up")
            
        finally:
            user_client.cleanup()
        
        print("✅ Comprehensive admin workflow completed successfully")
