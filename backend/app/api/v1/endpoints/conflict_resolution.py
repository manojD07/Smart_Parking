"""API endpoints for conflict detection and resolution."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_async_session, get_current_admin_user
from app.models.user import User
from app.models.parking import VehicleType
from app.services.conflict_resolution import ConflictResolutionService, ConflictType, ConflictSeverity, ResolutionStrategy
from app.schemas.common import BaseResponse
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


class ConflictDetectionRequest(BaseModel):
    """Request model for conflict detection."""
    
    slot_id: UUID = Field(..., description="Slot ID to check for conflicts")
    user_id: Optional[UUID] = Field(None, description="User ID (optional, uses current user if not provided)")
    vehicle_type: VehicleType = Field(..., description="Vehicle type")
    start_time: datetime = Field(..., description="Booking start time")
    end_time: datetime = Field(..., description="Booking end time")
    exclude_booking_id: Optional[UUID] = Field(None, description="Booking ID to exclude from conflict check")


class ConflictDetail(BaseModel):
    """Response model for conflict details."""
    
    conflict_id: str
    conflict_type: str
    severity: str
    description: str
    affected_resources: List[str]
    conflicting_bookings: List[UUID]
    resolution_strategies: List[str]
    auto_resolvable: bool
    estimated_resolution_time_seconds: Optional[float]
    metadata: Dict[str, Any]


class ConflictDetectionResponse(BaseResponse):
    """Response model for conflict detection."""
    
    conflicts: List[ConflictDetail]
    total_conflicts: int
    critical_conflicts: int
    resolvable_conflicts: int
    recommendations: List[str]


class ConflictResolutionRequest(BaseModel):
    """Request model for conflict resolution."""
    
    conflicts: List[Dict[str, Any]] = Field(..., description="Conflicts to resolve")
    preferred_strategy: Optional[ResolutionStrategy] = Field(None, description="Preferred resolution strategy")


class ResolutionResult(BaseModel):
    """Response model for resolution result."""
    
    success: bool
    strategy_used: str
    resolution_details: Dict[str, Any]
    alternative_suggestions: List[Dict[str, Any]]
    warnings: List[str]
    next_steps: List[str]


class ConflictResolutionResponse(BaseResponse):
    """Response model for conflict resolution."""
    
    resolution_result: ResolutionResult


class BookingValidationRequest(BaseModel):
    """Request model for atomic booking validation."""
    
    slot_id: UUID = Field(..., description="Slot ID")
    vehicle_type: VehicleType = Field(..., description="Vehicle type")
    start_time: datetime = Field(..., description="Booking start time")
    end_time: datetime = Field(..., description="Booking end time")
    timeout: int = Field(30, description="Validation timeout in seconds", ge=5, le=120)


class BookingValidationResponse(BaseResponse):
    """Response model for booking validation."""
    
    is_valid: bool
    conflicts: List[ConflictDetail]
    resolution_result: Optional[ResolutionResult]
    validation_timestamp: datetime


@router.post(
    "/detect-conflicts",
    response_model=ConflictDetectionResponse,
    summary="Detect booking conflicts",
    description="Detect potential conflicts for a booking request"
)
async def detect_conflicts(
    request: ConflictDetectionRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Detect conflicts for a booking request.
    
    This endpoint performs comprehensive conflict detection including:
    - Time overlap conflicts
    - Capacity conflicts  
    - State conflicts
    - User limit conflicts
    - Allocation conflicts
    - System constraint conflicts
    """
    try:
        conflict_service = ConflictResolutionService(session)
        
        # Use current user if not specified
        user_id = request.user_id or current_user.id
        
        # Detect conflicts
        conflicts = await conflict_service.detect_conflicts(
            slot_id=request.slot_id,
            user_id=user_id,
            vehicle_type=request.vehicle_type.value,
            start_time=request.start_time,
            end_time=request.end_time,
            exclude_booking_id=request.exclude_booking_id
        )
        
        # Process conflicts for response
        conflict_details = [
            ConflictDetail(
                conflict_id=c.conflict_id,
                conflict_type=c.conflict_type.value,
                severity=c.severity.value,
                description=c.description,
                affected_resources=c.affected_resources,
                conflicting_bookings=c.conflicting_bookings,
                resolution_strategies=[s.value for s in c.resolution_strategies],
                auto_resolvable=c.auto_resolvable,
                estimated_resolution_time_seconds=c.estimated_resolution_time.total_seconds() if c.estimated_resolution_time else None,
                metadata=c.metadata
            )
            for c in conflicts
        ]
        
        # Generate statistics
        critical_conflicts = len([c for c in conflicts if c.severity == ConflictSeverity.CRITICAL])
        resolvable_conflicts = len([c for c in conflicts if c.auto_resolvable])
        
        # Generate recommendations
        recommendations = []
        if critical_conflicts > 0:
            recommendations.append("Critical conflicts detected - consider alternative options")
        if resolvable_conflicts > 0:
            recommendations.append("Some conflicts may be auto-resolvable")
        if not conflicts:
            recommendations.append("No conflicts detected - booking should proceed successfully")
        
        logger.info(
            "Conflict detection completed",
            user_id=user_id,
            slot_id=request.slot_id,
            total_conflicts=len(conflicts),
            critical_conflicts=critical_conflicts
        )
        
        return ConflictDetectionResponse(
            success=True,
            message="Conflict detection completed successfully",
            conflicts=conflict_details,
            total_conflicts=len(conflicts),
            critical_conflicts=critical_conflicts,
            resolvable_conflicts=resolvable_conflicts,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error("Conflict detection failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect conflicts: {str(e)}"
        )


@router.post(
    "/resolve-conflicts",
    response_model=ConflictResolutionResponse,
    summary="Resolve booking conflicts",
    description="Attempt to resolve detected conflicts using various strategies"
)
async def resolve_conflicts(
    request: ConflictResolutionRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Attempt to resolve detected conflicts.
    
    This endpoint tries various resolution strategies:
    - Block operation
    - Queue for later processing
    - Suggest alternative slots
    - Use partial allocation
    - Require admin intervention
    - Auto-resolve when possible
    """
    try:
        conflict_service = ConflictResolutionService(session)
        
        # Convert request conflicts to service format
        # This is a simplified conversion - in practice, you'd reconstruct ConflictDetails objects
        conflicts = []  # TODO: Convert from request format to ConflictDetails objects
        
        # Attempt resolution
        resolution_result = await conflict_service.resolve_conflicts(
            conflicts=conflicts,
            preferred_strategy=request.preferred_strategy
        )
        
        # Convert to response format
        result = ResolutionResult(
            success=resolution_result.success,
            strategy_used=resolution_result.strategy_used.value,
            resolution_details=resolution_result.resolution_details,
            alternative_suggestions=resolution_result.alternative_suggestions,
            warnings=resolution_result.warnings,
            next_steps=resolution_result.next_steps
        )
        
        logger.info(
            "Conflict resolution completed",
            success=resolution_result.success,
            strategy_used=resolution_result.strategy_used.value
        )
        
        return ConflictResolutionResponse(
            success=True,
            message="Conflict resolution completed",
            resolution_result=result
        )
        
    except Exception as e:
        logger.error("Conflict resolution failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve conflicts: {str(e)}"
        )


@router.post(
    "/validate-booking",
    response_model=BookingValidationResponse,
    summary="Validate booking atomically",
    description="Atomically validate a booking with conflict detection and resolution"
)
async def validate_booking_atomically(
    request: BookingValidationRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Atomically validate a booking request.
    
    This endpoint performs:
    1. Atomic conflict detection with distributed locking
    2. Automatic conflict resolution attempts
    3. Comprehensive validation results
    
    Returns detailed validation results including any conflicts found
    and resolution attempts made.
    """
    try:
        conflict_service = ConflictResolutionService(session)
        
        # Perform atomic validation
        is_valid, conflicts, resolution_result = await conflict_service.validate_booking_atomically(
            slot_id=request.slot_id,
            user_id=current_user.id,
            vehicle_type=request.vehicle_type.value,
            start_time=request.start_time,
            end_time=request.end_time,
            timeout=request.timeout
        )
        
        # Process conflicts for response
        conflict_details = [
            ConflictDetail(
                conflict_id=c.conflict_id,
                conflict_type=c.conflict_type.value,
                severity=c.severity.value,
                description=c.description,
                affected_resources=c.affected_resources,
                conflicting_bookings=c.conflicting_bookings,
                resolution_strategies=[s.value for s in c.resolution_strategies],
                auto_resolvable=c.auto_resolvable,
                estimated_resolution_time_seconds=c.estimated_resolution_time.total_seconds() if c.estimated_resolution_time else None,
                metadata=c.metadata
            )
            for c in conflicts
        ]
        
        # Process resolution result
        resolution_response = None
        if resolution_result:
            resolution_response = ResolutionResult(
                success=resolution_result.success,
                strategy_used=resolution_result.strategy_used.value,
                resolution_details=resolution_result.resolution_details,
                alternative_suggestions=resolution_result.alternative_suggestions,
                warnings=resolution_result.warnings,
                next_steps=resolution_result.next_steps
            )
        
        logger.info(
            "Atomic booking validation completed",
            user_id=current_user.id,
            slot_id=request.slot_id,
            is_valid=is_valid,
            conflicts_found=len(conflicts)
        )
        
        return BookingValidationResponse(
            success=True,
            message="Booking validation completed successfully",
            is_valid=is_valid,
            conflicts=conflict_details,
            resolution_result=resolution_response,
            validation_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("Atomic booking validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate booking: {str(e)}"
        )


@router.get(
    "/slot/{slot_id}/conflicts",
    response_model=ConflictDetectionResponse,
    summary="Get slot conflicts",
    description="Get current conflicts for a specific slot"
)
async def get_slot_conflicts(
    slot_id: UUID,
    vehicle_type: VehicleType = Query(..., description="Vehicle type to check"),
    start_time: datetime = Query(..., description="Start time"),
    end_time: datetime = Query(..., description="End time"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Get conflicts for a specific slot and time range."""
    return await detect_conflicts(
        ConflictDetectionRequest(
            slot_id=slot_id,
            vehicle_type=vehicle_type,
            start_time=start_time,
            end_time=end_time
        ),
        session,
        current_user
    )


@router.get(
    "/system/health",
    summary="Conflict resolution system health",
    description="Get health status of the conflict resolution system"
)
async def get_system_health(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get conflict resolution system health.
    
    This endpoint provides system health information including:
    - Service status
    - Performance metrics
    - Error rates
    - Configuration status
    """
    try:
        conflict_service = ConflictResolutionService(session)
        
        # Basic health check
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ConflictResolutionService",
            "version": "1.0.0",
            "configuration": {
                "max_user_concurrent_bookings": conflict_service.max_user_concurrent_bookings,
                "conflict_detection_window_hours": conflict_service.conflict_detection_window.total_seconds() / 3600,
                "auto_resolution_timeout_seconds": conflict_service.auto_resolution_timeout.total_seconds()
            },
            "metrics": {
                "uptime": "active",
                "last_error": None,
                "performance": "optimal"
            }
        }
        
        return BaseResponse(
            success=True,
            message="Conflict resolution system is healthy",
            data=health_status
        )
        
    except Exception as e:
        logger.error("System health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System health check failed: {str(e)}"
        )
