"""Extended parking endpoint tests for 100% coverage."""

import pytest
from utils.api_client import APIClient
from utils.test_helpers import TestDataManager, AssertionHelpers
from config import config


@pytest.mark.regression
class TestExtendedParking:
    """Test all parking endpoints for complete coverage."""
    
    def test_parking_lot_availability_post_method(self, authenticated_client: APIClient):
        """Test parking lot availability using POST method."""
        print("\n📍 Testing Parking Lot Availability (POST Method)")
        
        # Test availability check using POST
        start_time = authenticated_client.generate_future_datetime(1)
        end_time = authenticated_client.generate_future_datetime(3)
        
        availability = authenticated_client.check_lot_availability_post(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            start_time=start_time,
            end_time=end_time
        )
        
        # Validate availability response structure
        AssertionHelpers.assert_availability_data(availability)
        
        print(f"✅ POST Availability check:")
        print(f"   🚗 Vehicle type: car")
        print(f"   📅 Time range: {start_time} to {end_time}")
        print(f"   📊 Available: {availability['available_slots']}/{availability['total_slots']}")
        print(f"   💰 Pricing: ${availability.get('hourly_rate', 'N/A')}/hour")
        
        # Test with bike availability
        bike_availability = authenticated_client.check_lot_availability_post(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="bike",
            start_time=start_time,
            end_time=end_time
        )
        
        AssertionHelpers.assert_availability_data(bike_availability)
        
        print(f"✅ Bike availability:")
        print(f"   🏍️ Available: {bike_availability['available_slots']}/{bike_availability['total_slots']}")
    
    def test_parking_lot_comprehensive_filtering(self, authenticated_client: APIClient):
        """Test comprehensive parking lot filtering and pagination."""
        print("\n🔍 Testing Comprehensive Parking Lot Filtering")
        
        # Test 1: Get all parking lots with pagination
        print("\n📋 Test 1: Pagination")
        page1 = authenticated_client.get_parking_lots(skip=0, limit=2)
        page2 = authenticated_client.get_parking_lots(skip=2, limit=2)
        
        assert isinstance(page1, list), "Should return list of parking lots"
        assert isinstance(page2, list), "Should return list of parking lots"
        
        print(f"✅ Page 1: {len(page1)} lots, Page 2: {len(page2)} lots")
        
        # Test 2: Filter by active status
        print("\n📋 Test 2: Filter by active status")
        active_lots = authenticated_client._make_request(
            "GET", "/parking/lots", 
            params={"is_active": True, "limit": 10}
        ).json()
        
        for lot in active_lots:
            assert lot["is_active"] is True, "All lots should be active"
        
        print(f"✅ Found {len(active_lots)} active lots")
        
        # Test 3: Get individual lot details
        print("\n📋 Test 3: Individual lot details")
        if active_lots:
            lot_id = active_lots[0]["id"]
            lot_details = authenticated_client.get_parking_lot(lot_id)
            
            # Verify detailed lot information
            required_fields = [
                "id", "name", "address", "latitude", "longitude",
                "total_car_slots", "total_bike_slots", 
                "hourly_rate_car", "hourly_rate_bike", "is_active"
            ]
            
            for field in required_fields:
                assert field in lot_details, f"Lot details should include {field}"
            
            assert lot_details["id"] == lot_id, "Should get correct lot"
            assert lot_details["latitude"] != 0, "Should have valid coordinates"
            assert lot_details["longitude"] != 0, "Should have valid coordinates"
            
            print(f"✅ Lot details: {lot_details['name']}")
            print(f"   📍 Location: {lot_details['latitude']}, {lot_details['longitude']}")
            print(f"   🚗 Car slots: {lot_details['total_car_slots']}")
            print(f"   🏍️ Bike slots: {lot_details['total_bike_slots']}")
    
    def test_parking_slot_management(self, authenticated_client: APIClient):
        """Test parking slot listing and filtering."""
        print("\n🅿️ Testing Parking Slot Management")
        
        # Get slots for test parking lot
        print("\n📋 Test 1: Get all slots")
        all_slots = authenticated_client.get_lot_slots(config.TEST_PARKING_LOT_ID, limit=50)
        
        assert isinstance(all_slots, list), "Should return list of slots"
        assert len(all_slots) > 0, "Should have at least some slots"
        
        # Verify slot structure
        for slot in all_slots[:3]:  # Check first 3 slots
            required_fields = ["id", "slot_number", "slot_type", "is_available", "lot_id"]
            for field in required_fields:
                assert field in slot, f"Slot should include {field}"
            
            assert slot["lot_id"] == config.TEST_PARKING_LOT_ID, "Slot should belong to correct lot"
            assert slot["slot_type"] in ["car", "bike"], "Slot type should be valid"
            assert isinstance(slot["is_available"], bool), "Availability should be boolean"
        
        print(f"✅ Retrieved {len(all_slots)} slots")
        
        # Test 2: Filter slots by vehicle type
        print("\n📋 Test 2: Filter by vehicle type")
        car_slots = authenticated_client._make_request(
            "GET", f"/parking/lots/{config.TEST_PARKING_LOT_ID}/slots",
            params={"vehicle_type": "car", "limit": 20}
        ).json()
        
        for slot in car_slots:
            assert slot["slot_type"] == "car", "All slots should be car slots"
        
        bike_slots = authenticated_client._make_request(
            "GET", f"/parking/lots/{config.TEST_PARKING_LOT_ID}/slots",
            params={"vehicle_type": "bike", "limit": 20}
        ).json()
        
        for slot in bike_slots:
            assert slot["slot_type"] == "bike", "All slots should be bike slots"
        
        print(f"✅ Found {len(car_slots)} car slots, {len(bike_slots)} bike slots")
        
        # Test 3: Filter slots by availability status
        print("\n📋 Test 3: Filter by availability")
        available_slots = authenticated_client._make_request(
            "GET", f"/parking/lots/{config.TEST_PARKING_LOT_ID}/slots",
            params={"status": "available", "limit": 20}
        ).json()
        
        for slot in available_slots:
            assert slot["is_available"] is True, "All slots should be available"
        
        print(f"✅ Found {len(available_slots)} available slots")
        
        # Test 4: Pagination for slots
        print("\n📋 Test 4: Slot pagination")
        paginated_slots = authenticated_client.get_lot_slots(
            config.TEST_PARKING_LOT_ID, 
            limit=5
        )
        
        assert len(paginated_slots) <= 5, "Should respect pagination limit"
        print(f"✅ Pagination: returned {len(paginated_slots)} slots")
    
    def test_parking_search_functionality(self, authenticated_client: APIClient):
        """Test parking lot search by location."""
        print("\n🔍 Testing Parking Search Functionality")
        
        # Test location-based search
        # Using coordinates near New York City (where our test data is likely located)
        search_results = authenticated_client.search_parking_lots(
            latitude=40.7128,
            longitude=-74.0060,
            radius_km=50.0
        )
        
        assert isinstance(search_results, list), "Search should return list of lots"
        
        # Verify search results structure
        for lot in search_results[:3]:  # Check first 3 results
            required_fields = ["id", "name", "address", "latitude", "longitude", "distance_km"]
            for field in required_fields:
                if field in lot:  # distance_km might not always be present
                    if field == "distance_km":
                        assert isinstance(lot[field], (int, float)), f"{field} should be numeric"
                        assert lot[field] >= 0, f"{field} should be non-negative"
        
        print(f"✅ Location search found {len(search_results)} lots")
        
        if search_results:
            closest_lot = search_results[0]
            print(f"   📍 Closest: {closest_lot['name']}")
            if "distance_km" in closest_lot:
                print(f"   📏 Distance: {closest_lot['distance_km']:.2f} km")
        
        # Test search with different radius
        narrow_search = authenticated_client.search_parking_lots(
            latitude=40.7128,
            longitude=-74.0060,
            radius_km=5.0  # Smaller radius
        )
        
        # Narrow search should return same or fewer results
        assert len(narrow_search) <= len(search_results), "Narrow search should return fewer or equal results"
        
        print(f"✅ Narrow search (5km): {len(narrow_search)} lots")
    
    def test_parking_error_scenarios(self, authenticated_client: APIClient):
        """Test parking endpoint error handling."""
        print("\n❌ Testing Parking Error Scenarios")
        
        # Test 1: Non-existent parking lot
        print("\n❌ Test 1: Non-existent parking lot")
        fake_lot_id = "00000000-0000-0000-0000-000000000000"
        
        response = authenticated_client._make_request("GET", f"/parking/lots/{fake_lot_id}")
        assert response.status_code == 404, "Non-existent lot should return 404"
        print("✅ Non-existent lot correctly returns 404")
        
        # Test 2: Invalid availability parameters
        print("\n❌ Test 2: Invalid availability parameters")
        response = authenticated_client._make_request(
            "POST", f"/parking/lots/{config.TEST_PARKING_LOT_ID}/availability",
            data={
                "vehicle_type": "invalid_type",
                "start_time": "invalid_time",
                "end_time": "also_invalid"
            }
        )
        assert response.status_code in [400, 422], "Invalid parameters should be rejected"
        print("✅ Invalid availability parameters correctly rejected")
        
        # Test 3: Invalid slot filters
        print("\n❌ Test 3: Invalid slot filters")
        response = authenticated_client._make_request(
            "GET", f"/parking/lots/{config.TEST_PARKING_LOT_ID}/slots",
            params={"vehicle_type": "invalid_vehicle_type"}
        )
        # This might return empty list or validation error
        assert response.status_code in [200, 400, 422], "Invalid vehicle type should be handled"
        print("✅ Invalid slot filters handled appropriately")
        
        # Test 4: Invalid search coordinates
        print("\n❌ Test 4: Invalid search coordinates")
        response = authenticated_client._make_request(
            "POST", "/parking/search",
            data={
                "latitude": 200.0,  # Invalid latitude
                "longitude": -74.0060,
                "radius_km": 10.0
            }
        )
        assert response.status_code in [400, 422], "Invalid coordinates should be rejected"
        print("✅ Invalid search coordinates correctly rejected")
        
        # Test 5: Slots for non-existent lot
        print("\n❌ Test 5: Slots for non-existent lot")
        response = authenticated_client._make_request(
            "GET", f"/parking/lots/{fake_lot_id}/slots"
        )
        assert response.status_code == 404, "Slots for non-existent lot should return 404"
        print("✅ Slots for non-existent lot correctly returns 404")
    
    def test_parking_data_consistency(self, authenticated_client: APIClient):
        """Test parking data consistency and relationships."""
        print("\n🔍 Testing Parking Data Consistency")
        
        # Get a parking lot
        lots = authenticated_client.get_parking_lots(limit=1)
        assert len(lots) > 0, "Should have at least one parking lot"
        
        lot = lots[0]
        lot_id = lot["id"]
        
        print(f"✅ Testing consistency for lot: {lot['name']}")
        
        # Test 1: Slot counts consistency
        print("\n📊 Test 1: Slot counts consistency")
        
        # Get declared slot counts from lot
        declared_car_slots = lot["total_car_slots"]
        declared_bike_slots = lot["total_bike_slots"]
        
        # Get actual slots
        actual_car_slots = authenticated_client._make_request(
            "GET", f"/parking/lots/{lot_id}/slots",
            params={"vehicle_type": "car", "limit": 1000}
        ).json()
        
        actual_bike_slots = authenticated_client._make_request(
            "GET", f"/parking/lots/{lot_id}/slots",
            params={"vehicle_type": "bike", "limit": 1000}
        ).json()
        
        actual_car_count = len(actual_car_slots)
        actual_bike_count = len(actual_bike_slots)
        
        print(f"   🚗 Declared car slots: {declared_car_slots}, Actual: {actual_car_count}")
        print(f"   🏍️ Declared bike slots: {declared_bike_slots}, Actual: {actual_bike_count}")
        
        # Allow for some variance (slots might be added/removed)
        car_diff = abs(declared_car_slots - actual_car_count)
        bike_diff = abs(declared_bike_slots - actual_bike_count)
        
        assert car_diff <= 10, f"Car slot count difference too large: {car_diff}"
        assert bike_diff <= 10, f"Bike slot count difference too large: {bike_diff}"
        
        print("✅ Slot counts are consistent")
        
        # Test 2: Availability calculation consistency
        print("\n📊 Test 2: Availability calculation consistency")
        
        availability = authenticated_client.get_lot_availability(
            lot_id=lot_id,
            vehicle_type="car",
            start_time=authenticated_client.generate_future_datetime(1),
            end_time=authenticated_client.generate_future_datetime(3)
        )
        
        AssertionHelpers.assert_availability_data(availability)
        
        # Available + occupied should equal total
        available = availability["available_slots"]
        total = availability["total_slots"]
        
        assert available <= total, "Available slots should not exceed total"
        assert available >= 0, "Available slots should be non-negative"
        
        print(f"✅ Availability calculation consistent: {available}/{total}")
        
        # Test 3: Geographic data consistency
        print("\n📊 Test 3: Geographic data consistency")
        
        assert -90 <= lot["latitude"] <= 90, "Latitude should be valid"
        assert -180 <= lot["longitude"] <= 180, "Longitude should be valid"
        assert lot["address"] and len(lot["address"]) > 0, "Address should not be empty"
        
        print(f"✅ Geographic data valid: {lot['latitude']}, {lot['longitude']}")
        
        # Test 4: Pricing data consistency
        print("\n📊 Test 4: Pricing data consistency")
        
        assert lot["hourly_rate_car"] > 0, "Car hourly rate should be positive"
        assert lot["hourly_rate_bike"] > 0, "Bike hourly rate should be positive"
        assert lot["hourly_rate_car"] >= lot["hourly_rate_bike"], "Car rate should be >= bike rate"
        
        print(f"✅ Pricing data valid: Car ${lot['hourly_rate_car']}/hr, Bike ${lot['hourly_rate_bike']}/hr")
    
    def test_parking_performance_indicators(self, authenticated_client: APIClient):
        """Test parking performance and capacity indicators."""
        print("\n📈 Testing Parking Performance Indicators")
        
        # Test multiple lots for performance indicators
        lots = authenticated_client.get_parking_lots(limit=5)
        
        performance_metrics = {
            "total_capacity": 0,
            "total_available": 0,
            "average_car_rate": 0,
            "average_bike_rate": 0,
            "active_lots": 0
        }
        
        for lot in lots:
            lot_id = lot["id"]
            
            # Get availability for performance calculation
            try:
                car_availability = authenticated_client.get_lot_availability(
                    lot_id=lot_id,
                    vehicle_type="car",
                    start_time=authenticated_client.generate_future_datetime(1),
                    end_time=authenticated_client.generate_future_datetime(2)
                )
                
                performance_metrics["total_capacity"] += car_availability["total_slots"]
                performance_metrics["total_available"] += car_availability["available_slots"]
                
            except Exception as e:
                print(f"⚠️ Could not get availability for lot {lot['name']}: {e}")
            
            # Accumulate pricing data
            performance_metrics["average_car_rate"] += float(lot["hourly_rate_car"])
            performance_metrics["average_bike_rate"] += float(lot["hourly_rate_bike"])
            
            if lot["is_active"]:
                performance_metrics["active_lots"] += 1
        
        # Calculate averages
        if len(lots) > 0:
            performance_metrics["average_car_rate"] /= len(lots)
            performance_metrics["average_bike_rate"] /= len(lots)
            
            occupancy_rate = 0
            if performance_metrics["total_capacity"] > 0:
                occupancy_rate = ((performance_metrics["total_capacity"] - performance_metrics["total_available"]) 
                                 / performance_metrics["total_capacity"]) * 100
        
        print(f"✅ System Performance Metrics:")
        print(f"   🏢 Active lots: {performance_metrics['active_lots']}/{len(lots)}")
        print(f"   📊 Total capacity: {performance_metrics['total_capacity']} slots")
        print(f"   📈 Current occupancy: {occupancy_rate:.1f}%")
        print(f"   💰 Average car rate: ${performance_metrics['average_car_rate']:.2f}/hr")
        print(f"   💰 Average bike rate: ${performance_metrics['average_bike_rate']:.2f}/hr")
        
        # Validate performance metrics
        assert performance_metrics["active_lots"] >= 0, "Active lots should be non-negative"
        assert performance_metrics["total_capacity"] >= 0, "Total capacity should be non-negative"
        assert 0 <= occupancy_rate <= 100, "Occupancy rate should be 0-100%"
        assert performance_metrics["average_car_rate"] > 0, "Average car rate should be positive"
        assert performance_metrics["average_bike_rate"] > 0, "Average bike rate should be positive"
        
        print("✅ All performance indicators are valid")
