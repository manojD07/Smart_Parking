"""Booking flow specific end-to-end tests."""

import pytest
from utils.api_client import APIClient
from utils.test_helpers import TestDataManager, AssertionHelpers, TestScenarios
from config import config


@pytest.mark.booking_flow
class TestBookingFlow:
    """Test specific booking flow scenarios."""
    
    def test_complete_booking_lifecycle(self, authenticated_client: APIClient, sample_booking_data: dict):
        """Test complete booking lifecycle: create, verify, cancel, verify."""
        print("\n🔄 Testing Complete Booking Lifecycle")
        
        # Execute complete booking flow
        result = TestScenarios.complete_booking_flow(authenticated_client, sample_booking_data)
        
        pricing = result["pricing"]
        booking = result["booking"]
        cancel_response = result["cancel_response"]
        final_booking = result["final_booking"]
        
        # Verify pricing was calculated
        assert pricing["total_amount"] > 0, "Pricing should be positive"
        print(f"✅ Pricing calculated: ${pricing['total_amount']}")
        
        # Verify booking was created with correct details
        assert booking["lot_id"] == sample_booking_data["lot_id"], "Lot ID should match"
        assert booking["vehicle_type"] == sample_booking_data["vehicle_type"], "Vehicle type should match"
        assert booking["vehicle_number"] == sample_booking_data["vehicle_number"], "Vehicle number should match"
        assert booking["status"] == "active", "Initial status should be active"
        print(f"✅ Booking created with reference: {booking['booking_reference']}")
        
        # Verify cancellation worked
        assert "message" in cancel_response, "Cancel response should have message"
        assert final_booking["status"] == "cancelled", "Final status should be cancelled"
        print(f"✅ Booking successfully cancelled")
    
    def test_pricing_accuracy_car_vs_bike(self, authenticated_client: APIClient):
        """Test pricing accuracy for car vs bike bookings."""
        print("\n💰 Testing Pricing Accuracy: Car vs Bike")
        
        start_time = authenticated_client.generate_future_datetime(1)
        end_time = authenticated_client.generate_future_datetime(3)  # 2 hours
        
        # Get pricing for car
        car_pricing = authenticated_client.get_pricing_preview(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            start_time=start_time,
            end_time=end_time
        )
        
        # Get pricing for bike
        bike_pricing = authenticated_client.get_pricing_preview(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="bike",
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify pricing structure
        assert "total_amount" in car_pricing, "Car pricing should include total amount"
        assert "total_amount" in bike_pricing, "Bike pricing should include total amount"
        assert "duration_hours" in car_pricing, "Car pricing should include duration"
        assert "duration_hours" in bike_pricing, "Bike pricing should include duration"
        
        car_amount = car_pricing["total_amount"]
        bike_amount = bike_pricing["total_amount"]
        duration = car_pricing["duration_hours"]
        
        # Both should have same duration
        assert car_pricing["duration_hours"] == bike_pricing["duration_hours"], "Duration should be same"
        
        # Car should typically be more expensive than bike
        assert car_amount > bike_amount, "Car should be more expensive than bike"
        
        print(f"✅ Car pricing: ${car_amount} for {duration} hours")
        print(f"✅ Bike pricing: ${bike_amount} for {duration} hours")
        print(f"✅ Price difference: ${car_amount - bike_amount}")
    
    def test_booking_with_different_durations(self, authenticated_client: APIClient):
        """Test booking pricing for different durations."""
        print("\n⏰ Testing Booking Durations and Pricing")
        
        durations = [1, 2, 4, 8]  # Different hour durations
        pricing_results = []
        
        for duration in durations:
            start_time = authenticated_client.generate_future_datetime(1)
            end_time = authenticated_client.generate_future_datetime(1 + duration)
            
            pricing = authenticated_client.get_pricing_preview(
                lot_id=config.TEST_PARKING_LOT_ID,
                vehicle_type="car",
                start_time=start_time,
                end_time=end_time
            )
            
            pricing_results.append({
                "duration": duration,
                "amount": pricing["total_amount"],
                "rate": pricing["total_amount"] / duration
            })
            
            print(f"✅ {duration}h duration: ${pricing['total_amount']} (${pricing['total_amount'] / duration:.2f}/hour)")
        
        # Verify pricing increases with duration
        for i in range(1, len(pricing_results)):
            prev_amount = pricing_results[i-1]["amount"]
            curr_amount = pricing_results[i]["amount"]
            assert curr_amount > prev_amount, f"Longer duration should cost more: {curr_amount} > {prev_amount}"
        
        print("✅ Pricing correctly increases with duration")
    
    def test_slot_allocation_and_release(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test that slots are properly allocated and released."""
        print("\n🅿️ Testing Slot Allocation and Release")
        
        # Check initial availability
        start_time = authenticated_client.generate_future_datetime(1)
        end_time = authenticated_client.generate_future_datetime(3)
        
        initial_availability = authenticated_client.get_lot_availability(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            start_time=start_time,
            end_time=end_time
        )
        
        initial_available = initial_availability["available_slots"]
        print(f"✅ Initial available car slots: {initial_available}")
        
        # Create booking
        booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            hours_from_now=1,
            duration_hours=2
        )
        
        booking = authenticated_client.create_booking(**booking_data)
        assert "slot_id" in booking, "Booking should include slot assignment"
        
        slot_id = booking["slot_id"]
        booking_id = booking["id"]
        print(f"✅ Booking created, assigned slot: {slot_id}")
        
        # Check availability after booking (might be same due to future booking)
        post_booking_availability = authenticated_client.get_lot_availability(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            start_time=start_time,
            end_time=end_time
        )
        
        post_booking_available = post_booking_availability["available_slots"]
        print(f"✅ Available slots after booking: {post_booking_available}")
        
        # Cancel booking
        cancel_response = authenticated_client.cancel_booking(booking_id)
        assert "message" in cancel_response, "Cancel should return success message"
        print(f"✅ Booking cancelled: {cancel_response.get('message')}")
        
        # Check availability after cancellation
        post_cancel_availability = authenticated_client.get_lot_availability(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            start_time=start_time,
            end_time=end_time
        )
        
        post_cancel_available = post_cancel_availability["available_slots"]
        print(f"✅ Available slots after cancellation: {post_cancel_available}")
        
        # Availability should be restored after cancellation
        assert post_cancel_available >= post_booking_available, "Slots should be available after cancellation"
    
    def test_concurrent_booking_scenario(self, test_data_manager: TestDataManager):
        """Test scenario simulating concurrent bookings by different users."""
        print("\n👥 Testing Concurrent Booking Scenario")
        
        # Create two separate users
        user1_data = test_data_manager.generate_test_user_data("concurrent_user1")
        user2_data = test_data_manager.generate_test_user_data("concurrent_user2")
        
        # Create two API clients
        client1 = APIClient()
        client2 = APIClient()
        
        try:
            # Register and login both users
            client1.register_user(**user1_data)
            client1.login_user(user1_data["email"], user1_data["password"])
            
            client2.register_user(**user2_data)
            client2.login_user(user2_data["email"], user2_data["password"])
            
            print(f"✅ Two users registered and logged in")
            
            # Both users try to book in same time slot
            start_time = client1.generate_future_datetime(1)
            end_time = client1.generate_future_datetime(3)
            
            booking_data1 = {
                "lot_id": config.TEST_PARKING_LOT_ID,
                "vehicle_type": "car",
                "vehicle_number": "USER1CAR",
                "start_time": start_time,
                "end_time": end_time
            }
            
            booking_data2 = {
                "lot_id": config.TEST_PARKING_LOT_ID,
                "vehicle_type": "car",
                "vehicle_number": "USER2CAR",
                "start_time": start_time,
                "end_time": end_time
            }
            
            # Create bookings (both should succeed as different slots)
            booking1 = client1.create_booking(**booking_data1)
            booking2 = client2.create_booking(**booking_data2)
            
            AssertionHelpers.assert_booking_data(booking1)
            AssertionHelpers.assert_booking_data(booking2)
            
            # Verify different slots assigned
            assert booking1["slot_id"] != booking2["slot_id"], "Different slots should be assigned"
            
            print(f"✅ User 1 booking: {booking1['booking_reference']} (slot: {booking1['slot_id']})")
            print(f"✅ User 2 booking: {booking2['booking_reference']} (slot: {booking2['slot_id']})")
            
            # Verify both users can see their own bookings
            user1_bookings = client1.get_my_bookings()
            user2_bookings = client2.get_my_bookings()
            
            user1_refs = [b["booking_reference"] for b in user1_bookings]
            user2_refs = [b["booking_reference"] for b in user2_bookings]
            
            assert booking1["booking_reference"] in user1_refs, "User 1 should see their booking"
            assert booking2["booking_reference"] in user2_refs, "User 2 should see their booking"
            assert booking1["booking_reference"] not in user2_refs, "User 2 should not see User 1's booking"
            assert booking2["booking_reference"] not in user1_refs, "User 1 should not see User 2's booking"
            
            print("✅ Users can only see their own bookings")
            
            # Clean up
            client1.cancel_booking(booking1["id"])
            client2.cancel_booking(booking2["id"])
            print("🧹 Bookings cleaned up")
            
        finally:
            client1.cleanup()
            client2.cleanup()
    
    def test_booking_reference_uniqueness(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test that booking references are unique."""
        print("\n🔢 Testing Booking Reference Uniqueness")
        
        booking_references = set()
        created_bookings = []
        
        # Create multiple bookings
        for i in range(5):
            booking_data = test_data_manager.generate_booking_data(
                lot_id=config.TEST_PARKING_LOT_ID,
                vehicle_type="car",
                hours_from_now=i + 1,
                duration_hours=1
            )
            
            booking = authenticated_client.create_booking(**booking_data)
            reference = booking["booking_reference"]
            
            assert reference not in booking_references, f"Booking reference {reference} should be unique"
            booking_references.add(reference)
            created_bookings.append(booking["id"])
            
            print(f"✅ Booking {i+1}: {reference} (unique)")
        
        print(f"✅ All {len(booking_references)} booking references are unique")
        
        # Clean up
        for booking_id in created_bookings:
            authenticated_client.cancel_booking(booking_id)
        print("🧹 All test bookings cleaned up")
    
    @pytest.mark.parametrize("vehicle_type,expected_min_slots", [
        ("car", 50),
        ("bike", 25)
    ])
    def test_vehicle_specific_availability(self, authenticated_client: APIClient, vehicle_type: str, expected_min_slots: int):
        """Test availability checks for specific vehicle types."""
        print(f"\n🚗🚲 Testing {vehicle_type.title()} Availability")
        
        start_time = authenticated_client.generate_future_datetime(1)
        end_time = authenticated_client.generate_future_datetime(3)
        
        availability = authenticated_client.get_lot_availability(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type=vehicle_type,
            start_time=start_time,
            end_time=end_time
        )
        
        AssertionHelpers.assert_availability_data(availability)
        
        # Check minimum expected slots
        assert availability["total_slots"] >= expected_min_slots, f"Should have at least {expected_min_slots} {vehicle_type} slots"
        
        print(f"✅ {vehicle_type.title()} availability: {availability['available_slots']}/{availability['total_slots']} slots")
        print(f"✅ Occupancy rate: {availability['occupancy_rate']:.1f}%")
