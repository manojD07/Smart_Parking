#!/usr/bin/env python3
"""Test runner script for Smart Parking E2E Tests."""

import sys
import os
import time
import argparse
import subprocess
from datetime import datetime, timezone

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.api_client import APIClient
from utils.test_helpers import wait_for_api_ready, generate_test_report
from config import config


def check_api_health():
    """Check if the Smart Parking API is healthy."""
    print("🔍 Checking Smart Parking API health...")
    
    if not wait_for_api_ready(max_attempts=10, delay=2.0):
        print("❌ Smart Parking API is not ready!")
        print(f"   Please ensure the backend is running at {config.API_BASE_URL}")
        print("   Run: docker-compose up --build")
        return False
    
    print("✅ Smart Parking API is ready!")
    return True


def run_test_suite(test_type="all", verbose=False, generate_report=True):
    """Run the test suite."""
    print(f"\n🧪 Running {test_type} tests...")
    print("=" * 60)
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.extend(["-v", "-s"])
    
    # Add test type selection
    if test_type == "smoke":
        cmd.extend(["-m", "smoke"])
    elif test_type == "user_journey":
        cmd.extend(["-m", "user_journey"])
    elif test_type == "admin_journey":
        cmd.extend(["-m", "admin_journey"])
    elif test_type == "booking_flow":
        cmd.extend(["-m", "booking_flow"])
    elif test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif test_type == "regression":
        cmd.extend(["-m", "regression"])
    elif test_type == "core":
        cmd.extend(["tests/test_smoke.py", "tests/test_user_journey.py", "tests/test_booking_flow.py"])
    elif test_type == "extended":
        cmd.extend(["tests/test_extended_auth.py", "tests/test_extended_bookings.py", "tests/test_extended_parking.py", "tests/test_extended_admin.py", "tests/test_user_management.py", "tests/test_payment_apis.py"])
    elif test_type != "all":
        # Handle individual test files
        if test_type in ["test_extended_auth.py", "test_extended_bookings.py", "test_extended_parking.py", "test_extended_admin.py", "test_user_management.py", "test_payment_apis.py"]:
            cmd.extend([f"tests/{test_type}"])
        else:
            cmd.extend([f"tests/{test_type}"])
    
    # Add report generation
    if generate_report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/test_report_{timestamp}.html"
        cmd.extend([
            "--html", report_file,
            "--self-contained-html",
            "--cov=utils",
            "--cov-report=html:reports/coverage",
            "--cov-report=term-missing"
        ])
        print(f"📊 Report will be generated: {report_file}")
    
    # Run tests
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        duration = time.time() - start_time
        
        print(f"\n⏱️ Test execution completed in {duration:.2f} seconds")
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print(f"❌ Some tests failed (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def install_dependencies():
    """Install test dependencies."""
    print("📦 Installing test dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_test_environment():
    """Setup test environment."""
    print("🔧 Setting up test environment...")
    
    # Create reports directory
    os.makedirs("reports", exist_ok=True)
    print("✅ Reports directory created")
    
    # Verify configuration
    print(f"🔗 API Base URL: {config.API_BASE_URL}")
    print(f"📡 API Version: {config.API_VERSION}")
    print(f"⏱️ Test Timeout: {config.TEST_TIMEOUT}s")
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Smart Parking E2E Test Runner")
    
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "smoke", "user_journey", "admin_journey", "booking_flow", "performance", "regression"],
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install dependencies before running tests"
    )
    
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip API health check"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Run tests with verbose output"
    )
    
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip report generation"
    )
    
    args = parser.parse_args()
    
    print("🎯 Smart Parking E2E Test Runner")
    print("=" * 60)
    print(f"📅 Start Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"🎪 Test Type: {args.test_type}")
    print(f"🔗 API URL: {config.API_BASE_URL}")
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
    
    # Setup test environment
    if not setup_test_environment():
        sys.exit(1)
    
    # Check API health
    if not args.skip_health_check:
        if not check_api_health():
            sys.exit(1)
    
    # Run tests
    success = run_test_suite(
        test_type=args.test_type,
        verbose=args.verbose,
        generate_report=not args.no_report
    )
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST EXECUTION COMPLETED SUCCESSFULLY!")
        print("✅ All tests passed - Smart Parking API is working correctly")
    else:
        print("💥 TEST EXECUTION FAILED!")
        print("❌ Some tests failed - Please check the output above")
        print("🔍 Check reports/test_report_*.html for detailed results")
    
    print(f"📅 End Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
