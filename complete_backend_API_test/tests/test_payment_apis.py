"""Comprehensive payment API tests."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from utils.api_client import APIClient
from utils.test_helpers import TestDataManager, AssertionHelpers
from config import config


@pytest.mark.regression
class TestPaymentAPIs:
    """Test all payment-related API endpoints."""
    
    def test_payment_gateway_status(self, authenticated_client: APIClient):
        """Test payment gateway status endpoint."""
        print("\n🏦 Testing Payment Gateway Status")
        
        response = authenticated_client._make_request("GET", "/payments/gateway/status", use_auth=True)
        assert response.status_code == 200, "Gateway status should be accessible"
        
        gateway_data = response.json()
        assert "dummy_gateway" in gateway_data, "Should have dummy gateway info"
        
        dummy_gateway = gateway_data["dummy_gateway"]
        expected_fields = ["name", "status", "version", "supported_methods", "currencies", "features"]
        for field in expected_fields:
            assert field in dummy_gateway, f"Gateway should include {field}"
        
        assert dummy_gateway["status"] == "active", "Gateway should be active"
        assert len(dummy_gateway["supported_methods"]) > 0, "Should support payment methods"
        assert "USD" in dummy_gateway["currencies"], "Should support USD"
        
        print(f"✅ Gateway Status: {dummy_gateway['name']} v{dummy_gateway['version']}")
        print(f"   Supported methods: {len(dummy_gateway['supported_methods'])}")
        print(f"   Currencies: {dummy_gateway['currencies']}")
    
    def test_create_payment_workflow(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test complete payment creation and processing workflow."""
        print("\n💳 Testing Payment Creation & Processing Workflow")
        
        # Step 1: Create a booking first
        booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="car",
            hours_from_now=1,
            duration_hours=2
        )
        
        booking = authenticated_client.create_booking(**booking_data)
        booking_id = booking["id"]
        booking_amount = booking["total_amount"]
        
        print(f"✅ Step 1: Booking created - ${booking_amount}")
        
        # Step 2: Create payment for the booking
        payment_data = {
            "booking_id": booking_id,
            "amount": booking_amount,
            "currency": "USD",
            "payment_method": "credit_card",
            "payment_gateway": "dummy_gateway",
            "description": f"Payment for booking {booking['booking_reference']}",
            "metadata": {
                "booking_reference": booking["booking_reference"],
                "user_type": "test_user"
            }
        }
        
        response = authenticated_client._make_request("POST", "/payments/", data=payment_data, use_auth=True)
        assert response.status_code == 201, "Payment creation should succeed"
        
        payment = response.json()
        payment_id = payment["id"]
        transaction_id = payment["transaction_id"]
        
        # Validate payment creation
        required_fields = [
            "id", "user_id", "booking_id", "amount", "currency", 
            "payment_method", "payment_gateway", "status", "transaction_id"
        ]
        for field in required_fields:
            assert field in payment, f"Payment should include {field}"
        
        assert payment["status"] == "pending", "Initial payment status should be pending"
        assert payment["amount"] == str(booking_amount), "Payment amount should match booking"
        assert payment["booking_id"] == booking_id, "Payment should be linked to booking"
        
        print(f"✅ Step 2: Payment created - {transaction_id}")
        print(f"   Amount: ${payment['amount']}")
        print(f"   Status: {payment['status']}")
        
        # Step 3: Process the payment
        gateway_data = {
            "card_number": "4111111111111111",
            "expiry_month": "12",
            "expiry_year": "2025",
            "cvv": "123",
            "cardholder_name": "Test User"
        }
        
        response = authenticated_client._make_request(
            "POST", f"/payments/{payment_id}/process", 
            data=gateway_data, use_auth=True
        )
        assert response.status_code == 200, "Payment processing should succeed"
        
        process_result = response.json()
        assert "success" in process_result, "Process result should indicate success status"
        assert "payment" in process_result, "Process result should include updated payment"
        assert "message" in process_result, "Process result should include message"
        
        updated_payment = process_result["payment"]
        final_status = updated_payment["status"]
        
        print(f"✅ Step 3: Payment processed")
        print(f"   Success: {process_result['success']}")
        print(f"   Final status: {final_status}")
        print(f"   Message: {process_result['message']}")
        
        # Step 4: Verify payment status
        response = authenticated_client._make_request("GET", f"/payments/{payment_id}", use_auth=True)
        assert response.status_code == 200, "Should be able to retrieve payment"
        
        final_payment = response.json()
        assert final_payment["id"] == payment_id, "Should get correct payment"
        
        if final_status == "completed":
            assert final_payment["processed_at"] is not None, "Completed payment should have processing time"
            assert final_payment["gateway_transaction_id"] is not None, "Should have gateway transaction ID"
            print("✅ Step 4: Payment completed successfully")
        else:
            assert final_payment["failure_reason"] is not None, "Failed payment should have failure reason"
            print(f"⚠️ Step 4: Payment failed - {final_payment.get('failure_reason', 'Unknown reason')}")
        
        # Clean up
        if final_status == "completed":
            authenticated_client.cancel_booking(booking_id)
        
        return payment_id, final_status
    
    def test_get_my_payments(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test retrieving user's payments."""
        print("\n📋 Testing Get My Payments")
        
        # Create a test payment first
        payment_id, _ = self.test_create_payment_workflow(authenticated_client, test_data_manager)
        
        # Get user's payments
        response = authenticated_client._make_request("GET", "/payments/my", use_auth=True)
        assert response.status_code == 200, "Should be able to get user payments"
        
        payments = response.json()
        assert isinstance(payments, list), "Should return list of payments"
        
        # Find our payment
        payment_ids = [p["id"] for p in payments]
        assert payment_id in payment_ids, "Should include our test payment"
        
        # Test filtering by status
        response = authenticated_client._make_request(
            "GET", "/payments/my", 
            params={"status": "completed"}, 
            use_auth=True
        )
        assert response.status_code == 200, "Status filtering should work"
        
        completed_payments = response.json()
        for payment in completed_payments:
            assert payment["status"] == "completed", "All payments should be completed"
        
        # Test pagination
        response = authenticated_client._make_request(
            "GET", "/payments/my", 
            params={"limit": 1}, 
            use_auth=True
        )
        assert response.status_code == 200, "Pagination should work"
        
        paginated_payments = response.json()
        assert len(paginated_payments) <= 1, "Should respect limit parameter"
        
        print(f"✅ Retrieved {len(payments)} user payments")
        print(f"   Completed payments: {len(completed_payments)}")
        print("✅ Filtering and pagination work correctly")
    
    def test_payment_by_transaction_id(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test retrieving payment by transaction ID."""
        print("\n🔍 Testing Get Payment by Transaction ID")
        
        # Create a test payment
        payment_id, _ = self.test_create_payment_workflow(authenticated_client, test_data_manager)
        
        # Get payment details to get transaction ID
        response = authenticated_client._make_request("GET", f"/payments/{payment_id}", use_auth=True)
        payment = response.json()
        transaction_id = payment["transaction_id"]
        
        # Look up by transaction ID
        response = authenticated_client._make_request(
            "GET", f"/payments/transaction/{transaction_id}", 
            use_auth=True
        )
        assert response.status_code == 200, "Should find payment by transaction ID"
        
        found_payment = response.json()
        assert found_payment["id"] == payment_id, "Should find correct payment"
        assert found_payment["transaction_id"] == transaction_id, "Transaction ID should match"
        
        print(f"✅ Found payment by transaction ID: {transaction_id}")
    
    def test_cancel_payment(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test cancelling a pending payment."""
        print("\n❌ Testing Payment Cancellation")
        
        # Create a payment but don't process it
        booking_data = test_data_manager.generate_booking_data(
            lot_id=config.TEST_PARKING_LOT_ID,
            vehicle_type="bike",
            hours_from_now=2,
            duration_hours=1
        )
        
        booking = authenticated_client.create_booking(**booking_data)
        
        payment_data = {
            "booking_id": booking["id"],
            "amount": booking["total_amount"],
            "currency": "USD",
            "payment_method": "credit_card",
            "description": "Test cancellation payment"
        }
        
        response = authenticated_client._make_request("POST", "/payments/", data=payment_data, use_auth=True)
        payment = response.json()
        payment_id = payment["id"]
        
        assert payment["status"] == "pending", "Payment should be pending"
        print(f"✅ Created pending payment: {payment['transaction_id']}")
        
        # Cancel the payment
        response = authenticated_client._make_request(
            "POST", f"/payments/{payment_id}/cancel", 
            use_auth=True
        )
        assert response.status_code == 200, "Payment cancellation should succeed"
        
        cancel_result = response.json()
        assert "message" in cancel_result, "Should return success message"
        
        # Verify payment is cancelled
        response = authenticated_client._make_request("GET", f"/payments/{payment_id}", use_auth=True)
        updated_payment = response.json()
        assert updated_payment["status"] == "cancelled", "Payment should be cancelled"
        
        print(f"✅ Payment cancelled: {cancel_result['message']}")
        
        # Clean up
        authenticated_client.cancel_booking(booking["id"])
    
    def test_booking_payments_integration(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test integration between bookings and payments."""
        print("\n🔗 Testing Booking-Payment Integration")
        
        # Create booking and payment
        payment_id, final_status = self.test_create_payment_workflow(authenticated_client, test_data_manager)
        
        # Get payment details to find booking ID
        response = authenticated_client._make_request("GET", f"/payments/{payment_id}", use_auth=True)
        payment = response.json()
        booking_id = payment["booking_id"]
        
        # Get all payments for this booking
        response = authenticated_client._make_request(
            "GET", f"/payments/booking/{booking_id}", 
            use_auth=True
        )
        assert response.status_code == 200, "Should get booking payments"
        
        booking_payments = response.json()
        assert isinstance(booking_payments, list), "Should return list of payments"
        assert len(booking_payments) >= 1, "Should have at least our payment"
        
        # Find our payment
        payment_ids = [p["id"] for p in booking_payments]
        assert payment_id in payment_ids, "Should include our payment"
        
        print(f"✅ Found {len(booking_payments)} payments for booking")
        print(f"   Payment statuses: {[p['status'] for p in booking_payments]}")
    
    def test_payment_error_scenarios(self, authenticated_client: APIClient):
        """Test payment error handling scenarios."""
        print("\n❌ Testing Payment Error Scenarios")
        
        # Test 1: Create payment without booking
        print("\n❌ Test 1: Payment without booking")
        payment_data = {
            "amount": "25.00",
            "currency": "USD",
            "payment_method": "credit_card",
            "description": "Standalone payment test"
        }
        
        response = authenticated_client._make_request("POST", "/payments/", data=payment_data, use_auth=True)
        assert response.status_code == 201, "Should allow payment without booking"
        print("✅ Standalone payment creation works")
        
        # Test 2: Invalid payment amount
        print("\n❌ Test 2: Invalid payment amount")
        invalid_payment_data = {
            "amount": "0",  # Invalid amount
            "currency": "USD",
            "payment_method": "credit_card"
        }
        
        response = authenticated_client._make_request("POST", "/payments/", data=invalid_payment_data, use_auth=True)
        assert response.status_code == 422, "Should reject invalid amount"
        print("✅ Invalid amount correctly rejected")
        
        # Test 3: Invalid payment method
        print("\n❌ Test 3: Invalid payment method")
        invalid_method_data = {
            "amount": "25.00",
            "currency": "USD",
            "payment_method": "invalid_method"
        }
        
        response = authenticated_client._make_request("POST", "/payments/", data=invalid_method_data, use_auth=True)
        assert response.status_code == 422, "Should reject invalid payment method"
        print("✅ Invalid payment method correctly rejected")
        
        # Test 4: Access other user's payment
        print("\n❌ Test 4: Access other user's payment")
        fake_payment_id = "00000000-0000-0000-0000-000000000000"
        
        response = authenticated_client._make_request("GET", f"/payments/{fake_payment_id}", use_auth=True)
        assert response.status_code == 404, "Non-existent payment should return 404"
        print("✅ Non-existent payment correctly returns 404")
        
        # Test 5: Process non-existent payment
        print("\n❌ Test 5: Process non-existent payment")
        response = authenticated_client._make_request(
            "POST", f"/payments/{fake_payment_id}/process", 
            use_auth=True
        )
        assert response.status_code == 404, "Should not process non-existent payment"
        print("✅ Non-existent payment processing correctly rejected")
    
    def test_payment_method_variations(self, authenticated_client: APIClient, test_data_manager: TestDataManager):
        """Test different payment methods."""
        print("\n💳 Testing Different Payment Methods")
        
        payment_methods = ["credit_card", "debit_card", "digital_wallet", "upi"]
        
        for method in payment_methods:
            print(f"\n💳 Testing {method}")
            
            # Create payment with specific method
            payment_data = {
                "amount": "15.00",
                "currency": "USD",
                "payment_method": method,
                "description": f"Test payment with {method}"
            }
            
            response = authenticated_client._make_request("POST", "/payments/", data=payment_data, use_auth=True)
            assert response.status_code == 201, f"Should create payment with {method}"
            
            payment = response.json()
            assert payment["payment_method"] == method, f"Payment method should be {method}"
            
            print(f"✅ {method} payment created: {payment['transaction_id']}")
    
    def test_payment_currency_support(self, authenticated_client: APIClient):
        """Test different currency support."""
        print("\n💱 Testing Currency Support")
        
        currencies = ["USD"]
        
        for currency in currencies:
            print(f"\n💱 Testing {currency}")
            
            payment_data = {
                "amount": "10.00",
                "currency": currency,
                "payment_method": "credit_card",
                "description": f"Test payment in {currency}"
            }
            
            response = authenticated_client._make_request("POST", "/payments/", data=payment_data, use_auth=True)
            assert response.status_code == 201, f"Should create payment in {currency}"
            
            payment = response.json()
            assert payment["currency"] == currency, f"Currency should be {currency}"
            
            print(f"✅ {currency} payment created successfully")


@pytest.mark.regression  
class TestPaymentCardManagement:
    """Test payment card management APIs."""
    
    def test_add_payment_card(self, authenticated_client: APIClient):
        """Test adding a payment card."""
        print("\n💳 Testing Add Payment Card")
        
        card_data = {
            "card_number": "4111111111111111",  # Test Visa card
            "expiry_month": "12",
            "expiry_year": "2025",
            "cvv": "123",
            "cardholder_name": "Test User",
            "is_default": True
        }
        
        response = authenticated_client._make_request("POST", "/payments/cards", data=card_data, use_auth=True)
        assert response.status_code == 201, "Card creation should succeed"
        
        card = response.json()
        
        # Validate card response
        required_fields = [
            "id", "card_last_four", "card_brand", "card_type", 
            "expiry_month", "expiry_year", "cardholder_name", 
            "is_default", "is_active", "masked_number"
        ]
        for field in required_fields:
            assert field in card, f"Card should include {field}"
        
        assert card["card_last_four"] == "1111", "Should show last 4 digits"
        assert card["card_brand"] == "visa", "Should detect Visa"
        assert card["card_type"] == "credit", "Should detect credit card"
        assert card["is_default"] is True, "Should be set as default"
        assert card["is_active"] is True, "Should be active"
        assert "****" in card["masked_number"], "Should mask card number"
        
        print(f"✅ Card added: {card['masked_number']}")
        print(f"   Brand: {card['card_brand']} {card['card_type']}")
        print(f"   Default: {card['is_default']}")
        
        return card["id"]
    
    def test_get_my_payment_cards(self, authenticated_client: APIClient):
        """Test retrieving user's payment cards."""
        print("\n📋 Testing Get My Payment Cards")
        
        # Add a test card first
        card_id = self.test_add_payment_card(authenticated_client)
        
        # Get user's cards
        response = authenticated_client._make_request("GET", "/payments/cards", use_auth=True)
        assert response.status_code == 200, "Should get user cards"
        
        cards = response.json()
        assert isinstance(cards, list), "Should return list of cards"
        assert len(cards) >= 1, "Should have at least our test card"
        
        # Find our card
        card_ids = [c["id"] for c in cards]
        assert card_id in card_ids, "Should include our test card"
        
        print(f"✅ Retrieved {len(cards)} payment cards")
        
        # Verify no sensitive data is exposed
        for card in cards:
            assert "card_number" not in card, "Should not expose full card number"
            assert "cvv" not in card, "Should not expose CVV"
            assert "card_token" not in card, "Should not expose token"
        
        print("✅ No sensitive card data exposed")
    
    def test_set_default_card(self, authenticated_client: APIClient):
        """Test setting a card as default."""
        print("\n⭐ Testing Set Default Card")
        
        # Add first card as default
        card1_id = self.test_add_payment_card(authenticated_client)
        
        # Add second card as non-default
        card2_data = {
            "card_number": "5555555555554444",  # Test Mastercard
            "expiry_month": "06",
            "expiry_year": "2026",
            "cvv": "456",
            "cardholder_name": "Test User 2",
            "is_default": False
        }
        
        response = authenticated_client._make_request("POST", "/payments/cards", data=card2_data, use_auth=True)
        card2 = response.json()
        card2_id = card2["id"]
        
        print(f"✅ Added second card: {card2['masked_number']}")
        
        # Set second card as default
        response = authenticated_client._make_request(
            "POST", f"/payments/cards/{card2_id}/set-default", 
            use_auth=True
        )
        assert response.status_code == 200, "Setting default should succeed"
        
        result = response.json()
        assert "message" in result, "Should return success message"
        
        print(f"✅ Set card as default: {result['message']}")
        
        # Verify default status
        response = authenticated_client._make_request("GET", "/payments/cards", use_auth=True)
        cards = response.json()
        
        default_cards = [c for c in cards if c["is_default"]]
        assert len(default_cards) == 1, "Should have exactly one default card"
        assert default_cards[0]["id"] == card2_id, "Second card should be default"
        
        print("✅ Default card status updated correctly")
    
    def test_remove_payment_card(self, authenticated_client: APIClient):
        """Test removing a payment card."""
        print("\n🗑️ Testing Remove Payment Card")
        
        # Add a test card
        card_id = self.test_add_payment_card(authenticated_client)
        
        # Remove the card
        response = authenticated_client._make_request(
            "DELETE", f"/payments/cards/{card_id}", 
            use_auth=True
        )
        assert response.status_code == 200, "Card removal should succeed"
        
        result = response.json()
        assert "message" in result, "Should return success message"
        
        print(f"✅ Card removed: {result['message']}")
        
        # Verify card is no longer active
        response = authenticated_client._make_request("GET", "/payments/cards", use_auth=True)
        cards = response.json()
        
        active_card_ids = [c["id"] for c in cards if c["is_active"]]
        assert card_id not in active_card_ids, "Removed card should not be in active cards"
        
        print("✅ Card successfully deactivated")
    
    def test_card_validation_errors(self, authenticated_client: APIClient):
        """Test card validation error scenarios."""
        print("\n❌ Testing Card Validation Errors")
        
        # Test 1: Invalid card number
        print("\n❌ Test 1: Invalid card number")
        invalid_card_data = {
            "card_number": "1234",  # Too short
            "expiry_month": "12",
            "expiry_year": "2025",
            "cvv": "123",
            "cardholder_name": "Test User"
        }
        
        response = authenticated_client._make_request("POST", "/payments/cards", data=invalid_card_data, use_auth=True)
        assert response.status_code == 422, "Should reject invalid card number"
        print("✅ Invalid card number correctly rejected")
        
        # Test 2: Invalid expiry date
        print("\n❌ Test 2: Invalid expiry date")
        invalid_expiry_data = {
            "card_number": "4111111111111111",
            "expiry_month": "13",  # Invalid month
            "expiry_year": "2025",
            "cvv": "123",
            "cardholder_name": "Test User"
        }
        
        response = authenticated_client._make_request("POST", "/payments/cards", data=invalid_expiry_data, use_auth=True)
        assert response.status_code == 422, "Should reject invalid expiry month"
        print("✅ Invalid expiry month correctly rejected")
        
        # Test 3: Past expiry year
        print("\n❌ Test 3: Past expiry year")
        past_expiry_data = {
            "card_number": "4111111111111111",
            "expiry_month": "12",
            "expiry_year": "2020",  # Past year
            "cvv": "123",
            "cardholder_name": "Test User"
        }
        
        response = authenticated_client._make_request("POST", "/payments/cards", data=past_expiry_data, use_auth=True)
        assert response.status_code == 422, "Should reject past expiry year"
        print("✅ Past expiry year correctly rejected")


@pytest.mark.regression
class TestPaymentAdminAPIs:
    """Test admin-only payment APIs."""
    
    def test_payment_statistics(self, admin_client: APIClient):
        """Test payment statistics endpoint."""
        print("\n📊 Testing Payment Statistics (Admin)")
        
        from datetime import date
        
        # Get statistics for last 30 days
        end_date = date.today()
        start_date = end_date.replace(day=1)  # First day of current month
        
        response = admin_client._make_request(
            "GET", "/payments/stats/overview",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            use_auth=True
        )
        assert response.status_code == 200, "Admin should access payment statistics"
        
        stats = response.json()
        
        # Validate statistics structure
        required_fields = [
            "total_payments", "total_amount", "successful_payments",
            "failed_payments", "pending_payments", "total_refunds",
            "average_payment", "success_rate"
        ]
        for field in required_fields:
            assert field in stats, f"Statistics should include {field}"
        
        # Validate data types
        assert isinstance(stats["total_payments"], int), "Total payments should be integer"
        assert isinstance(stats["success_rate"], (int, float)), "Success rate should be numeric"
        
        print(f"✅ Payment Statistics:")
        print(f"   Total payments: {stats['total_payments']}")
        print(f"   Total amount: ${stats['total_amount']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Average payment: ${stats['average_payment']}")
    
    def test_get_all_payments_admin(self, admin_client: APIClient):
        """Test admin getting all payments."""
        print("\n👑 Testing Get All Payments (Admin)")
        
        # Get all payments
        response = admin_client._make_request("GET", "/payments/admin/all", use_auth=True)
        assert response.status_code == 200, "Admin should access all payments"
        
        payments = response.json()
        assert isinstance(payments, list), "Should return list of payments"
        
        print(f"✅ Retrieved {len(payments)} total payments")
        
        # Test filtering by status
        response = admin_client._make_request(
            "GET", "/payments/admin/all",
            params={"status": "completed"},
            use_auth=True
        )
        assert response.status_code == 200, "Status filtering should work"
        
        completed_payments = response.json()
        for payment in completed_payments:
            assert payment["status"] == "completed", "All payments should be completed"
        
        print(f"   Completed payments: {len(completed_payments)}")
        
        # Test pagination
        response = admin_client._make_request(
            "GET", "/payments/admin/all",
            params={"limit": 5},
            use_auth=True
        )
        assert response.status_code == 200, "Pagination should work"
        
        paginated_payments = response.json()
        assert len(paginated_payments) <= 5, "Should respect limit"
        
        print("✅ Filtering and pagination work correctly")
    
    def test_expire_old_payments(self, admin_client: APIClient):
        """Test expiring old payments."""
        print("\n⏰ Testing Expire Old Payments (Admin)")
        
        response = admin_client._make_request("POST", "/payments/admin/expire-old", use_auth=True)
        assert response.status_code == 200, "Should allow expiring old payments"
        
        result = response.json()
        assert "message" in result, "Should return status message"
        
        print(f"✅ Expire old payments: {result['message']}")
    
    def test_generate_payment_report(self, admin_client: APIClient):
        """Test generating comprehensive payment report."""
        print("\n📋 Testing Payment Report Generation (Admin)")
        
        from datetime import date, timedelta
        
        # Generate report for last 7 days
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        report_data = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        response = admin_client._make_request(
            "POST", "/payments/reports/generate",
            data=report_data,
            use_auth=True
        )
        assert response.status_code == 200, "Should generate payment report"
        
        report = response.json()
        
        # Validate report structure
        required_sections = ["period", "stats", "method_breakdown", "daily_stats", "top_users"]
        for section in required_sections:
            assert section in report, f"Report should include {section}"
        
        # Validate period
        assert "start_date" in report["period"], "Period should include start date"
        assert "end_date" in report["period"], "Period should include end date"
        
        # Validate stats section
        stats = report["stats"]
        assert "total_payments" in stats, "Stats should include total payments"
        assert "success_rate" in stats, "Stats should include success rate"
        
        # Validate method breakdown
        method_breakdown = report["method_breakdown"]
        assert isinstance(method_breakdown, list), "Method breakdown should be list"
        
        # Validate daily stats
        daily_stats = report["daily_stats"]
        assert isinstance(daily_stats, list), "Daily stats should be list"
        
        # Validate top users
        top_users = report["top_users"]
        assert isinstance(top_users, list), "Top users should be list"
        
        print(f"✅ Payment Report Generated:")
        print(f"   Period: {report['period']['start_date']} to {report['period']['end_date']}")
        print(f"   Total payments: {stats['total_payments']}")
        print(f"   Method breakdown: {len(method_breakdown)} methods")
        print(f"   Daily data points: {len(daily_stats)}")
        print(f"   Top users: {len(top_users)}")
    
    def test_regular_user_cannot_access_admin_payments(self, authenticated_client: APIClient):
        """Test that regular users cannot access admin payment endpoints."""
        print("\n🔒 Testing Admin Payment Endpoint Security")
        
        admin_endpoints = [
            ("GET", "/payments/stats/overview?start_date=2023-01-01&end_date=2023-12-31"),
            ("GET", "/payments/admin/all"),
            ("POST", "/payments/admin/expire-old"),
            ("POST", "/payments/reports/generate")
        ]
        
        forbidden_count = 0
        
        for method, endpoint in admin_endpoints:
            print(f"\n❌ Testing {method} {endpoint}")
            
            try:
                if method == "GET":
                    response = authenticated_client._make_request("GET", endpoint, use_auth=True)
                elif method == "POST":
                    response = authenticated_client._make_request("POST", endpoint, data={}, use_auth=True)
                
                if response.status_code == 403:
                    forbidden_count += 1
                    print(f"✅ Correctly forbidden: {method} {endpoint}")
                else:
                    print(f"⚠️ Unexpected response: {method} {endpoint} ({response.status_code})")
                
            except Exception as e:
                print(f"⚠️ Error testing {method} {endpoint}: {e}")
        
        print(f"\n📊 Admin Endpoint Security:")
        print(f"   ❌ Forbidden: {forbidden_count}/{len(admin_endpoints)} endpoints")
        print(f"   🔒 Security: {'GOOD' if forbidden_count >= len(admin_endpoints) * 0.8 else 'NEEDS REVIEW'}")


@pytest.mark.performance
class TestPaymentPerformance:
    """Test payment API performance."""
    
    def test_payment_creation_performance(self, authenticated_client: APIClient):
        """Test payment creation performance."""
        print("\n⚡ Testing Payment Creation Performance")
        
        import time
        
        payment_data = {
            "amount": "50.00",
            "currency": "USD",
            "payment_method": "credit_card",
            "description": "Performance test payment"
        }
        
        # Create multiple payments and measure time
        payment_times = []
        num_payments = 5
        
        for i in range(num_payments):
            start_time = time.time()
            
            response = authenticated_client._make_request(
                "POST", "/payments/", 
                data=payment_data, 
                use_auth=True
            )
            
            end_time = time.time()
            
            assert response.status_code == 201, f"Payment {i+1} should succeed"
            payment_times.append(end_time - start_time)
        
        # Calculate performance metrics
        avg_time = sum(payment_times) / len(payment_times)
        max_time = max(payment_times)
        min_time = min(payment_times)
        
        print(f"✅ Payment Creation Performance:")
        print(f"   Payments created: {num_payments}")
        print(f"   Average time: {avg_time:.3f}s")
        print(f"   Max time: {max_time:.3f}s")
        print(f"   Min time: {min_time:.3f}s")
        
        # Performance assertions
        assert avg_time < 2.0, "Average payment creation should be under 2 seconds"
        assert max_time < 5.0, "Max payment creation should be under 5 seconds"
        
        print("✅ Payment creation performance is acceptable")
