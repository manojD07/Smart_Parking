# Smart Parking Management System - End-to-End API Tests

Comprehensive end-to-end test suite for the Smart Parking Management System backend API.

## 🎯 Overview

This test suite validates the complete functionality of the Smart Parking API through realistic user journeys and system workflows. It covers:

- **Complete User Journeys**: Registration → Login → Browse → Book → Cancel
- **Admin Operations**: Lot management, statistics, user oversight
- **Booking Workflows**: Creation, validation, cancellation, pricing
- **Performance Testing**: Load testing, concurrency, response times
- **Smoke Testing**: Basic functionality validation

## 🏗️ Architecture

```
End_To_End_API_test/
├── tests/
│   ├── test_smoke.py           # Basic functionality tests
│   ├── test_user_journey.py    # Complete user workflows
│   ├── test_booking_flow.py    # Booking-specific scenarios
│   ├── test_admin_journey.py   # Admin functionality tests
│   ├── test_performance.py     # Performance and load tests
│   └── conftest.py            # Pytest configuration and fixtures
├── utils/
│   ├── api_client.py          # Smart Parking API client
│   └── test_helpers.py        # Test utilities and assertions
├── reports/                   # Generated test reports
├── config.py                 # Test configuration
├── requirements.txt          # Python dependencies
├── pytest.ini              # Pytest settings
├── run_tests.py            # Main test runner
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Smart Parking backend running on `http://localhost:8000`
- Docker and Docker Compose (for backend)

### 1. Start the Backend

```bash
cd ../backend
docker-compose up --build
```

### 2. Install Test Dependencies

```bash
cd End_To_End_API_test
pip install -r requirements.txt
```

### 3. Run Tests

```bash
# Run all tests
python run_tests.py

# Run specific test suites
python run_tests.py smoke
python run_tests.py user_journey
python run_tests.py booking_flow
python run_tests.py admin_journey
python run_tests.py performance

# Install dependencies and run tests
python run_tests.py --install-deps

# Run with verbose output
python run_tests.py --verbose
```

## 📊 Test Categories

### 🔥 Smoke Tests (`test_smoke.py`)
Basic functionality validation to ensure the API is operational.

**Covered:**
- ✅ API health check
- ✅ Parking lot listing and details
- ✅ Slot availability checks
- ✅ User registration and login
- ✅ Location-based search
- ✅ Authentication validation

**Run:** `python run_tests.py smoke`

### 👤 User Journey Tests (`test_user_journey.py`)
Complete end-to-end user workflows from registration to booking completion.

**Scenarios:**
- ✅ New user complete journey (register → login → browse → book → cancel)
- ✅ Multiple bookings for different time slots
- ✅ Car and bike booking workflows
- ✅ Booking validation edge cases

**Run:** `python run_tests.py user_journey`

### 📅 Booking Flow Tests (`test_booking_flow.py`)
Detailed booking operation testing and validation.

**Covered:**
- ✅ Complete booking lifecycle
- ✅ Pricing accuracy (car vs bike)
- ✅ Different duration pricing
- ✅ Slot allocation and release
- ✅ Concurrent booking scenarios
- ✅ Booking reference uniqueness

**Run:** `python run_tests.py booking_flow`

### 🔧 Admin Journey Tests (`test_admin_journey.py`)
Administrative functionality and permissions testing.

