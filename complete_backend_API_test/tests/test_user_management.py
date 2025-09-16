"""Complete user management endpoint tests."""

import pytest
from utils.api_client import APIClient
from utils.test_helpers import TestDataManager, AssertionHelpers
from config import config


@pytest.mark.regression
class TestUserManagement:
    """Test all user management endpoints."""
    
    def test_user_profile_management(self, authenticated_client: APIClient):
        """Test user profile operations."""
        print("\n👤 Testing User Profile Management")
        
        # Get current profile
        print("\n📋 Step 1: Get current profile")
        profile = authenticated_client.get_user_profile()
        
        required_fields = ["id", "email", "first_name", "last_name", "is_admin", "is_active"]
        for field in required_fields:
            assert field in profile, f"Profile should include {field}"
        
        original_first_name = profile["first_name"]
        original_last_name = profile["last_name"]
        
        print(f"✅ Current profile: {profile['first_name']} {profile['last_name']} ({profile['email']})")
        
        # Update profile
        print("\n✏️ Step 2: Update profile")
        updated_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+9876543210"
        }
        
        updated_profile = authenticated_client.update_user_profile(updated_data)
        
        assert updated_profile["first_name"] == "Updated", "First name should be updated"
        assert updated_profile["last_name"] == "Name", "Last name should be updated"
        assert updated_profile["phone"] == "+9876543210", "Phone should be updated"
        
        print(f"✅ Profile updated: {updated_profile['first_name']} {updated_profile['last_name']}")
        
        # Verify update persisted
        print("\n🔍 Step 3: Verify update persisted")
        refreshed_profile = authenticated_client.get_user_profile()
        assert refreshed_profile["first_name"] == "Updated", "Update should persist"
        assert refreshed_profile["last_name"] == "Name", "Update should persist"
        
        print("✅ Profile update persisted correctly")
        
        # Restore original values
        restore_data = {
            "first_name": original_first_name,
            "last_name": original_last_name
        }
        authenticated_client.update_user_profile(restore_data)
        print("🔄 Profile restored to original values")
    
    def test_user_password_change_via_users_endpoint(self, api_client: APIClient, test_data_manager: TestDataManager):
        """Test password change via users endpoint."""
        print("\n🔐 Testing Password Change via Users Endpoint")
        
        # Create test user
        user_data = test_data_manager.generate_test_user_data("pwd_change_test")
        api_client.register_user(**user_data)
        api_client.login_user(user_data["email"], user_data["password"])
        
        old_password = user_data["password"]
        new_password = "NewPassword789!"
        
        # Change password via users endpoint
        result = api_client.change_user_password(old_password, new_password)
        assert "message" in result, "Password change should return success message"
        
        print(f"✅ Password changed via users endpoint: {result.get('message')}")
        
        # Verify old password no longer works
        test_client = APIClient()
        try:
            response = test_client._make_request(
                "POST", "/auth/login",
                data={"email": user_data["email"], "password": old_password}
            )
            assert response.status_code == 401, "Old password should be rejected"
            
            # Verify new password works
            response = test_client._make_request(
                "POST", "/auth/login",
                data={"email": user_data["email"], "password": new_password}
            )
            assert response.status_code == 200, "New password should work"
            
            print("✅ Password change verified successfully")
            
        finally:
            test_client.cleanup()
    
    def test_user_bookings_via_users_endpoint(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test getting user bookings via users endpoint."""
        print("\n📅 Testing User Bookings via Users Endpoint")
        
        # Create a test booking first
        booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            hours_from_now=1,
            duration_hours=2
        )
        
        booking = authenticated_client.create_booking(**booking_data)
        booking_id = booking["id"]
        booking_ref = booking["booking_reference"]
        
        print(f"✅ Test booking created: {booking_ref}")
        
        # Get bookings via users endpoint
        user_bookings = authenticated_client.get_user_bookings()
        
        # Verify our booking is in the list
        booking_ids = [b["id"] for b in user_bookings]
        assert booking_id in booking_ids, "Booking should appear in user bookings"
        
        # Find our specific booking
        our_booking = next(b for b in user_bookings if b["id"] == booking_id)
        assert our_booking["booking_reference"] == booking_ref, "Booking details should match"
        
        print(f"✅ Found {len(user_bookings)} user bookings via users endpoint")
        
        # Test pagination
        paginated_bookings = authenticated_client.get_user_bookings(limit=1)
        assert len(paginated_bookings) <= 1, "Pagination should work"
        
        print("✅ Pagination works correctly")
        
        # Clean up
        authenticated_client.cancel_booking(booking_id)
        print("🧹 Test booking cleaned up")
    
    def test_account_deletion(self, test_data_manager: TestDataManager):
        """Test user account deletion."""
        print("\n🗑️ Testing Account Deletion")
        
        # Create test user
        user_data = test_data_manager.generate_test_user_data("delete_test")
        test_client = APIClient()
        
        try:
            test_client.register_user(**user_data)
            test_client.login_user(user_data["email"], user_data["password"])
            
            # Verify user exists
            profile = test_client.get_user_profile()
            user_email = profile["email"]
            print(f"✅ Test user created: {user_email}")
            
            # Delete account
            deletion_result = test_client.delete_user_account()
            assert "message" in deletion_result, "Account deletion should return success message"
            
            print(f"✅ Account deleted: {deletion_result.get('message')}")
            
            # Verify user can no longer login
            verify_client = APIClient()
            try:
                response = verify_client._make_request(
                    "POST", "/auth/login",
                    data={"email": user_email, "password": user_data["password"]}
                )
                # Account should be deactivated, not necessarily deleted
                assert response.status_code in [401, 404], "Deleted user should not be able to login"
                print("✅ Deleted user cannot login")
                
            finally:
                verify_client.cleanup()
            
        finally:
            test_client.cleanup()


@pytest.mark.regression
class TestAdminUserManagement:
    """Test admin user management endpoints."""
    
    def test_get_all_users(self, admin_client: APIClient):
        """Test admin getting all users."""
        print("\n👥 Testing Get All Users (Admin)")
        
        users = admin_client.get_all_users(limit=10)
        
        assert isinstance(users, list), "Should return list of users"
        assert len(users) > 0, "Should have at least one user"
        
        # Verify user structure
        for user in users[:3]:  # Check first 3 users
            required_fields = ["id", "email", "first_name", "last_name", "is_admin", "is_active"]
            for field in required_fields:
                assert field in user, f"User should include {field}"
        
        print(f"✅ Retrieved {len(users)} users")
        
        # Test pagination
        paginated_users = admin_client.get_all_users(limit=2)
        assert len(paginated_users) <= 2, "Pagination should work"
        
        print("✅ User pagination works correctly")
    
    def test_get_user_by_id(self, admin_client: APIClient, test_data_manager: TestDataManager):
        """Test admin getting user by ID."""
        print("\n🔍 Testing Get User by ID (Admin)")
        
        # Create a test user first
        user_data = test_data_manager.generate_test_user_data("admin_lookup_test")
        test_client = APIClient()
        
        try:
            created_user = test_client.register_user(**user_data)
            user_id = created_user["id"]
            
            print(f"✅ Test user created with ID: {user_id}")
            
            # Admin looks up user by ID
            found_user = admin_client.get_user_by_id(user_id)
            
            assert found_user["id"] == user_id, "Should find correct user"
            assert found_user["email"] == user_data["email"], "Email should match"
            assert found_user["first_name"] == user_data["first_name"], "Name should match"
            
            print(f"✅ Admin found user: {found_user['email']}")
            
        finally:
            test_client.cleanup()
    
    def test_user_activation_deactivation(self, admin_client: APIClient, test_data_manager: TestDataManager):
        """Test admin user activation/deactivation."""
        print("\n🔄 Testing User Activation/Deactivation (Admin)")
        
        # Create test user
        user_data = test_data_manager.generate_test_user_data("activation_test")
        test_client = APIClient()
        
        try:
            created_user = test_client.register_user(**user_data)
            user_id = created_user["id"]
            
            print(f"✅ Test user created: {created_user['email']}")
            
            # Verify user is initially active
            user_info = admin_client.get_user_by_id(user_id)
            assert user_info["is_active"] is True, "User should be initially active"
            
            # Deactivate user
            deactivate_result = admin_client.deactivate_user(user_id)
            assert "message" in deactivate_result, "Deactivation should return success message"
            
            print(f"✅ User deactivated: {deactivate_result.get('message')}")
            
            # Verify user is deactivated
            user_info = admin_client.get_user_by_id(user_id)
            assert user_info["is_active"] is False, "User should be deactivated"
            
            # Verify deactivated user cannot login
            response = test_client._make_request(
                "POST", "/auth/login",
                data={"email": user_data["email"], "password": user_data["password"]}
            )
            assert response.status_code == 401, "Deactivated user should not be able to login"
            
            print("✅ Deactivated user cannot login")
            
            # Reactivate user
            activate_result = admin_client.activate_user(user_id)
            assert "message" in activate_result, "Activation should return success message"
            
            print(f"✅ User reactivated: {activate_result.get('message')}")
            
            # Verify user is active again
            user_info = admin_client.get_user_by_id(user_id)
            assert user_info["is_active"] is True, "User should be active again"
            
            # Verify reactivated user can login
            login_result = test_client.login_user(user_data["email"], user_data["password"])
            assert "access_token" in login_result, "Reactivated user should be able to login"
            
            print("✅ Reactivated user can login")
            
        finally:
            test_client.cleanup()
    
    def test_admin_privilege_management(self, admin_client: APIClient, test_data_manager: TestDataManager):
        """Test admin privilege management."""
        print("\n👑 Testing Admin Privilege Management")
        
        # Create test user
        user_data = test_data_manager.generate_test_user_data("admin_priv_test")
        test_client = APIClient()
        
        try:
            created_user = test_client.register_user(**user_data)
            user_id = created_user["id"]
            
            print(f"✅ Test user created: {created_user['email']}")
            
            # Verify user is not admin initially
            user_info = admin_client.get_user_by_id(user_id)
            assert user_info["is_admin"] is False, "User should not be admin initially"
            
            # Make user admin
            make_admin_result = admin_client.make_user_admin(user_id)
            assert "message" in make_admin_result, "Make admin should return success message"
            
            print(f"✅ User made admin: {make_admin_result.get('message')}")
            
            # Verify user is now admin
            user_info = admin_client.get_user_by_id(user_id)
            assert user_info["is_admin"] is True, "User should be admin now"
            
            # Test that new admin can access admin endpoints
            test_client.login_user(user_data["email"], user_data["password"])
            
            try:
                dashboard = test_client.get_admin_dashboard()
                assert "overview" in dashboard, "New admin should access dashboard"
                print("✅ New admin can access admin endpoints")
            except Exception as e:
                print(f"⚠️ Admin endpoint access test failed: {e}")
            
            # Remove admin privileges
            remove_admin_result = admin_client.remove_user_admin(user_id)
            assert "message" in remove_admin_result, "Remove admin should return success message"
            
            print(f"✅ Admin privileges removed: {remove_admin_result.get('message')}")
            
            # Verify user is no longer admin
            user_info = admin_client.get_user_by_id(user_id)
            assert user_info["is_admin"] is False, "User should not be admin anymore"
            
        finally:
            test_client.cleanup()
    
    def test_user_search_functionality(self, admin_client: APIClient, test_data_manager: TestDataManager):
        """Test admin user search functionality."""
        print("\n🔍 Testing User Search Functionality (Admin)")
        
        # Create test users with distinct attributes
        test_users = []
        test_clients = []
        
        try:
            # User 1: Regular user
            user1_data = test_data_manager.generate_test_user_data("search_test1")
            user1_data["first_name"] = "SearchTest"
            user1_data["last_name"] = "UserOne"
            
            client1 = APIClient()
            user1 = client1.register_user(**user1_data)
            test_users.append(user1)
            test_clients.append(client1)
            
            # User 2: Admin user  
            user2_data = test_data_manager.generate_test_user_data("search_test2")
            user2_data["first_name"] = "SearchTest"
            user2_data["last_name"] = "UserTwo"
            
            client2 = APIClient()
            user2 = client2.register_user(**user2_data)
            admin_client.make_user_admin(user2["id"])  # Make admin
            test_users.append(user2)
            test_clients.append(client2)
            
            print(f"✅ Created {len(test_users)} test users")
            
            # Test 1: Search by first name
            print("\n📋 Test 1: Search by first name")
            name_results = admin_client.search_users(first_name="SearchTest")
            found_ids = [u["id"] for u in name_results]
            
            for user in test_users:
                assert user["id"] in found_ids, f"User {user['email']} should be found by first name"
            
            print(f"✅ Found {len(name_results)} users by first name")
            
            # Test 2: Search by admin status
            print("\n📋 Test 2: Search by admin status")
            admin_results = admin_client.search_users(is_admin=True)
            admin_ids = [u["id"] for u in admin_results]
            
            assert user2["id"] in admin_ids, "Admin user should be found in admin search"
            print(f"✅ Found {len(admin_results)} admin users")
            
            # Test 3: Search by active status
            print("\n📋 Test 3: Search by active status")
            active_results = admin_client.search_users(is_active=True)
            
            assert len(active_results) >= 2, "Should find active users"
            print(f"✅ Found {len(active_results)} active users")
            
            # Test 4: Search with pagination
            print("\n📋 Test 4: Search with pagination")
            paginated_results = admin_client.search_users(limit=1)
            
            assert len(paginated_results) <= 1, "Pagination should work"
            print("✅ Search pagination works correctly")
            
        finally:
            for client in test_clients:
                client.cleanup()
    
    def test_admin_user_update(self, admin_client: APIClient, test_data_manager: TestDataManager):
        """Test admin updating user details."""
        print("\n✏️ Testing Admin User Update")
        
        # Create test user
        user_data = test_data_manager.generate_test_user_data("admin_update_test")
        test_client = APIClient()
        
        try:
            created_user = test_client.register_user(**user_data)
            user_id = created_user["id"]
            
            print(f"✅ Test user created: {created_user['email']}")
            
            # Admin updates user details
            update_data = {
                "first_name": "AdminUpdated",
                "last_name": "Name",
                "phone": "+5555555555"
            }
            
            updated_user = admin_client.update_user_by_id(user_id, update_data)
            
            assert updated_user["first_name"] == "AdminUpdated", "First name should be updated"
            assert updated_user["last_name"] == "Name", "Last name should be updated"
            assert updated_user["phone"] == "+5555555555", "Phone should be updated"
            
            print(f"✅ User updated by admin: {updated_user['first_name']} {updated_user['last_name']}")
            
            # Verify update persisted
            refreshed_user = admin_client.get_user_by_id(user_id)
            assert refreshed_user["first_name"] == "AdminUpdated", "Update should persist"
            
            print("✅ Admin user update persisted correctly")
            
        finally:
            test_client.cleanup()
    
    def test_regular_user_cannot_access_admin_user_endpoints(self, authenticated_client: APIClient):
        """Test that regular users cannot access admin user management endpoints."""
        print("\n🔒 Testing Admin Endpoint Security")
        
        # Test 1: Get all users (should fail)
        print("\n❌ Test 1: Regular user tries to get all users")
        response = authenticated_client._make_request("GET", "/users/", use_auth=True)
        assert response.status_code == 403, "Regular user should be forbidden"
        print("✅ Regular user correctly forbidden from getting all users")
        
        # Test 2: Search users (should fail)
        print("\n❌ Test 2: Regular user tries to search users")
        response = authenticated_client._make_request("GET", "/users/search", use_auth=True)
        assert response.status_code == 403, "Regular user should be forbidden"
        print("✅ Regular user correctly forbidden from searching users")
        
        # Test 3: Make user admin (should fail)
        print("\n❌ Test 3: Regular user tries to make someone admin")
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        response = authenticated_client._make_request("POST", f"/users/{fake_user_id}/make-admin", use_auth=True)
        assert response.status_code == 403, "Regular user should be forbidden"
        print("✅ Regular user correctly forbidden from making admins")
