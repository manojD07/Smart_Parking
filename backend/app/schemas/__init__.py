"""Pydantic schemas for request/response validation."""

from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin
from app.schemas.parking import (
    ParkingLotCreate, ParkingLotUpdate, ParkingLotResponse,
    ParkingSlotCreate, ParkingSlotResponse,
    AvailabilityRequest, AvailabilityResponse,
    LocationSearchRequest, PricingRuleCreate
)
from app.schemas.booking import BookingCreate, BookingUpdate, BookingResponse
from app.schemas.auth import UserRegistration, TokenResponse, RefreshTokenRequest, ChangePasswordRequest
from app.schemas.common import PaginatedResponse, ErrorResponse, SuccessResponse

__all__ = [
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserLogin",
    "UserRegistration",
    "TokenResponse",
    "RefreshTokenRequest", 
    "ChangePasswordRequest",
    "ParkingLotCreate",
    "ParkingLotUpdate",
    "ParkingLotResponse",
    "ParkingSlotCreate",
    "ParkingSlotResponse",
    "AvailabilityRequest",
    "AvailabilityResponse",
    "LocationSearchRequest",
    "PricingRuleCreate",
    "BookingCreate",
    "BookingUpdate",
    "BookingResponse", 
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
]