**Covered:**
- ✅ Parking lot creation and management
- ✅ Lot statistics and reporting
- ✅ Admin data access permissions
- ✅ Security (regular users can't access admin endpoints)
- ✅ Comprehensive admin workflows

**Run:** `python run_tests.py admin_journey`

### ⚡ Performance Tests (`test_performance.py`)
Load testing and performance validation.

**Covered:**
- ✅ API response time benchmarks
- ✅ Authentication performance
- ✅ Booking operation performance
- ✅ Concurrent user load testing
- ✅ Booking throughput testing
- ✅ Availability endpoint under load

**Run:** `python run_tests.py performance`

## 🛠️ Configuration

Edit `config.py` to customize test settings:

```python
class TestConfig:
    API_BASE_URL = "http://localhost:8000"
    TEST_TIMEOUT = 30
    MAX_RETRIES = 3
    
    # Test credentials
    TEST_USER_EMAIL = "e2e_test_user@smartparking.com"
    ADMIN_EMAIL = "admin@smartparking.com"
    ADMIN_PASSWORD = "AdminPassword123!"
    
    # Test data
    TEST_PARKING_LOT_ID = "6a650b0d-2311-4b30-a313-ae7529086f11"
    CLEANUP_TEST_DATA = True
```

## 📈 Test Reports

Tests automatically generate detailed reports:

- **HTML Reports**: `reports/test_report_YYYYMMDD_HHMMSS.html`
- **Coverage Reports**: `reports/coverage/index.html`
- **Console Output**: Real-time test progress and results

### Sample Report Structure:
```
✅ PASS test_smoke.py::TestSmoke::test_api_health_check (0.05s)
✅ PASS test_user_journey.py::TestCompleteUserJourney::test_new_user_complete_journey (12.34s)
✅ PASS test_booking_flow.py::TestBookingFlow::test_complete_booking_lifecycle (8.76s)
```

## 🎭 Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only smoke tests
pytest -m smoke

# Run user journey tests
pytest -m user_journey

# Run admin tests
pytest -m admin_journey

# Run booking flow tests
pytest -m booking_flow

# Run performance tests
pytest -m performance
```

## 🧪 Example Test Scenarios

### Complete User Journey
```python
def test_new_user_complete_journey():
    # 1. Register new user
    # 2. Login and get access token
    # 3. Browse available parking lots
    # 4. Check lot details and availability
    # 5. Get pricing preview
    # 6. Create booking
    # 7. Verify booking in user's list
    # 8. Get booking details
    # 9. Cancel booking
    # 10. Verify cancellation
```

### Concurrent User Load Test
```python
def test_concurrent_user_load():
    # Simulate 5 concurrent users
    # Each performs: register, login, browse, book
    # Validate system handles load gracefully
    # Measure response times and success rates
```

### Admin Workflow Test
```python
def test_admin_comprehensive_workflow():
    # 1. Admin creates new parking lot
    # 2. Verify lot is publicly accessible
    # 3. Check initial statistics (zero bookings)
    # 4. User creates booking for new lot
    # 5. Verify updated statistics
    # 6. Clean up test data
```

## 🔍 Debugging and Troubleshooting

### Common Issues

**API Not Ready:**
```bash
❌ Smart Parking API is not ready!
Solution: Ensure backend is running: docker-compose up --build
```

**Authentication Failures:**
```bash
❌ Admin login failed
Solution: Check admin credentials in config.py
```

**Slow Performance:**
```bash
⚠️ Response time exceeded threshold
Solution: Check system resources and database performance
```

### Verbose Output
Run tests with detailed output:
```bash
python run_tests.py --verbose
```

### Skip Health Check
Skip API health check (if API is confirmed running):
```bash
python run_tests.py --skip-health-check
```

## 📊 Performance Benchmarks

Expected performance thresholds:

| Operation | Expected Time | Threshold |
|-----------|---------------|-----------|
| Health Check | < 0.5s | < 1.0s |
| Get Parking Lots | < 1.0s | < 2.0s |
| User Registration | < 2.0s | < 3.0s |
| User Login | < 1.0s | < 2.0s |
| Create Booking | < 2.0s | < 3.0s |
| Get Availability | < 1.0s | < 2.0s |
| Booking Cancellation | < 1.0s | < 2.0s |

## 🎯 Coverage Goals

- **API Endpoints**: 100% of public endpoints tested
- **User Workflows**: All major user journeys covered
- **Admin Operations**: Complete admin functionality tested
- **Error Scenarios**: Edge cases and validation errors tested
- **Performance**: Load testing under realistic conditions

## 🤝 Contributing

### Adding New Tests

1. Create test file in appropriate category (`tests/test_*.py`)
2. Use appropriate markers (`@pytest.mark.smoke`, etc.)
3. Follow naming convention: `test_descriptive_name`
4. Include docstrings and print statements for clarity
5. Clean up test data in fixtures or teardown

### Test Structure
```python
@pytest.mark.category_name
class TestFeatureName:
    """Test description."""
    
    def test_specific_scenario(self, authenticated_client):
        """Test specific scenario description."""
        print(f"\n🧪 Testing Specific Scenario")
        
        # Arrange
        test_data = generate_test_data()
        
        # Act
        result = authenticated_client.perform_action(test_data)
        
        # Assert
        assert result["status"] == "success"
        print("✅ Test completed successfully")
```

## 🚀 CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start Backend
        run: docker-compose up -d
      - name: Run E2E Tests
        run: |
          cd End_To_End_API_test
          python run_tests.py --install-deps
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    stages {
        stage('Start Backend') {
            steps {
                sh 'docker-compose up -d'
            }
        }
        stage('Run E2E Tests') {
            steps {
                dir('End_To_End_API_test') {
                    sh 'python run_tests.py --install-deps'
                }
            }
        }
    }
}
```

## 📞 Support

- **Issues**: Check test output and reports for detailed error information
- **Configuration**: Review `config.py` for environment-specific settings
- **Logs**: Check `reports/` directory for detailed test reports
- **API**: Ensure Smart Parking backend is running and accessible

---

## 🎉 Success Criteria

When all tests pass, you can be confident that:

✅ **Smart Parking API is fully functional**  
✅ **All user workflows operate correctly**  
✅ **Admin functionality is secure and working**  
✅ **System handles concurrent users appropriately**  
✅ **Performance meets acceptable thresholds**  
✅ **Data integrity is maintained**  
✅ **Error handling works correctly**

**Ready for production deployment! 🚀**

---

## 🎯 **100% API COVERAGE ACHIEVED!** 🎉

### **Complete Backend Coverage**
- **Total APIs**: 42 endpoints
- **Tested APIs**: 42 endpoints ✅  
- **Coverage**: 100% 🎯

#### **Test Suites Available**
```bash
# Core functionality (essential features)
python run_tests.py core

# Extended coverage (100% endpoint testing)  
python run_tests.py extended

# All tests (complete coverage)
python run_tests.py all

# Individual extended test suites
python run_tests.py test_extended_auth.py
python run_tests.py test_extended_bookings.py
python run_tests.py test_extended_parking.py
python run_tests.py test_extended_admin.py
python run_tests.py test_user_management.py
```

#### **Endpoint Coverage Summary**
- 🔐 **Authentication (6/6)**: Register, login, refresh, password change, logout, user info
- 👥 **User Management (13/13)**: Profile, admin operations, search, activation
- 🅿️ **Parking Management (10/10)**: Lots CRUD, slots, availability, search, admin ops
- 📅 **Booking Operations (9/9)**: Create, view, cancel, check-in/out, search, pricing
- 🔧 **Admin Functions (4/4)**: Dashboard, revenue reports, user stats, maintenance

**🚀 The Smart Parking API now has complete test coverage for production deployment!** 🎯
