"""Configuration for End-to-End API Tests."""

import os
from typing import Optional


class TestConfig:
    """Test configuration settings."""
    
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    TEST_TIMEOUT: int = int(os.getenv("TEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))
    
    # Test User Credentials
    TEST_USER_EMAIL: str = os.getenv("TEST_USER_EMAIL", "e2e_test_user@smartparking.com")
    TEST_USER_PASSWORD: str = os.getenv("TEST_USER_PASSWORD", "E2ETestPassword123!")
    TEST_USER_FIRST_NAME: str = os.getenv("TEST_USER_FIRST_NAME", "E2E")
    TEST_USER_LAST_NAME: str = os.getenv("TEST_USER_LAST_NAME", "TestUser")
    TEST_USER_PHONE: str = os.getenv("TEST_USER_PHONE", "+1234567890")
    
    # Admin User Credentials
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@smartparking.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "AdminPassword123!")
    
    # Test Data
    TEST_PARKING_LOT_ID: str = os.getenv("TEST_PARKING_LOT_ID", "6a650b0d-2311-4b30-a313-ae7529086f11")
    TEST_VEHICLE_CAR: str = os.getenv("TEST_VEHICLE_CAR", "ABC123E2E")
    TEST_VEHICLE_BIKE: str = os.getenv("TEST_VEHICLE_BIKE", "BIKE789E2E")
    
    # Test Settings
    CLEANUP_TEST_DATA: bool = os.getenv("CLEANUP_TEST_DATA", "true").lower() == "true"
    GENERATE_REPORTS: bool = os.getenv("GENERATE_REPORTS", "true").lower() == "true"
    PARALLEL_TESTS: bool = os.getenv("PARALLEL_TESTS", "false").lower() == "true"
    
    @property
    def api_url(self) -> str:
        """Get the full API URL."""
        return f"{self.API_BASE_URL}/api/{self.API_VERSION}"
    
    @property
    def headers(self) -> dict:
        """Get default headers."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def auth_headers(self, token: str) -> dict:
        """Get headers with authentication token."""
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        return headers


# Global config instance
config = TestConfig()
