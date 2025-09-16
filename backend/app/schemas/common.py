"""Common Pydantic schemas."""

from typing import Generic, TypeVar, List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

T = TypeVar('T')


class BaseResponse(BaseModel):
    """Base response schema."""
    
    class Config:
        from_attributes = True
        use_enum_values = True


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response schema."""
    
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class ErrorResponse(BaseResponse):
    """Error response schema."""
    
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    error_type: Optional[str] = Field(None, description="Error type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class SuccessResponse(BaseResponse):
    """Success response schema."""
    
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class HealthResponse(BaseResponse):
    """Health check response schema."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(..., description="Service version")
    database: str = Field(..., description="Database status")
    redis: str = Field(..., description="Redis status")


class TokenResponse(BaseResponse):
    """Token response schema."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class SearchRequest(BaseModel):
    """Search request schema."""
    
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")


class TimeRangeRequest(BaseModel):
    """Time range request schema."""
    
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LocationRequest(BaseModel):
    """Location-based search request."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    radius_km: float = Field(default=10.0, ge=0.1, le=100, description="Search radius in kilometers")
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")


class StatisticsRequest(BaseModel):
    """Statistics request schema."""
    
    start_date: datetime = Field(..., description="Start date for statistics")
    end_date: datetime = Field(..., description="End date for statistics")
    group_by: Optional[str] = Field(None, description="Group statistics by (day, week, month)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
