"""Dummy payment service for demonstration purposes."""

import uuid
import secrets
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any
from datetime import timezone
from app.schemas.payment import PaymentMethod, PaymentStatus, DummyPaymentResponse
from app.models.booking import Booking
import structlog

logger = structlog.get_logger(__name__)


class DummyPaymentService:
    """Dummy payment service for simulating payment processing."""
    
    @staticmethod
    def generate_transaction_id() -> str:
        """Generate a dummy transaction ID."""
        return f"TXN{secrets.token_hex(8).upper()}"
    
    @staticmethod
    def generate_payment_id() -> str:
        """Generate a dummy payment ID."""
        return str(uuid.uuid4())
    
    async def process_payment(
        self,
        booking: Booking,
        payment_method: PaymentMethod,
        simulate_failure: bool = False
    ) -> DummyPaymentResponse:
        """Process a dummy payment for a booking."""
        
        # Simulate some processing time
        import asyncio
        await asyncio.sleep(0.5)
        
        payment_id = self.generate_payment_id()
        transaction_id = self.generate_transaction_id()
        
        # Simulate payment failure for testing
        if simulate_failure:
            logger.warning("Simulating payment failure", booking_id=booking.id)
            return DummyPaymentResponse(
                success=False,
                payment_id=payment_id,
                transaction_id=transaction_id,
                message="Payment failed: Insufficient funds",
                booking_id=str(booking.id),
                amount=booking.total_amount
            )
        
        # Simulate random failure (5% chance)
        import random
        if random.random() < 0.05:
            logger.warning("Random payment failure", booking_id=booking.id)
            return DummyPaymentResponse(
                success=False,
                payment_id=payment_id,
                transaction_id=transaction_id,
                message="Payment failed: Bank declined transaction",
                booking_id=str(booking.id),
                amount=booking.total_amount
            )
        
        # Successful payment
        logger.info("Payment processed successfully", 
                   booking_id=booking.id, 
                   amount=booking.total_amount,
                   payment_method=payment_method.value)
        
        return DummyPaymentResponse(
            success=True,
            payment_id=payment_id,
            transaction_id=transaction_id,
            message="Payment processed successfully",
            booking_id=str(booking.id),
            amount=booking.total_amount
        )
    
    async def validate_payment_method(
        self,
        payment_method: PaymentMethod,
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate payment method details (dummy validation)."""
        
        validation_result = {
            "valid": True,
            "message": "Payment method validated",
            "errors": []
        }
        
        if payment_method == PaymentMethod.CREDIT_CARD:
            # Basic card validation
            card_number = payment_details.get("card_number", "")
            if not card_number or len(card_number) < 4:
                validation_result["valid"] = False
                validation_result["errors"].append("Invalid card number")
            
            expiry_month = payment_details.get("expiry_month", "")
            expiry_year = payment_details.get("expiry_year", "")
            if not expiry_month or not expiry_year:
                validation_result["valid"] = False
                validation_result["errors"].append("Invalid expiry date")
            
            cvv = payment_details.get("cvv", "")
            if not cvv or len(cvv) < 3:
                validation_result["valid"] = False
                validation_result["errors"].append("Invalid CVV")
        
        elif payment_method == PaymentMethod.UPI:
            upi_id = payment_details.get("upi_id", "")
            if not upi_id or "@" not in upi_id:
                validation_result["valid"] = False
                validation_result["errors"].append("Invalid UPI ID")
        
        elif payment_method == PaymentMethod.NET_BANKING:
            bank_name = payment_details.get("bank_name", "")
            if not bank_name:
                validation_result["valid"] = False
                validation_result["errors"].append("Bank name required")
        
        return validation_result
    
    def get_payment_methods(self) -> Dict[str, Dict[str, Any]]:
        """Get available payment methods with their details."""
        return {
            PaymentMethod.CREDIT_CARD.value: {
                "name": "Credit Card",
                "description": "Visa, MasterCard, American Express",
                "icon": "credit-card",
                "fields": ["card_number", "card_holder_name", "expiry_month", "expiry_year", "cvv"]
            },
            PaymentMethod.DEBIT_CARD.value: {
                "name": "Debit Card",
                "description": "Bank debit cards",
                "icon": "credit-card",
                "fields": ["card_number", "card_holder_name", "expiry_month", "expiry_year", "cvv"]
            },
            PaymentMethod.UPI.value: {
                "name": "UPI",
                "description": "Google Pay, PhonePe, Paytm",
                "icon": "mobile-alt",
                "fields": ["upi_id"]
            },
            PaymentMethod.NET_BANKING.value: {
                "name": "Net Banking",
                "description": "Internet Banking",
                "icon": "university",
                "fields": ["bank_name"]
            }
        }
