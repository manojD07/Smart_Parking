"""Pytest configuration and fixtures."""

import pytest
import time
from typing import Generator, Dict, Any

from utils.api_client import APIClient
from utils.test_helpers import TestDataManager, wait_for_api_ready
from config import config


@pytest.fixture(scope="session", autouse=True)
def ensure_api_ready():
    """Ensure API is ready before running tests."""
    print("\n🔍 Checking if Smart Parking API is ready...")
    
    if not wait_for_api_ready(max_attempts=30, delay=2.0):
        pytest.fail("Smart Parking API is not ready. Please ensure the backend is running.")
    
    print("✅ Smart Parking API is ready!")


@pytest.fixture(scope="function")
def api_client() -> Generator[APIClient, None, None]:
    """Create API client for each test."""
    client = APIClient()
    yield client
    client.cleanup()


@pytest.fixture(scope="function")
def authenticated_client() -> Generator[APIClient, None, None]:
    """Create authenticated API client with a fresh user."""
    client = APIClient()
    data_manager = TestDataManager()
    
    # Create and login test user
    user_data = data_manager.generate_test_user_data()
    
    # Register user
    client.register_user(
        email=user_data["email"],
        password=user_data["password"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        phone=user_data["phone"]
    )
    
    # Login user
    client.login_user(user_data["email"], user_data["password"])
    
    yield client
    client.cleanup()


@pytest.fixture(scope="function")
def admin_client() -> Generator[APIClient, None, None]:
    """Create authenticated admin client."""
    client = APIClient()
    
    # Login admin user
    try:
        client.login_user(config.ADMIN_EMAIL, config.ADMIN_PASSWORD)
    except Exception as e:
        pytest.skip(f"Admin login failed: {e}")
    
    yield client
    client.cleanup()


@pytest.fixture(scope="function")
def test_data_manager() -> TestDataManager:
    """Create test data manager."""
    return TestDataManager()


@pytest.fixture(scope="function")
def sample_booking_data(test_data_manager: TestDataManager) -> Dict[str, Any]:
    """Generate sample booking data."""
    return test_data_manager.generate_booking_data(
        lot_id=config.TEST_PARKING_LOT_ID,
        vehicle_type="car",
        hours_from_now=1,
        duration_hours=2
    )


@pytest.fixture(scope="function")
def sample_lot_data(test_data_manager: TestDataManager) -> Dict[str, Any]:
    """Generate sample parking lot data."""
    return test_data_manager.generate_parking_lot_data()


@pytest.fixture(scope="function")
def performance_timer():
    """Timer fixture for performance tests."""
    start_time = time.time()
    yield lambda: time.time() - start_time


def pytest_runtest_setup(item):
    """Setup for each test."""
    print(f"\n🧪 Running: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """Teardown for each test."""
    if hasattr(item, "rep_call") and item.rep_call.failed:
        print(f"❌ Test failed: {item.name}")
    else:
        print(f"✅ Test passed: {item.name}")


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression test"
    )
    config.addinivalue_line(
        "markers", "user_journey: mark test as user journey test"
    )
    config.addinivalue_line(
        "markers", "admin_journey: mark test as admin journey test"
    )
    config.addinivalue_line(
        "markers", "booking_flow: mark test as booking flow test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add markers based on test file names
        if "smoke" in item.nodeid:
            item.add_marker(pytest.mark.smoke)
        elif "user_journey" in item.nodeid:
            item.add_marker(pytest.mark.user_journey)
        elif "admin" in item.nodeid:
            item.add_marker(pytest.mark.admin_journey)
        elif "booking" in item.nodeid:
            item.add_marker(pytest.mark.booking_flow)
        elif "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
