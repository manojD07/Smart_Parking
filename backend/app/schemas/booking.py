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
    start_time: datetime = Field(..., description="Booking start time")
    end_time: datetime = Field(..., description="Booking end time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookingUpdate(BaseModel):
    """Booking update schema."""
    
    vehicle_number: Optional[str] = Field(None, min_length=3, max_length=20, description="Vehicle number")
    start_time: Optional[datetime] = Field(None, description="Booking start time")
    end_time: Optional[datetime] = Field(None, description="Booking end time")


class BookingResponse(BaseModel):
    """Booking response schema."""
    
    id: UUID = Field(..., description="Booking ID")
    user_id: UUID = Field(..., description="User ID")
    lot_id: UUID = Field(..., description="Parking lot ID")
    slot_id: Optional[UUID] = Field(None, description="Parking slot ID")
    vehicle_type: str = Field(..., description="Vehicle type")
    vehicle_number: str = Field(..., description="Vehicle number")
    start_time: datetime = Field(..., description="Booking start time")
    end_time: datetime = Field(..., description="Booking end time")
    total_amount: Decimal = Field(..., description="Total booking amount")
    status: str = Field(..., description="Booking status")
    booking_reference: str = Field(..., description="Booking reference code")
    check_in_time: Optional[datetime] = Field(None, description="Check-in time")
    check_out_time: Optional[datetime] = Field(None, description="Check-out time")
    created_at: datetime = Field(..., description="Booking creation time")
    updated_at: datetime = Field(..., description="Booking last update time")
    
    # Related objects
    lot: Optional[Dict[str, Any]] = Field(None, description="Parking lot details")
    slot: Optional[Dict[str, Any]] = Field(None, description="Parking slot details")
    user: Optional[Dict[str, Any]] = Field(None, description="User details")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class PricingPreviewRequest(BaseModel):
    """Pricing preview request schema."""
    
    lot_id: UUID = Field(..., description="Parking lot ID")
    vehicle_type: str = Field(..., description="Vehicle type (car/bike)")
    start_time: datetime = Field(..., description="Booking start time")
    end_time: datetime = Field(..., description="Booking end time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PricingBreakdown(BaseModel):
    """Pricing breakdown item."""
    
    rule_name: str = Field(..., description="Pricing rule name")
    rule_type: Optional[str] = Field(None, description="Rule type")
    start_time: datetime = Field(..., description="Start time for this rule")
    end_time: datetime = Field(..., description="End time for this rule")
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
    start_time: str = Field(..., description="Start time")
    end_time: str = Field(..., description="End time")
