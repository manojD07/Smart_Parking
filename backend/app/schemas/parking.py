"""Parking schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, time
from uuid import UUID
from decimal import Decimal


class ParkingLotBase(BaseModel):
    """Base parking lot schema."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Parking lot name")
    address: str = Field(..., min_length=1, description="Parking lot address")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class ParkingLotCreate(ParkingLotBase):
    """Parking lot creation schema."""
    
    total_car_slots: int = Field(..., ge=0, description="Total car slots")
    total_bike_slots: int = Field(..., ge=0, description="Total bike slots")
    hourly_rate_car: float = Field(..., gt=0, description="Hourly rate for cars")
    hourly_rate_bike: float = Field(..., gt=0, description="Hourly rate for bikes")


class ParkingLotUpdate(BaseModel):
    """Parking lot update schema."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Parking lot name")
    address: Optional[str] = Field(None, min_length=1, description="Parking lot address")
    total_car_slots: Optional[int] = Field(None, ge=0, description="Total car slots")
    total_bike_slots: Optional[int] = Field(None, ge=0, description="Total bike slots")
    hourly_rate_car: Optional[float] = Field(None, gt=0, description="Hourly rate for cars")
    hourly_rate_bike: Optional[float] = Field(None, gt=0, description="Hourly rate for bikes")
    is_active: Optional[bool] = Field(None, description="Whether lot is active")


class ParkingLotResponse(ParkingLotBase):
    """Parking lot response schema."""
    
    id: UUID = Field(..., description="Parking lot ID")
    total_car_slots: int = Field(..., description="Total car slots")
    total_bike_slots: int = Field(..., description="Total bike slots")
    hourly_rate_car: Decimal = Field(..., description="Hourly rate for cars")
    hourly_rate_bike: Decimal = Field(..., description="Hourly rate for bikes")
    is_active: bool = Field(..., description="Whether lot is active")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")
    
    # Available slots for guest search
    available_car_slots: Optional[int] = Field(None, description="Currently available car slots")
    available_bike_slots: Optional[int] = Field(None, description="Currently available bike slots")
    
    class Config:
        from_attributes = True


class ParkingSlotCreate(BaseModel):
    """Parking slot creation schema."""
    
    slot_number: str = Field(..., min_length=1, max_length=10, description="Slot number")
    slot_type: str = Field(..., description="Vehicle type (car/bike)")


class ParkingSlotResponse(BaseModel):
    """Parking slot response schema."""
    
    id: UUID = Field(..., description="Slot ID")
    lot_id: UUID = Field(..., description="Parking lot ID")
    slot_number: str = Field(..., description="Slot number")
    slot_type: str = Field(..., description="Vehicle type")
    status: str = Field(..., description="Slot status")
    is_occupied: bool = Field(..., description="Whether slot is occupied")
    is_reserved: bool = Field(..., description="Whether slot is reserved")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class AvailabilityRequest(BaseModel):
    """Availability check request."""
    
    vehicle_type: str = Field(..., description="Vehicle type (car/bike)")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")


class AvailabilityResponse(BaseModel):
    """Availability response schema."""
    
    total_slots: int = Field(..., description="Total slots for vehicle type")
    occupied_slots: int = Field(..., description="Currently occupied slots")
    available_slots: int = Field(..., description="Available slots")
    occupancy_rate: float = Field(..., description="Occupancy rate percentage")


class LocationSearchRequest(BaseModel):
    """Location search request schema."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    radius_km: float = Field(default=10.0, ge=0.1, le=100, description="Search radius in km")
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")


class PricingRuleCreate(BaseModel):
    """Pricing rule creation schema."""
    
    lot_id: UUID = Field(..., description="Parking lot ID")
    name: str = Field(..., min_length=1, description="Rule name")
    vehicle_type: str = Field(..., description="Vehicle type")
    rule_type: str = Field(..., description="Rule type")
    price_per_hour: float = Field(..., gt=0, description="Price per hour")
    multiplier: float = Field(default=1.0, gt=0, description="Price multiplier")
    start_time: Optional[time] = Field(None, description="Start time")
    end_time: Optional[time] = Field(None, description="End time")
    days_of_week: Optional[List[str]] = Field(None, description="Days of week")
    priority: str = Field(default="normal", description="Rule priority")
    min_charge: Optional[float] = Field(None, ge=0, description="Minimum charge")
    max_charge: Optional[float] = Field(None, ge=0, description="Maximum charge")
