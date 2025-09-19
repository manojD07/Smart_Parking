"""
Schemas for duration validation and hybrid booking system.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from uuid import UUID


class DurationTier(str, Enum):
    """Duration tier categories."""
    MICRO = "micro"
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ValidationResult(str, Enum):
    """Validation result types."""
    VALID = "valid"
    INVALID_DURATION = "invalid_duration"
    INVALID_TIME_RANGE = "invalid_time_range"
    OUTSIDE_OPERATING_HOURS = "outside_operating_hours"
    DURATION_TOO_SHORT = "duration_too_short"
    DURATION_TOO_LONG = "duration_too_long"
    INVALID_INCREMENT = "invalid_increment"
    SLOT_UNAVAILABLE = "slot_unavailable"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"


class DurationValidationRequest(BaseModel):
    """Request for duration validation."""
    duration_minutes: int = Field(
        ..., 
        ge=1, 
        le=480, 
        description="Requested duration in minutes (1-480)"
    )


class DurationValidationResponse(BaseModel):
    """Response from duration validation."""
    is_valid: bool = Field(..., description="Whether duration is valid")
    suggested_duration: Optional[int] = Field(None, description="Suggested valid duration")
    tier: Optional[DurationTier] = Field(None, description="Duration tier")
    increment: Optional[int] = Field(None, description="Tier increment in minutes")
    reason: Optional[str] = Field(None, description="Validation reason/message")
    alternatives: List[int] = Field(default_factory=list, description="Alternative durations")


class BookingValidationRequest(BaseModel):
    """Request for comprehensive booking validation."""
    slot_id: UUID = Field(..., description="Target parking slot ID")
    start_time: datetime = Field(..., description="Booking start time")
    end_time: datetime = Field(..., description="Booking end time")
    vehicle_type: str = Field(..., description="Vehicle type (car/bike)")
    user_id: UUID = Field(..., description="User requesting booking")
    lot_id: Optional[UUID] = Field(None, description="Parking lot ID")
    
    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        """Ensure end time is after start time."""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)


class BookingValidationResponse(BaseModel):
    """Response from comprehensive booking validation."""
    is_valid: bool = Field(..., description="Whether booking request is valid")
    result: ValidationResult = Field(..., description="Validation result type")
    message: str = Field(..., description="Human-readable validation message")
    duration_validation: Optional[DurationValidationResponse] = Field(
        None, description="Duration-specific validation details"
    )
    suggested_start_time: Optional[datetime] = Field(
        None, description="Suggested corrected start time"
    )
    suggested_end_time: Optional[datetime] = Field(
        None, description="Suggested corrected end time"
    )
    alternative_durations: List[int] = Field(
        default_factory=list, description="Alternative valid durations"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Non-blocking validation warnings"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional validation metadata"
    )


class DurationTierInfo(BaseModel):
    """Information about a duration tier."""
    tier: DurationTier = Field(..., description="Tier identifier")
    description: str = Field(..., description="Tier description")
    min_duration: int = Field(..., description="Minimum duration in minutes")
    max_duration: int = Field(..., description="Maximum duration in minutes")
    increment: int = Field(..., description="Duration increment in minutes")
    valid_durations: List[int] = Field(..., description="All valid durations for this tier")


class DurationSystemSummary(BaseModel):
    """Summary of the entire duration system."""
    total_valid_durations: int = Field(..., description="Total number of valid durations")
    min_duration: int = Field(..., description="System minimum duration")
    max_duration: int = Field(..., description="System maximum duration")
    tiers: List[DurationTierInfo] = Field(..., description="All duration tiers")
    overlapping_durations: List[int] = Field(..., description="Durations available in multiple tiers")
    gaps: List[int] = Field(default_factory=list, description="Missing durations (should be empty)")


class AlternativeTimeSlot(BaseModel):
    """Alternative time slot suggestion."""
    start_time: datetime = Field(..., description="Alternative start time")
    end_time: datetime = Field(..., description="Alternative end time")
    duration_minutes: int = Field(..., description="Duration in minutes")
    tier: DurationTier = Field(..., description="Duration tier")
    reason: str = Field(..., description="Why this alternative is suggested")


class TimeValidationRequest(BaseModel):
    """Request for time-based validation."""
    start_time: datetime = Field(..., description="Proposed start time")
    max_end_time: datetime = Field(..., description="Latest acceptable end time")
    preferred_duration: Optional[int] = Field(None, description="Preferred duration in minutes")


class TimeValidationResponse(BaseModel):
    """Response from time-based validation."""
    valid_durations: List[int] = Field(..., description="Valid durations for the time window")
    recommended_duration: Optional[int] = Field(None, description="Recommended duration")
    alternative_slots: List[AlternativeTimeSlot] = Field(
        default_factory=list, description="Alternative time slots"
    )
    warnings: List[str] = Field(default_factory=list, description="Time-related warnings")
