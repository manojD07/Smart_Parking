"""Booking schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class BookingCreate(BaseModel):
    """Booking creation schema."""
    
    lot_id: UUID = Field(..., description="Parking lot ID")
    vehicle_type: str = Field(..., description="Vehicle type (car/bike)")
    vehicle_number: str = Field(..., min_length=3, max_length=20, description="Vehicle number")
    start_time: datetime = Field(..., description="Booking start time (UTC)")
    end_time: datetime = Field(..., description="Booking end time (UTC)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookingUpdate(BaseModel):
    """Booking update schema."""
    
    vehicle_number: Optional[str] = Field(None, min_length=3, max_length=20, description="Vehicle number")
    start_time: Optional[datetime] = Field(None, description="Booking start time (UTC)")
    end_time: Optional[datetime] = Field(None, description="Booking end time (UTC)")


class BookingResponse(BaseModel):
    """Booking response schema."""
    
    id: UUID = Field(..., description="Booking ID")
    user_id: UUID = Field(..., description="User ID")
    lot_id: UUID = Field(..., description="Parking lot ID")
    slot_id: Optional[UUID] = Field(None, description="Parking slot ID")
    vehicle_type: str = Field(..., description="Vehicle type")
    vehicle_number: str = Field(..., description="Vehicle number")
    start_time: datetime = Field(..., description="Booking start time (UTC)")
    end_time: datetime = Field(..., description="Booking end time (UTC)")
    total_amount: Decimal = Field(..., description="Total booking amount")
    status: str = Field(..., description="Booking status")
    booking_reference: str = Field(..., description="Booking reference code")
    check_in_time: Optional[datetime] = Field(None, description="Check-in time (UTC)")
    check_out_time: Optional[datetime] = Field(None, description="Check-out time (UTC)")
    created_at: datetime = Field(..., description="Booking creation time (UTC)")
    updated_at: datetime = Field(..., description="Booking last update time (UTC)")
    
    # Related object names (simplified to avoid async loading issues)
    lot_name: Optional[str] = Field(None, description="Parking lot name")
    lot_address: Optional[str] = Field(None, description="Parking lot address")
    slot_number: Optional[str] = Field(None, description="Parking slot number")
    user_email: Optional[str] = Field(None, description="User email")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
    
    @classmethod
    def from_orm(cls, booking):
        """Create BookingResponse from ORM booking object with related data."""
        return cls(
            id=booking.id,
            user_id=booking.user_id,
            lot_id=booking.lot_id,
            slot_id=booking.slot_id,
            vehicle_type=booking.vehicle_type,
            vehicle_number=booking.vehicle_number,
            start_time=booking.start_time,
            end_time=booking.end_time,
            total_amount=booking.total_amount,
            status=booking.status,
            booking_reference=booking.booking_reference,
            check_in_time=booking.check_in_time,
            check_out_time=booking.check_out_time,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
            # Populate related object data
            lot_name=booking.lot.name if booking.lot else None,
            lot_address=booking.lot.address if booking.lot else None,
            slot_number=booking.slot.slot_number if booking.slot else None,
            user_email=booking.user.email if booking.user else None
        )


class PricingPreviewRequest(BaseModel):
    """Pricing preview request schema."""
    
    lot_id: UUID = Field(..., description="Parking lot ID")
    vehicle_type: str = Field(..., description="Vehicle type (car/bike)")
    start_time: datetime = Field(..., description="Booking start time (UTC)")
    end_time: datetime = Field(..., description="Booking end time (UTC)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PricingBreakdown(BaseModel):
    """Pricing breakdown item."""
    
    rule_name: str = Field(..., description="Pricing rule name")
    rule_type: Optional[str] = Field(None, description="Rule type")
    start_time: datetime = Field(..., description="Start time for this rule (UTC)")
    end_time: datetime = Field(..., description="End time for this rule (UTC)")
    duration_hours: float = Field(..., description="Duration in hours")
    rate_per_hour: float = Field(..., description="Rate per hour")
    multiplier: Optional[float] = Field(None, description="Price multiplier")
    amount: float = Field(..., description="Amount for this segment")


class PricingPreviewResponse(BaseModel):
    """Pricing preview response schema."""
    
    total_amount: float = Field(..., description="Total amount")
    duration_hours: float = Field(..., description="Total duration in hours")
    average_rate: float = Field(..., description="Average rate per hour")
    currency: str = Field(default="USD", description="Currency")
    pricing_breakdown: List[PricingBreakdown] = Field(..., description="Detailed pricing breakdown")
    lot_id: str = Field(..., description="Parking lot ID")
    vehicle_type: str = Field(..., description="Vehicle type")
    start_time: str = Field(..., description="Start time (UTC)")
    end_time: str = Field(..., description="End time (UTC)")
