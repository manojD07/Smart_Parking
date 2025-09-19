"""
Booking Validator Service for Smart Parking System

Validates booking requests against duration constraints, operational hours,
and business rules. Integrates with the hybrid duration calculator.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, time
from enum import Enum
from typing import List, Dict, Optional, Tuple
from uuid import UUID
import structlog

from app.services.hybrid_duration_calculator import (
    duration_calculator, DurationValidation, DurationTier
)
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class ValidationResult(str, Enum):
    """Booking validation results."""
    VALID = "valid"
    INVALID_DURATION = "invalid_duration"
    INVALID_TIME_RANGE = "invalid_time_range"
    OUTSIDE_OPERATING_HOURS = "outside_operating_hours"
    DURATION_TOO_SHORT = "duration_too_short"
    DURATION_TOO_LONG = "duration_too_long"
    INVALID_INCREMENT = "invalid_increment"
    SLOT_UNAVAILABLE = "slot_unavailable"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"


@dataclass
class BookingValidationRequest:
    """Request for booking validation."""
    slot_id: UUID
    start_time: datetime
    end_time: datetime
    vehicle_type: str
    user_id: UUID
    lot_id: Optional[UUID] = None
    
    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)


@dataclass
class BookingValidationResponse:
    """Response from booking validation."""
    is_valid: bool
    result: ValidationResult
    message: str
    duration_validation: Optional[DurationValidation] = None
    suggested_start_time: Optional[datetime] = None
    suggested_end_time: Optional[datetime] = None
    alternative_durations: List[int] = None
    warnings: List[str] = None
    metadata: Dict[str, any] = None
    
    def __post_init__(self):
        if self.alternative_durations is None:
            self.alternative_durations = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class BookingValidatorService:
    """
    Service for validating booking requests against business rules.
    
    Performs comprehensive validation including:
    - Duration validation using hybrid model
    - Time range validation
    - Operating hours compliance
    - Business rule enforcement
    """
    
    def __init__(self):
        """Initialize booking validator."""
        from app.core.config import settings
        self.settings = settings
        self.duration_calculator = duration_calculator
        self.logger = logger.bind(service="BookingValidatorService")
    
    def validate_booking_request(
        self, 
        request: BookingValidationRequest
    ) -> BookingValidationResponse:
        """
        Comprehensive validation of a booking request.
        
        Args:
            request: Booking validation request
            
        Returns:
            BookingValidationResponse with validation results
        """
        try:
            # Step 1: Basic time validation
            basic_validation = self._validate_basic_time_constraints(request)
            if not basic_validation.is_valid:
                return basic_validation
            
            # Step 2: Duration validation using hybrid model
            duration_validation = self.duration_calculator.validate_duration(
                request.duration_minutes
            )
            
            if not duration_validation.is_valid:
                return BookingValidationResponse(
                    is_valid=False,
                    result=ValidationResult.INVALID_DURATION,
                    message=duration_validation.reason or "Invalid duration",
                    duration_validation=duration_validation,
                    suggested_end_time=request.start_time + timedelta(
                        minutes=duration_validation.suggested_duration
                    ) if duration_validation.suggested_duration else None,
                    alternative_durations=duration_validation.alternatives
                )
            
            # Step 3: Operating hours validation
            operating_hours_validation = self._validate_operating_hours(request)
            if not operating_hours_validation.is_valid:
                return operating_hours_validation
            
            # Step 4: Business rules validation
            business_rules_validation = self._validate_business_rules(request)
            if not business_rules_validation.is_valid:
                return business_rules_validation
            
            # Step 5: Time precision validation
            precision_validation = self._validate_time_precision(request)
            if not precision_validation.is_valid:
                return precision_validation
            
            # All validations passed
            return BookingValidationResponse(
                is_valid=True,
                result=ValidationResult.VALID,
                message="Booking request is valid",
                duration_validation=duration_validation,
                metadata={
                    "tier": duration_validation.tier.value if duration_validation.tier else None,
                    "increment": duration_validation.increment,
                    "validated_duration": request.duration_minutes
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Error validating booking request",
                error=str(e),
                request=request
            )
            return BookingValidationResponse(
                is_valid=False,
                result=ValidationResult.BUSINESS_RULE_VIOLATION,
                message=f"Validation error: {str(e)}"
            )
    
    def validate_duration_only(self, duration_minutes: int) -> DurationValidation:
        """Quick duration-only validation."""
        return self.duration_calculator.validate_duration(duration_minutes)
    
    def get_valid_durations_for_timeframe(
        self, 
        start_time: datetime, 
        max_end_time: datetime
    ) -> List[int]:
        """Get valid durations that fit within a timeframe."""
        max_duration_minutes = int(
            (max_end_time - start_time).total_seconds() / 60
        )
        
        return self.duration_calculator.get_valid_durations_for_range(
            self.settings.min_booking_duration,
            min(max_duration_minutes, self.settings.max_booking_duration)
        )
    
    def suggest_alternative_times(
        self, 
        request: BookingValidationRequest,
        existing_bookings: List[Tuple[datetime, datetime]] = None,
        demand_level: str = "medium"
    ) -> List[Tuple[datetime, datetime]]:
        """Suggest alternative start/end times for invalid requests with buffer consideration."""
        alternatives = []
        
        # Try adjusting to valid durations
        if request.duration_minutes not in duration_calculator._all_valid_durations:
            valid_durations = duration_calculator._get_nearby_durations(
                request.duration_minutes, 5
            )
            
            for duration in valid_durations:
                alt_end_time = request.start_time + timedelta(minutes=duration)
                
                # Validate with buffer if existing bookings provided
                if existing_bookings:
                    is_valid, _, _ = duration_calculator.validate_booking_with_buffer(
                        request.start_time, alt_end_time, existing_bookings, demand_level
                    )
                    if is_valid:
                        alternatives.append((request.start_time, alt_end_time))
                else:
                    alternatives.append((request.start_time, alt_end_time))
        
        # Try adjusting start time to align with increments
        tier = duration_calculator.get_tier_for_duration(request.duration_minutes)
        if tier:
            increment = duration_calculator._get_increment_for_duration(request.duration_minutes)
            
            # Round start time to nearest increment boundary
            start_minute = request.start_time.minute
            rounded_minute = (start_minute // increment) * increment
            
            if rounded_minute != start_minute:
                adjusted_start = request.start_time.replace(
                    minute=rounded_minute, second=0, microsecond=0
                )
                adjusted_end = adjusted_start + timedelta(minutes=request.duration_minutes)
                
                # Validate with buffer if existing bookings provided
                if existing_bookings:
                    is_valid, _, _ = duration_calculator.validate_booking_with_buffer(
                        adjusted_start, adjusted_end, existing_bookings, demand_level
                    )
                    if is_valid:
                        alternatives.append((adjusted_start, adjusted_end))
                else:
                    alternatives.append((adjusted_start, adjusted_end))
        
        return alternatives[:3]  # Return top 3 alternatives
    
    def validate_booking_with_buffer_check(
        self,
        request: BookingValidationRequest,
        existing_bookings: List[Tuple[datetime, datetime]] = None,
        demand_level: str = "medium"
    ) -> BookingValidationResponse:
        """Enhanced booking validation including buffer time conflicts."""
        
        # First run standard validation
        standard_validation = self.validate_booking_request(request)
        
        if not standard_validation.is_valid or not existing_bookings:
            return standard_validation
        
        # Check buffer time conflicts
        is_valid, conflict_reason, suggested_slots = duration_calculator.validate_booking_with_buffer(
            request.start_time, request.end_time, existing_bookings, demand_level
        )
        
        if not is_valid:
            buffer_time = duration_calculator.calculate_buffer_time(
                request.duration_minutes, demand_level
            )
            
            return BookingValidationResponse(
                is_valid=False,
                result=ValidationResult.BUSINESS_RULE_VIOLATION,
                message=conflict_reason,
                duration_validation=standard_validation.duration_validation,
                alternative_durations=standard_validation.alternative_durations,
                warnings=[
                    f"Buffer time of {buffer_time} minutes is required between bookings",
                    f"Current demand level: {demand_level}"
                ],
                metadata={
                    "buffer_time_minutes": buffer_time,
                    "demand_level": demand_level,
                    "suggested_slots": [
                        {
                            "start_time": slot[0].isoformat(),
                            "end_time": slot[1].isoformat()
                        }
                        for slot in suggested_slots
                    ]
                }
            )
        
        # Add buffer information to successful validation
        buffer_time = duration_calculator.calculate_buffer_time(
            request.duration_minutes, demand_level
        )
        
        _, slot_release_time, _ = duration_calculator.calculate_actual_end_time(
            request.start_time, request.duration_minutes, demand_level
        )
        
        standard_validation.warnings.append(
            f"Slot will be released at {slot_release_time.strftime('%H:%M')} "
            f"(includes {buffer_time}-minute buffer)"
        )
        standard_validation.metadata.update({
            "buffer_time_minutes": buffer_time,
            "slot_release_time": slot_release_time.isoformat(),
            "demand_level": demand_level
        })
        
        return standard_validation
    
    def _validate_basic_time_constraints(
        self, 
        request: BookingValidationRequest
    ) -> BookingValidationResponse:
        """Validate basic time constraints."""
        
        # Check if end time is after start time
        if request.end_time <= request.start_time:
            return BookingValidationResponse(
                is_valid=False,
                result=ValidationResult.INVALID_TIME_RANGE,
                message="End time must be after start time"
            )
        
        # Check if start time is in the future (allow some grace period)
        grace_period = timedelta(minutes=5)
        if request.start_time < datetime.now(timezone.utc) - grace_period:
            return BookingValidationResponse(
                is_valid=False,
                result=ValidationResult.INVALID_TIME_RANGE,
                message="Cannot book in the past"
            )
        
        # Check duration bounds
        if request.duration_minutes < self.settings.min_booking_duration:
            return BookingValidationResponse(
                is_valid=False,
                result=ValidationResult.DURATION_TOO_SHORT,
                message=f"Minimum booking duration is {self.settings.min_booking_duration} minutes",
                suggested_end_time=request.start_time + timedelta(
                    minutes=self.settings.min_booking_duration
                )
            )
        
        if request.duration_minutes > self.settings.max_booking_duration:
            return BookingValidationResponse(
                is_valid=False,
                result=ValidationResult.DURATION_TOO_LONG,
                message=f"Maximum booking duration is {self.settings.max_booking_duration} minutes",
                suggested_end_time=request.start_time + timedelta(
                    minutes=self.settings.max_booking_duration
                )
            )
        
        return BookingValidationResponse(
            is_valid=True,
            result=ValidationResult.VALID,
            message="Basic time constraints satisfied"
        )
    
    def _validate_operating_hours(
        self, 
        request: BookingValidationRequest
    ) -> BookingValidationResponse:
        """Validate against parking lot operating hours."""
        
        # For now, assume 24/7 operation
        # In production, this would check lot-specific operating hours
        operating_start = time(0, 0)  # 12:00 AM
        operating_end = time(23, 59)  # 11:59 PM
        
        booking_start_time = request.start_time.time()
        booking_end_time = request.end_time.time()
        
        # Handle overnight bookings
        if booking_end_time < booking_start_time:
            # Booking spans midnight - allow for 24/7 operation
            pass
        else:
            # Same-day booking
            if (booking_start_time < operating_start or 
                booking_end_time > operating_end):
                return BookingValidationResponse(
                    is_valid=False,
                    result=ValidationResult.OUTSIDE_OPERATING_HOURS,
                    message=f"Booking must be within operating hours: {operating_start} - {operating_end}"
                )
        
        return BookingValidationResponse(
            is_valid=True,
            result=ValidationResult.VALID,
            message="Operating hours validated"
        )
    
    def _validate_business_rules(
        self, 
        request: BookingValidationRequest
    ) -> BookingValidationResponse:
        """Validate against business-specific rules."""
        
        warnings = []
        
        # Rule 1: Peak time duration recommendations
        peak_hours = [7, 8, 9, 17, 18, 19]  # 7-9 AM, 5-7 PM
        if request.start_time.hour in peak_hours:
            if request.duration_minutes > 120:  # 2 hours
                warnings.append(
                    "Long bookings during peak hours may affect availability for other users"
                )
        
        # Rule 2: Weekend pricing notification
        if request.start_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            warnings.append("Weekend pricing may apply")
        
        # Rule 3: Advance booking limits
        max_advance_days = 30
        if request.start_time > datetime.now(timezone.utc) + timedelta(days=max_advance_days):
            return BookingValidationResponse(
                is_valid=False,
                result=ValidationResult.BUSINESS_RULE_VIOLATION,
                message=f"Cannot book more than {max_advance_days} days in advance"
            )
        
        return BookingValidationResponse(
            is_valid=True,
            result=ValidationResult.VALID,
            message="Business rules validated",
            warnings=warnings
        )
    
    def _validate_time_precision(
        self, 
        request: BookingValidationRequest
    ) -> BookingValidationResponse:
        """Validate time precision (minute-level accuracy)."""
        
        # Check for second/microsecond precision
        if (request.start_time.second != 0 or 
            request.start_time.microsecond != 0 or
            request.end_time.second != 0 or 
            request.end_time.microsecond != 0):
            
            # Round to nearest minute
            suggested_start = request.start_time.replace(second=0, microsecond=0)
            suggested_end = request.end_time.replace(second=0, microsecond=0)
            
            return BookingValidationResponse(
                is_valid=False,
                result=ValidationResult.INVALID_TIME_RANGE,
                message="Booking times must be precise to the minute",
                suggested_start_time=suggested_start,
                suggested_end_time=suggested_end
            )
        
        return BookingValidationResponse(
            is_valid=True,
            result=ValidationResult.VALID,
            message="Time precision validated"
        )
    
    def get_duration_tier_info(self) -> Dict[str, any]:
        """Get duration tier information for UI display."""
        return self.duration_calculator.get_duration_summary()


# Global instance for application use
booking_validator = BookingValidatorService()
