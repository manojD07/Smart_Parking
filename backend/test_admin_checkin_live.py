#!/usr/bin/env python3
"""
Live testing script for admin and check-in/check-out APIs.
This script tests the actual running backend.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta, timezone, date
from typing import Optional, Dict, Any


class AdminCheckinTester:
    """Live tester for admin and checkin APIs."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.admin_token: Optional[str] = None
        self.user_token: Optional[str] = None
        self.test_booking_id: Optional[str] = None
        self.test_booking_reference: Optional[str] = None
        
    async def setup_users(self) -> bool:
        """Set up admin and regular users for testing."""
        async with httpx.AsyncClient() as client:
            try:
                # Try to create admin user (may fail if exists)
                admin_data = {
                    "email": "livetest_admin@parking.com",
                    "first_name": "LiveTest",
                    "last_name": "Admin",
                    "password": "LiveTestAdmin123!",
                    "phone": "9999999991"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=admin_data
                )
                if response.status_code == 201:
                    print("✅ Admin user created")
                else:
                    print("ℹ️ Admin user might already exist")
                
                # Try to create regular user
                user_data = {
                    "email": "livetest_user@parking.com", 
                    "first_name": "LiveTest",
                    "last_name": "User",
                    "password": "LiveTestUser123!",
                    "phone": "9999999992"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=user_data
                )
                if response.status_code == 201:
                    print("✅ Regular user created")
                else:
                    print("ℹ️ Regular user might already exist")
                
                # Login admin
                login_response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={
                        "email": "livetest_admin@parking.com",
                        "password": "LiveTestAdmin123!"
                    }
                )
                
                if login_response.status_code == 200:
                    admin_tokens = login_response.json()
                    self.admin_token = admin_tokens["access_token"]
                    print("✅ Admin login successful")
                else:
                    print(f"❌ Admin login failed: {login_response.status_code}")
                    print(f"Response: {login_response.text}")
                    return False
                
                # Login regular user
                user_login_response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={
                        "email": "livetest_user@parking.com",
                        "password": "LiveTestUser123!"
                    }
                )
                
                if user_login_response.status_code == 200:
                    user_tokens = user_login_response.json()
                    self.user_token = user_tokens["access_token"]
                    print("✅ User login successful")
                else:
                    print(f"❌ User login failed: {user_login_response.status_code}")
                    return False
                
                return True
                
            except Exception as e:
                print(f"❌ Setup failed: {e}")
                return False

    async def test_admin_dashboard(self) -> bool:
        """Test admin dashboard access."""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/admin/dashboard",
                    headers={"Authorization": f"Bearer {self.admin_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Admin dashboard access successful")
                    print(f"   📊 Total users: {data.get('overview', {}).get('total_users', 'N/A')}")
                    print(f"   🏢 Total lots: {data.get('overview', {}).get('total_parking_lots', 'N/A')}")
                    print(f"   📈 Today bookings: {data.get('overview', {}).get('today_bookings', 'N/A')}")
                    return True
                else:
                    print(f"❌ Admin dashboard failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Admin dashboard test failed: {e}")
                return False

    async def test_admin_dashboard_unauthorized(self) -> bool:
        """Test admin dashboard with regular user token."""
        if not self.user_token:
            print("❌ No user token available")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/admin/dashboard",
                    headers={"Authorization": f"Bearer {self.user_token}"}
                )
                
                if response.status_code == 403:
                    print("✅ Admin dashboard correctly blocks regular users")
                    return True
                else:
                    print(f"❌ Expected 403, got: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Admin dashboard unauthorized test failed: {e}")
                return False

    async def test_revenue_report(self) -> bool:
        """Test admin revenue report."""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                today = date.today()
                yesterday = today - timedelta(days=1)
                
                response = await client.get(
                    f"{self.base_url}/api/v1/admin/reports/revenue",
                    params={
                        "start_date": str(yesterday),
                        "end_date": str(today)
                    },
                    headers={"Authorization": f"Bearer {self.admin_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Revenue report access successful")
                    print(f"   💰 Total revenue: {data.get('total_revenue', 'N/A')}")
                    print(f"   📊 Total bookings: {data.get('total_bookings', 'N/A')}")
                    return True
                else:
                    print(f"❌ Revenue report failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Revenue report test failed: {e}")
                return False

    async def create_test_booking(self) -> bool:
        """Create a test booking for check-in tests."""
        if not self.user_token:
            print("❌ No user token available")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                # First, get available parking lots
                lots_response = await client.get(
                    f"{self.base_url}/api/v1/parking/lots",
                    params={"limit": 1, "is_active": True}
                )
                
                if lots_response.status_code != 200:
                    print(f"❌ Failed to get parking lots: {lots_response.status_code}")
                    return False
                
                lots = lots_response.json()
                if not lots:
                    print("❌ No parking lots available")
                    return False
                
                lot_id = lots[0]["id"]
                
                # Create booking
                start_time = datetime.now(timezone.utc) + timedelta(minutes=30)
                end_time = start_time + timedelta(hours=2)
                
                booking_data = {
                    "lot_id": lot_id,
                    "vehicle_type": "car",
                    "vehicle_number": "LIVETEST123",
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/bookings/",
                    json=booking_data,
                    headers={"Authorization": f"Bearer {self.user_token}"}
                )
                
                if response.status_code == 201:
                    booking = response.json()
                    self.test_booking_id = booking["id"]
                    self.test_booking_reference = booking["booking_reference"]
                    print(f"✅ Test booking created: {self.test_booking_reference}")
                    return True
                else:
                    print(f"❌ Booking creation failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Booking creation failed: {e}")
                return False

    async def test_admin_checkin_by_reference(self) -> bool:
        """Test admin check-in by booking reference."""
        if not self.admin_token or not self.test_booking_reference:
            print("❌ Missing admin token or booking reference")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/bookings/checkin/{self.test_booking_reference}",
                    headers={"Authorization": f"Bearer {self.admin_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Admin check-in successful: {data.get('message', 'N/A')}")
                    return True
                else:
                    print(f"❌ Admin check-in failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Admin check-in test failed: {e}")
                return False

    async def test_user_checkin_by_id(self) -> bool:
        """Test user check-in by booking ID."""
        if not self.user_token or not self.test_booking_id:
            print("❌ Missing user token or booking ID")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/bookings/{self.test_booking_id}/checkin",
                    headers={"Authorization": f"Bearer {self.user_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ User check-in successful: {data.get('message', 'N/A')}")
                    return True
                else:
                    print(f"❌ User check-in failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ User check-in test failed: {e}")
                return False

    async def test_user_checkout_by_id(self) -> bool:
        """Test user check-out by booking ID."""
        if not self.user_token or not self.test_booking_id:
            print("❌ Missing user token or booking ID")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/bookings/{self.test_booking_id}/checkout",
                    headers={"Authorization": f"Bearer {self.user_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ User check-out successful: {data.get('message', 'N/A')}")
                    return True
                else:
                    print(f"❌ User check-out failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ User check-out test failed: {e}")
                return False

    async def test_get_booking_by_reference(self) -> bool:
        """Test getting booking by reference."""
        if not self.user_token or not self.test_booking_reference:
            print("❌ Missing user token or booking reference")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/bookings/reference/{self.test_booking_reference}",
                    headers={"Authorization": f"Bearer {self.user_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Get booking by reference successful")
                    print(f"   📋 Status: {data.get('status', 'N/A')}")
                    print(f"   🚗 Vehicle: {data.get('vehicle_number', 'N/A')}")
                    return True
                else:
                    print(f"❌ Get booking by reference failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Get booking by reference test failed: {e}")
                return False

    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all admin and check-in tests."""
        print("🚀 STARTING ADMIN & CHECKIN API LIVE TESTS")
        print("=" * 50)
        
        results = {}
        
        # Setup
        print("\n1️⃣ Setting up users...")
        results["setup"] = await self.setup_users()
        
        if not results["setup"]:
            print("❌ Setup failed, stopping tests")
            return results
        
        # Admin tests
        print("\n2️⃣ Testing admin endpoints...")
        results["admin_dashboard"] = await self.test_admin_dashboard()
        results["admin_dashboard_unauthorized"] = await self.test_admin_dashboard_unauthorized()
        results["revenue_report"] = await self.test_revenue_report()
        
        # Booking creation
        print("\n3️⃣ Creating test booking...")
        results["create_booking"] = await self.create_test_booking()
        
        if not results["create_booking"]:
            print("❌ Booking creation failed, skipping check-in tests")
            return results
        
        # Check-in/out tests (create separate bookings for each to avoid conflicts)
        print("\n4️⃣ Testing check-in/check-out...")
        
        # Test get booking by reference first
        results["get_booking_by_reference"] = await self.test_get_booking_by_reference()
        
        # Test admin check-in
        # Create new booking for admin checkin test
        await self.create_test_booking()
        results["admin_checkin"] = await self.test_admin_checkin_by_reference()
        
        # Test user check-in and check-out flow
        # Create new booking for user checkin/checkout test
        await self.create_test_booking()
        results["user_checkin"] = await self.test_user_checkin_by_id()
        if results["user_checkin"]:
            results["user_checkout"] = await self.test_user_checkout_by_id()
        else:
            results["user_checkout"] = False
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 OVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️ Some tests failed - check logs above")
        
        return results


async def main():
    """Main function to run the tests."""
    tester = AdminCheckinTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
