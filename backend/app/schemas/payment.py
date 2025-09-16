"""Payment related schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from decimal import Decimal
import uuid


class PaymentMethod(str, Enum):
    """Payment method options."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    CASH = "cash"


class PaymentStatus(str, Enum):
    """Payment status options."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentCreate(BaseModel):
    """Schema for creating a payment."""
    booking_id: str = Field(..., description="Booking ID for the payment")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    
    # Credit/Debit card details (for demo purposes)
    card_number: Optional[str] = Field(None, description="Card number (last 4 digits)")
    card_holder_name: Optional[str] = Field(None, description="Card holder name")
    expiry_month: Optional[str] = Field(None, description="Card expiry month")
    expiry_year: Optional[str] = Field(None, description="Card expiry year")
    cvv: Optional[str] = Field(None, description="Card CVV")
    
    # UPI details
    upi_id: Optional[str] = Field(None, description="UPI ID")
    
    # Net banking details
    bank_name: Optional[str] = Field(None, description="Bank name")


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: str = Field(..., description="Payment ID")
    booking_id: str = Field(..., description="Booking ID")
    amount: Decimal = Field(..., description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    status: PaymentStatus = Field(..., description="Payment status")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    gateway_response: Optional[str] = Field(None, description="Gateway response")
    created_at: str = Field(..., description="Payment creation time")
    processed_at: Optional[str] = Field(None, description="Payment processing time")
    
    class Config:
        from_attributes = True


class DummyPaymentRequest(BaseModel):
    """Schema for dummy payment processing."""
    booking_id: str = Field(..., description="Booking ID")
    payment_method: PaymentMethod = Field(default=PaymentMethod.CREDIT_CARD, description="Payment method")
    simulate_failure: bool = Field(default=False, description="Simulate payment failure for testing")


class DummyPaymentResponse(BaseModel):
    """Schema for dummy payment response."""
    success: bool = Field(..., description="Payment success status")
    payment_id: str = Field(..., description="Generated payment ID")
    transaction_id: str = Field(..., description="Transaction ID")
    message: str = Field(..., description="Payment status message")
    booking_id: str = Field(..., description="Booking ID")
    amount: Decimal = Field(..., description="Payment amount")