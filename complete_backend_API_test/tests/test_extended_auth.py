"""Extended authentication endpoint tests for 100% coverage."""

import pytest
from utils.api_client import APIClient
from utils.test_helpers import TestDataManager, AssertionHelpers
from config import config


@pytest.mark.regression
class TestExtendedAuthentication:
    """Test all authentication endpoints for complete coverage."""
    
    def test_change_password_workflow(self, authenticated_client: APIClient):
        """Test password change functionality."""
        print("\n🔐 Testing Password Change Workflow")
        
        # Get current user info first
        user_info = authenticated_client.get_current_user_info()
        assert "email" in user_info, "Should get user info successfully"
        
        # Test changing password
        old_password = "E2ETestPassword123!"  # From authenticated_client fixture
        new_password = "NewPassword456!"
        
        change_result = authenticated_client.change_password(old_password, new_password)
        assert "message" in change_result, "Password change should return success message"
        
        print(f"✅ Password changed: {change_result.get('message')}")
        
        # Verify old password no longer works by trying to login with it
        test_client = APIClient()
        try:
            # This should fail with old password
            response = test_client._make_request(
                "POST", "/auth/login", 
                data={"email": user_info["email"], "password": old_password}
            )
            assert response.status_code == 401, "Old password should be rejected"
            print("✅ Old password correctly rejected")
            
            # This should work with new password
            response = test_client._make_request(
                "POST", "/auth/login", 
                data={"email": user_info["email"], "password": new_password}
            )
            assert response.status_code == 200, "New password should work"
            print("✅ New password works correctly")
            
        finally:
            test_client.cleanup()
    
    def test_get_current_user_info(self, authenticated_client: APIClient):
        """Test getting current user information."""
        print("\n👤 Testing Get Current User Info")
        
        user_info = authenticated_client.get_current_user_info()
        
        # Validate user info structure
        required_fields = ["id", "email", "first_name", "last_name", "is_admin", "is_active"]
        for field in required_fields:
            assert field in user_info, f"User info should include {field}"
        
        assert "@" in user_info["email"], "Email should be valid"
        assert user_info["is_active"] is True, "User should be active"
        
        print(f"✅ User info retrieved: {user_info['email']}")
        print(f"   Name: {user_info['first_name']} {user_info['last_name']}")
        print(f"   Admin: {user_info['is_admin']}")
        print(f"   Active: {user_info['is_active']}")
    
    def test_logout_functionality(self, authenticated_client: APIClient):
        """Test user logout functionality."""
        print("\n🚪 Testing Logout Functionality")
        
        # Verify we're authenticated first
        user_info = authenticated_client.get_current_user_info()
        assert "email" in user_info, "Should be authenticated initially"
        
        # Logout
        logout_result = authenticated_client.logout()
        assert "message" in logout_result, "Logout should return success message"
        
        print(f"✅ Logout successful: {logout_result.get('message')}")
        
        # Note: In stateless JWT, logout is primarily client-side
        # The token is still valid until expiry, but client should discard it
    
    def test_token_refresh_functionality(self, api_client: APIClient, test_data_manager: TestDataManager):
        """Test token refresh workflow."""
        print("\n🔄 Testing Token Refresh")
        
        # Create and login user
        user_data = test_data_manager.generate_test_user_data("refresh_test")
        api_client.register_user(**user_data)
        
        login_result = api_client.login_user(user_data["email"], user_data["password"])
        
        assert "access_token" in login_result, "Login should provide access token"
        assert "refresh_token" in login_result, "Login should provide refresh token"
        
        original_access_token = login_result["access_token"]
        print(f"✅ Original access token: {original_access_token[:20]}...")
        
        # Use refresh token to get new access token
        refresh_result = api_client.refresh_access_token()
        
        assert "access_token" in refresh_result, "Refresh should provide new access token"
        new_access_token = refresh_result["access_token"]
        
        # Verify we got a new token (different from original)
        assert new_access_token != original_access_token, "New token should be different"
        print(f"✅ New access token: {new_access_token[:20]}...")
        
        # Verify new token works
        user_info = api_client.get_current_user_info()
        assert user_info["email"] == user_data["email"], "New token should work for API calls"
        print("✅ New token works for authenticated requests")
    
    def test_authentication_error_scenarios(self, api_client: APIClient):
        """Test authentication error scenarios."""
        print("\n❌ Testing Authentication Error Scenarios")
        
        # Test 1: Invalid login credentials
        print("\n🔒 Test 1: Invalid login credentials")
        response = api_client._make_request(
            "POST", "/auth/login",
            data={"email": "nonexistent@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401, "Invalid credentials should be rejected"
        print("✅ Invalid credentials correctly rejected")
        
        # Test 2: Invalid refresh token
        print("\n🔄 Test 2: Invalid refresh token")
        api_client.refresh_token = "invalid_refresh_token"
        response = api_client._make_request(
            "POST", "/auth/refresh",
            data={"refresh_token": "invalid_refresh_token"}
        )
        assert response.status_code in [401, 422], "Invalid refresh token should be rejected"
        print("✅ Invalid refresh token correctly rejected")
        
        # Test 3: Unauthorized access to protected endpoint
        print("\n🚫 Test 3: Unauthorized access")
        api_client.access_token = None  # Remove token
        response = api_client._make_request("GET", "/auth/me", use_auth=False)
        assert response.status_code == 401, "Unauthorized access should be rejected"
        print("✅ Unauthorized access correctly rejected")
        
        # Test 4: Malformed token
        print("\n🔧 Test 4: Malformed token")
        api_client.access_token = "invalid.jwt.token"
        response = api_client._make_request("GET", "/auth/me", use_auth=True)
        assert response.status_code == 401, "Malformed token should be rejected"
        print("✅ Malformed token correctly rejected")
    
    def test_registration_validation(self, api_client: APIClient):
        """Test user registration validation."""
        print("\n📝 Testing Registration Validation")
        
        # Test 1: Valid registration (baseline)
        print("\n✅ Test 1: Valid registration")
        unique_email = api_client.generate_unique_email("valid_reg")
        valid_data = {
            "email": unique_email,
            "password": "ValidPassword123!",
            "first_name": "Valid",
            "last_name": "User",
            "phone": "+1234567890"
        }
        
        user = api_client.register_user(**valid_data)
        assert "id" in user, "Valid registration should succeed"
        print(f"✅ Valid registration successful: {user['email']}")
        
        # Test 2: Duplicate email
        print("\n❌ Test 2: Duplicate email")
        response = api_client._make_request("POST", "/auth/register", data=valid_data)
        assert response.status_code == 409, "Duplicate email should be rejected"
        print("✅ Duplicate email correctly rejected")
        
        # Test 3: Invalid email format
        print("\n❌ Test 3: Invalid email format")
        invalid_email_data = valid_data.copy()
        invalid_email_data["email"] = "invalid-email-format"
        
        response = api_client._make_request("POST", "/auth/register", data=invalid_email_data)
        assert response.status_code == 422, "Invalid email format should be rejected"
        print("✅ Invalid email format correctly rejected")
        
        # Test 4: Weak password
        print("\n❌ Test 4: Weak password")
        weak_password_data = valid_data.copy()
        weak_password_data["email"] = api_client.generate_unique_email("weak_pw")
        weak_password_data["password"] = "123"  # Too short
        
        response = api_client._make_request("POST", "/auth/register", data=weak_password_data)
        assert response.status_code == 422, "Weak password should be rejected"
        print("✅ Weak password correctly rejected")
    
    @pytest.mark.parametrize("missing_field", ["email", "password", "first_name", "last_name"])
    def test_registration_required_fields(self, api_client: APIClient, missing_field: str):
        """Test that all required fields are validated in registration."""
        print(f"\n📋 Testing missing required field: {missing_field}")
        
        valid_data = {
            "email": api_client.generate_unique_email("missing_field"),
            "password": "ValidPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890"
        }
        
        # Remove the required field
        del valid_data[missing_field]
        
        response = api_client._make_request("POST", "/auth/register", data=valid_data)
        assert response.status_code == 422, f"Missing {missing_field} should be rejected"
        print(f"✅ Missing {missing_field} correctly rejected")
