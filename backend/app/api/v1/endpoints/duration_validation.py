"""
API endpoints for duration validation and hybrid booking system.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.api.deps import get_async_session, get_current_active_user
from app.schemas.duration import (
    DurationValidationRequest, DurationValidationResponse,
    BookingValidationRequest, BookingValidationResponse,
    DurationSystemSummary, TimeValidationRequest, TimeValidationResponse,
    AlternativeTimeSlot, DurationTier
)
from app.schemas.common import BaseResponse
from app.services.booking_validator import booking_validator
from app.services.hybrid_duration_calculator import duration_calculator
from app.models.user import User
from app.core.exceptions import ValidationError
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post(
    "/validate-duration",
    response_model=DurationValidationResponse,
    summary="Validate booking duration",
    description="Validates a requested booking duration against the hybrid duration model."
)
async def validate_duration(
    request: DurationValidationRequest,
    current_user: User = Depends(get_current_active_user)
) -> DurationValidationResponse:
    """Validate a single duration value."""
    try:
        validation_result = duration_calculator.validate_duration(request.duration_minutes)
        
        return DurationValidationResponse(
            is_valid=validation_result.is_valid,
            suggested_duration=validation_result.suggested_duration,
            tier=validation_result.tier,
            increment=validation_result.increment,
            reason=validation_result.reason,
            alternatives=validation_result.alternatives or []
        )
        
    except Exception as e:
        logger.error(
            "Error validating duration",
            duration=request.duration_minutes,
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Duration validation failed: {str(e)}"
        )


@router.post(
    "/validate-booking",
    response_model=BookingValidationResponse,
    summary="Comprehensive booking validation",
    description="Performs comprehensive validation of a booking request including duration, time range, and business rules."
)
async def validate_booking(
    request: BookingValidationRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
) -> BookingValidationResponse:
    """Comprehensive booking request validation."""
    try:
        # Override user_id with authenticated user
        request.user_id = current_user.id
        
        validation_result = booking_validator.validate_booking_request(request)
        
        logger.info(
            "Booking validation completed",
            user_id=current_user.id,
            slot_id=request.slot_id,
            duration=request.duration_minutes,
            is_valid=validation_result.is_valid,
            result=validation_result.result.value
        )
        
        return validation_result
        
    except Exception as e:
        logger.error(
            "Error validating booking request",
            user_id=current_user.id,
            slot_id=request.slot_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Booking validation failed: {str(e)}"
        )


@router.get(
    "/duration-system",
    response_model=DurationSystemSummary,
    summary="Get duration system summary",
    description="Returns comprehensive information about the hybrid duration system including all tiers and valid durations."
)
async def get_duration_system_summary(
    current_user: User = Depends(get_current_active_user)
) -> DurationSystemSummary:
    """Get complete duration system information."""
    try:
        summary_data = duration_calculator.get_duration_summary()
        
        return DurationSystemSummary(
            total_valid_durations=summary_data["total_valid_durations"],
            min_duration=summary_data["min_duration"],
            max_duration=summary_data["max_duration"],
            tiers=[
                {
                    "tier": tier["tier"],
                    "description": tier["description"],
                    "min_duration": tier["min_duration"],
                    "max_duration": tier["max_duration"],
                    "increment": tier["increment"],
                    "valid_durations": tier["valid_durations"]
                }
                for tier in summary_data["tiers"]
            ],
            overlapping_durations=summary_data["overlapping_durations"],
            gaps=summary_data["gaps"]
        )
        
    except Exception as e:
        logger.error(
            "Error getting duration system summary",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get duration system summary: {str(e)}"
        )


@router.get(
    "/valid-durations",
    response_model=List[int],
    summary="Get valid durations for range",
    description="Returns all valid durations within a specified range."
)
async def get_valid_durations_for_range(
    min_duration: int = Query(15, ge=1, description="Minimum duration in minutes"),
    max_duration: int = Query(480, le=1440, description="Maximum duration in minutes"),
    current_user: User = Depends(get_current_active_user)
) -> List[int]:
    """Get valid durations within a specified range."""
    try:
        if min_duration >= max_duration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_duration must be less than max_duration"
            )
        
        valid_durations = duration_calculator.get_valid_durations_for_range(
            min_duration, max_duration
        )
        
        logger.debug(
            "Retrieved valid durations for range",
            user_id=current_user.id,
            min_duration=min_duration,
            max_duration=max_duration,
            count=len(valid_durations)
        )
        
        return valid_durations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting valid durations for range",
            user_id=current_user.id,
            min_duration=min_duration,
            max_duration=max_duration,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get valid durations: {str(e)}"
        )


@router.get(
    "/tier/{tier}/durations",
    response_model=List[int],
    summary="Get durations for specific tier",
    description="Returns all valid durations for a specific duration tier."
)
async def get_durations_by_tier(
    tier: DurationTier,
    current_user: User = Depends(get_current_active_user)
) -> List[int]:
    """Get all valid durations for a specific tier."""
    try:
        durations = duration_calculator.get_durations_by_tier(tier)
        
        logger.debug(
            "Retrieved durations for tier",
            user_id=current_user.id,
            tier=tier.value,
            count=len(durations)
        )
        
        return durations
        
    except Exception as e:
        logger.error(
            "Error getting durations for tier",
            user_id=current_user.id,
            tier=tier.value,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get durations for tier {tier.value}: {str(e)}"
        )


@router.post(
    "/validate-timeframe",
    response_model=TimeValidationResponse,
    summary="Validate time frame for booking",
    description="Validates a time frame and returns valid durations that fit within it."
)
async def validate_timeframe(
    request: TimeValidationRequest,
    current_user: User = Depends(get_current_active_user)
) -> TimeValidationResponse:
    """Validate time frame and get valid durations."""
    try:
        if request.start_time >= request.max_end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_time must be before max_end_time"
            )
        
        valid_durations = booking_validator.get_valid_durations_for_timeframe(
            request.start_time, request.max_end_time
        )
        
        # Determine recommended duration
        recommended_duration = None
        if request.preferred_duration:
            # Find closest valid duration to preferred
            closest = min(
                valid_durations,
                key=lambda x: abs(x - request.preferred_duration),
                default=None
            )
            if closest and abs(closest - request.preferred_duration) <= 15:
                recommended_duration = closest
        
        if not recommended_duration and valid_durations:
            # Default to middle duration
            recommended_duration = valid_durations[len(valid_durations) // 2]
        
        # Generate alternative time slots
        alternative_slots = []
        if valid_durations:
            for duration in valid_durations[:3]:  # Top 3 alternatives
                tier = duration_calculator.get_tier_for_duration(duration)
                alternative_slots.append(
                    AlternativeTimeSlot(
                        start_time=request.start_time,
                        end_time=request.start_time + timedelta(minutes=duration),
                        duration_minutes=duration,
                        tier=tier or DurationTier.MICRO,
                        reason=f"Fits within available time window ({tier.value if tier else 'flexible'})"
                    )
                )
        
        warnings = []
        if not valid_durations:
            warnings.append("No valid durations fit within the specified time frame")
        
        return TimeValidationResponse(
            valid_durations=valid_durations,
            recommended_duration=recommended_duration,
            alternative_slots=alternative_slots,
            warnings=warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error validating timeframe",
            user_id=current_user.id,
            start_time=request.start_time.isoformat(),
            max_end_time=request.max_end_time.isoformat(),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeframe validation failed: {str(e)}"
        )


@router.get(
    "/duration/{duration}/info",
    response_model=DurationValidationResponse,
    summary="Get information about specific duration",
    description="Returns detailed information about a specific duration including tier and alternatives."
)
async def get_duration_info(
    duration: int = Path(..., ge=1, le=1440, description="Duration in minutes"),
    current_user: User = Depends(get_current_active_user)
) -> DurationValidationResponse:
    """Get detailed information about a specific duration."""
    try:
        validation_result = duration_calculator.validate_duration(duration)
        
        return DurationValidationResponse(
            is_valid=validation_result.is_valid,
            suggested_duration=validation_result.suggested_duration,
            tier=validation_result.tier,
            increment=validation_result.increment,
            reason=validation_result.reason,
            alternatives=validation_result.alternatives or []
        )
        
    except Exception as e:
        logger.error(
            "Error getting duration info",
            user_id=current_user.id,
            duration=duration,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get duration info: {str(e)}"
        )


@router.get(
    "/next-durations/{current_duration}",
    response_model=List[int],
    summary="Get next available durations",
    description="Returns the next available durations after the current duration."
)
async def get_next_durations(
    current_duration: int = Path(..., ge=1, description="Current duration in minutes"),
    count: int = Query(5, ge=1, le=10, description="Number of next durations to return"),
    current_user: User = Depends(get_current_active_user)
) -> List[int]:
    """Get next available durations after current duration."""
    try:
        next_durations = duration_calculator.get_next_available_durations(
            current_duration, count
        )
        
        logger.debug(
            "Retrieved next durations",
            user_id=current_user.id,
            current_duration=current_duration,
            count=len(next_durations)
        )
        
        return next_durations
        
    except Exception as e:
        logger.error(
            "Error getting next durations",
            user_id=current_user.id,
            current_duration=current_duration,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get next durations: {str(e)}"
        )


@router.get(
    "/buffer-time/{duration}",
    response_model=Dict[str, Any],
    summary="Calculate buffer time for duration",
    description="Returns buffer time calculation for a specific duration across different demand levels."
)
async def get_buffer_time_info(
    duration: int = Path(..., ge=15, le=480, description="Duration in minutes"),
    demand_level: str = Query("medium", description="Demand level (low/medium/high/peak)"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get buffer time information for a duration."""
    try:
        buffer_time = duration_calculator.calculate_buffer_time(duration, demand_level)
        
        # Calculate for all demand levels for comparison
        all_demand_buffers = {}
        for level in ["low", "medium", "high", "peak"]:
            all_demand_buffers[level] = duration_calculator.calculate_buffer_time(duration, level)
        
        tier = duration_calculator.get_tier_for_duration(duration)
        increment = duration_calculator._get_increment_for_duration(duration)
        
        # Calculate example end times
        example_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        booking_end, slot_release, buffer_minutes = duration_calculator.calculate_actual_end_time(
            example_start, duration, demand_level
        )
        
        return {
            "duration_minutes": duration,
            "demand_level": demand_level,
            "buffer_time_minutes": buffer_time,
            "tier": tier.value if tier else "unknown",
            "tier_increment": increment,
            "all_demand_levels": all_demand_buffers,
            "example_timing": {
                "booking_start": example_start.isoformat(),
                "booking_end": booking_end.isoformat(),
                "slot_release": slot_release.isoformat(),
                "buffer_explanation": f"Slot will be available for next booking at {slot_release.strftime('%H:%M')}"
            },
            "buffer_strategy": duration_calculator.settings.buffer_time_strategy,
            "buffer_enabled": duration_calculator.settings.enable_buffer_time
        }
        
    except Exception as e:
        logger.error(
            "Error getting buffer time info",
            user_id=current_user.id,
            duration=duration,
            demand_level=demand_level,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get buffer time info: {str(e)}"
        )
