"""Performance and load testing for Smart Parking API."""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.api_client import APIClient
from utils.test_helpers import TestDataManager
from config import config


@pytest.mark.performance
class TestPerformance:
    """Performance and load tests."""
    
    def test_api_response_times(self, api_client: APIClient, performance_timer):
        """Test API response times for common operations."""
        print("\n⏱️ Testing API Response Times")
        
        # Test 1: Health check response time
        start_time = time.time()
        health = api_client.health_check()
        health_time = time.time() - start_time
        
        assert health["status"] == "healthy", "Health check should succeed"
        assert health_time < 1.0, f"Health check should be fast, took {health_time:.3f}s"
        print(f"✅ Health check: {health_time:.3f}s")
        
        # Test 2: Get parking lots response time
        start_time = time.time()
        lots = api_client.get_parking_lots(limit=20)
        lots_time = time.time() - start_time
        
        assert len(lots) > 0, "Should return parking lots"
        assert lots_time < 2.0, f"Get lots should be fast, took {lots_time:.3f}s"
        print(f"✅ Get parking lots: {lots_time:.3f}s")
        
        # Test 3: Get specific lot response time
        start_time = time.time()
        lot = api_client.get_parking_lot(config.TEST_PARKING_LOT_ID)
        lot_time = time.time() - start_time
        
        assert lot["id"] == config.TEST_PARKING_LOT_ID, "Should return correct lot"
        assert lot_time < 1.5, f"Get specific lot should be fast, took {lot_time:.3f}s"
        print(f"✅ Get specific lot: {lot_time:.3f}s")
        
        # Test 4: Get availability response time
        start_time = time.time()
        start_dt = api_client.generate_future_datetime(1)
        end_dt = api_client.generate_future_datetime(3)
        
        availability = api_client.get_lot_availability(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            start_time=start_dt,
            end_time=end_dt
        )
        availability_time = time.time() - start_time
        
        assert "available_slots" in availability, "Should return availability data"
        assert availability_time < 2.0, f"Get availability should be fast, took {availability_time:.3f}s"
        print(f"✅ Get availability: {availability_time:.3f}s")
    
    def test_authentication_performance(self, api_client: APIClient, test_data_manager: TestDataManager):
        """Test authentication operation performance."""
        print("\n🔐 Testing Authentication Performance")
        
        user_data = test_data_manager.generate_test_user_data("perf_test")
        
        # Test registration performance
        start_time = time.time()
        user = api_client.register_user(**user_data)
        registration_time = time.time() - start_time
        
        assert "id" in user, "Registration should succeed"
        assert registration_time < 3.0, f"Registration should be fast, took {registration_time:.3f}s"
        print(f"✅ User registration: {registration_time:.3f}s")
        
        # Test login performance
        start_time = time.time()
        login_result = api_client.login_user(user_data["email"], user_data["password"])
        login_time = time.time() - start_time
        
        assert "access_token" in login_result, "Login should succeed"
        assert login_time < 2.0, f"Login should be fast, took {login_time:.3f}s"
        print(f"✅ User login: {login_time:.3f}s")
    
    def test_booking_performance(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test booking operation performance."""
        print("\n📅 Testing Booking Performance")
        
        booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            hours_from_now=1,
            duration_hours=2
        )
        
        # Test pricing preview performance
        start_time = time.time()
        pricing = authenticated_client.get_pricing_preview(**booking_data)
        pricing_time = time.time() - start_time
        
        assert "total_amount" in pricing, "Pricing should succeed"
        assert pricing_time < 2.0, f"Pricing preview should be fast, took {pricing_time:.3f}s"
        print(f"✅ Pricing preview: {pricing_time:.3f}s")
        
        # Test booking creation performance
        start_time = time.time()
        booking = authenticated_client.create_booking(**booking_data)
        booking_time = time.time() - start_time
        
        assert "id" in booking, "Booking creation should succeed"
        assert booking_time < 3.0, f"Booking creation should be reasonably fast, took {booking_time:.3f}s"
        print(f"✅ Booking creation: {booking_time:.3f}s")
        
        booking_id = booking["id"]
        
        # Test booking retrieval performance
        start_time = time.time()
        retrieved_booking = authenticated_client.get_booking(booking_id)
        retrieval_time = time.time() - start_time
        
        assert retrieved_booking["id"] == booking_id, "Should retrieve correct booking"
        assert retrieval_time < 1.5, f"Booking retrieval should be fast, took {retrieval_time:.3f}s"
        print(f"✅ Booking retrieval: {retrieval_time:.3f}s")
        
        # Test booking cancellation performance
        start_time = time.time()
        cancel_result = authenticated_client.cancel_booking(booking_id)
        cancel_time = time.time() - start_time
        
        assert "message" in cancel_result, "Cancellation should succeed"
        assert cancel_time < 2.0, f"Booking cancellation should be fast, took {cancel_time:.3f}s"
        print(f"✅ Booking cancellation: {cancel_time:.3f}s")
    
    def test_concurrent_user_load(self, test_data_manager: TestDataManager):
        """Test system under concurrent user load."""
        print("\n👥 Testing Concurrent User Load")
        
        num_concurrent_users = 5
        operations_per_user = 3
        
        def user_workflow(user_index):
            """Single user workflow."""
            client = APIClient()
            results = {"user_id": user_index, "operations": [], "success": True, "error": None}
            
            try:
                # Register and login
                user_data = test_data_manager.generate_test_user_data(f"load_user_{user_index}")
                
                start = time.time()
                client.register_user(**user_data)
                client.login_user(user_data["email"], user_data["password"])
                auth_time = time.time() - start
                
                results["operations"].append(("auth", auth_time))
                
                # Perform multiple operations
                for op_index in range(operations_per_user):
                    # Browse lots
                    start = time.time()
                    lots = client.get_parking_lots(limit=5)
                    browse_time = time.time() - start
                    results["operations"].append((f"browse_{op_index}", browse_time))
                    
                    # Check availability
                    start = time.time()
                    start_dt = client.generate_future_datetime(1)
                    end_dt = client.generate_future_datetime(3)
                    
                    availability = client.get_lot_availability(
                        lot_id=config.TEST_PARKING_LOT_ID,
                        vehicle_type="car",
                        start_time=start_dt,
                        end_time=end_dt
                    )
                    availability_time = time.time() - start
                    results["operations"].append((f"availability_{op_index}", availability_time))
                
            except Exception as e:
                results["success"] = False
                results["error"] = str(e)
            finally:
                client.cleanup()
            
            return results
        
        # Execute concurrent users
        print(f"🚀 Starting {num_concurrent_users} concurrent users...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
            futures = [
                executor.submit(user_workflow, i) 
                for i in range(num_concurrent_users)
            ]
            
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_users = [r for r in results if r["success"]]
        failed_users = [r for r in results if not r["success"]]
        
        print(f"✅ Load test completed in {total_time:.2f}s")
        print(f"✅ Successful users: {len(successful_users)}/{num_concurrent_users}")
        
        if failed_users:
            print(f"❌ Failed users: {len(failed_users)}")
            for failed in failed_users:
                print(f"   User {failed['user_id']}: {failed['error']}")
        
        # Calculate average operation times
        all_operations = []
        for user_result in successful_users:
            all_operations.extend(user_result["operations"])
        
        if all_operations:
            avg_time = sum(op[1] for op in all_operations) / len(all_operations)
            max_time = max(op[1] for op in all_operations)
            
            print(f"📊 Operation times: avg={avg_time:.3f}s, max={max_time:.3f}s")
            
            # Performance assertions
            assert len(successful_users) >= num_concurrent_users * 0.8, "At least 80% of users should succeed"
            assert avg_time < 5.0, f"Average operation time should be reasonable, got {avg_time:.3f}s"
            assert max_time < 10.0, f"Maximum operation time should be reasonable, got {max_time:.3f}s"
    
    def test_booking_throughput(self, test_data_manager: TestDataManager):
        """Test booking creation throughput."""
        print("\n🏃‍♂️ Testing Booking Throughput")
        
        num_bookings = 10
        created_bookings = []
        
        # Create authenticated user
        client = APIClient()
        user_data = test_data_manager.generate_test_user_data("throughput_user")
        
        try:
            client.register_user(**user_data)
            client.login_user(user_data["email"], user_data["password"])
            
            # Create multiple bookings rapidly
            print(f"🚀 Creating {num_bookings} bookings rapidly...")
            start_time = time.time()
            
            for i in range(num_bookings):
                booking_data = test_data_manager.generate_booking_data(
                    lot_id=config.TEST_PARKING_LOT_ID,
                    vehicle_type="car" if i % 2 == 0 else "bike",
                    hours_from_now=i + 1,
                    duration_hours=1
                )
                
                booking = client.create_booking(**booking_data)
                created_bookings.append(booking["id"])
            
            total_time = time.time() - start_time
            throughput = num_bookings / total_time
            
            print(f"✅ Created {num_bookings} bookings in {total_time:.2f}s")
            print(f"📊 Throughput: {throughput:.2f} bookings/second")
            
            # Performance assertions
            assert len(created_bookings) == num_bookings, "All bookings should be created"
            assert throughput > 1.0, f"Throughput should be reasonable, got {throughput:.2f} bookings/sec"
            
            # Clean up
            print("🧹 Cleaning up bookings...")
            for booking_id in created_bookings:
                try:
                    client.cancel_booking(booking_id)
                except Exception as e:
                    print(f"   Warning: Could not cancel booking {booking_id}: {e}")
            
        finally:
            client.cleanup()
    
    @pytest.mark.parametrize("concurrent_requests", [3, 5, 8])
    def test_availability_under_load(self, api_client: APIClient, concurrent_requests: int):
        """Test availability endpoint under concurrent load."""
        print(f"\n⚡ Testing Availability Under Load ({concurrent_requests} concurrent)")
        
        def check_availability():
            """Single availability check."""
            start_time = time.time()
            start_dt = api_client.generate_future_datetime(1)
            end_dt = api_client.generate_future_datetime(3)
            
            availability = api_client.get_lot_availability(
                lot_id=config.TEST_PARKING_LOT_ID,
                vehicle_type="car",
                start_time=start_dt,
                end_time=end_dt
            )
            
            response_time = time.time() - start_time
            return {
                "success": "available_slots" in availability,
                "response_time": response_time,
                "available_slots": availability.get("available_slots", 0)
            }
        
        # Execute concurrent availability checks
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(check_availability) for _ in range(concurrent_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_requests]
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        print(f"✅ {len(successful_requests)}/{concurrent_requests} requests succeeded")
        print(f"📊 Total time: {total_time:.3f}s")
        print(f"📊 Avg response time: {avg_response_time:.3f}s")
        print(f"📊 Max response time: {max_response_time:.3f}s")
        
        # Performance assertions
        assert len(successful_requests) == concurrent_requests, "All requests should succeed"
        assert avg_response_time < 3.0, f"Average response time should be reasonable"
        assert max_response_time < 5.0, f"Maximum response time should be acceptable"
        
        # Verify consistent data
        available_slots_results = [r["available_slots"] for r in successful_requests]
        unique_results = set(available_slots_results)
        
        if len(unique_results) == 1:
            print("✅ All concurrent requests returned consistent availability data")
        else:
            print(f"⚠️ Availability results varied: {unique_results} (may be due to concurrent bookings)")
