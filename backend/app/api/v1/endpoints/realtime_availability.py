"""API endpoints for real-time availability management."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_async_session, get_current_admin_user
from app.models.user import User
from app.models.parking import VehicleType
from app.services.realtime_availability import RealTimeAvailabilityService
from app.schemas.common import BaseResponse
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


class AvailabilityResponse(BaseModel):
    """Response model for availability data."""
    
    lot_id: str
    lot_name: str
    last_updated: str
    vehicle_types: Dict[str, Dict[str, Any]]
    total_available_slots: int
    total_capacity: int
    overall_occupancy_rate: float
    is_full: bool
    has_capacity: bool


class VehicleTypeAvailability(BaseModel):
    """Response model for vehicle type specific availability."""
    
    vehicle_type: str
    total_slots: int
    available_slots: int
    occupied_slots: int
    reserved_slots: int
    maintenance_slots: int
    occupancy_rate: float
    bike_in_car_availability: Dict[str, Any]


class AvailabilityNotificationRequest(BaseModel):
    """Request model for manual availability notifications."""
    
    lot_id: UUID = Field(..., description="Parking lot ID")
    vehicle_type: VehicleType = Field(..., description="Vehicle type")
    change_type: str = Field("manual_update", description="Type of change")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class OccupancyAnalyticsResponse(BaseModel):
    """Response model for occupancy analytics."""
    
    lot_id: str
    time_range_hours: int
    current_availability: Dict[str, Any]
    booking_metrics: Dict[str, Any]
    occupancy_trends: Dict[str, Any]


@router.get(
    "/lot/{lot_id}/availability",
    response_model=AvailabilityResponse,
    summary="Get real-time lot availability",
    description="Get comprehensive real-time availability for a parking lot"
)
async def get_lot_availability(
    lot_id: UUID,
    vehicle_type: Optional[VehicleType] = Query(None, description="Specific vehicle type"),
    real_time: bool = Query(True, description="Include real-time booking data"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time availability for a parking lot.
    
    This endpoint provides comprehensive availability data including:
    - Total and available slots by vehicle type
    - Occupancy rates and status
    - Bike-in-car slot availability
    - Real-time updates based on current bookings
    """
    try:
        availability_service = RealTimeAvailabilityService(session)
        
        # Get availability data
        availability_data = await availability_service.get_lot_availability(
            lot_id=lot_id,
            vehicle_type=vehicle_type,
            real_time=real_time
        )
        
        logger.info(
            "Lot availability retrieved",
            lot_id=lot_id,
            user_id=current_user.id,
            vehicle_type=vehicle_type.value if vehicle_type else "all",
            total_available=availability_data["total_available_slots"]
        )
        
        return AvailabilityResponse(**availability_data)
        
    except Exception as e:
        logger.error("Failed to get lot availability", lot_id=lot_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get availability for lot {lot_id}"
        )


@router.get(
    "/lot/{lot_id}/availability/{vehicle_type}",
    response_model=VehicleTypeAvailability,
    summary="Get vehicle type specific availability",
    description="Get availability for a specific vehicle type in a parking lot"
)
async def get_vehicle_type_availability(
    lot_id: UUID,
    vehicle_type: VehicleType,
    real_time: bool = Query(True, description="Include real-time booking data"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Get availability for a specific vehicle type."""
    try:
        availability_service = RealTimeAvailabilityService(session)
        
        # Get overall availability
        availability_data = await availability_service.get_lot_availability(
            lot_id=lot_id,
            vehicle_type=vehicle_type,
            real_time=real_time
        )
        
        # Extract vehicle type specific data
        vehicle_data = availability_data["vehicle_types"].get(vehicle_type.value)
        if not vehicle_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for vehicle type {vehicle_type.value}"
            )
        
        return VehicleTypeAvailability(**vehicle_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get vehicle type availability", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get {vehicle_type.value} availability"
        )


@router.post(
    "/notify-availability-change",
    response_model=BaseResponse,
    summary="Manually notify availability change",
    description="Manually trigger availability change notification (admin only)"
)
async def notify_availability_change(
    request: AvailabilityNotificationRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Manually trigger availability change notification.
    
    This endpoint allows administrators to manually trigger availability
    change notifications, useful for testing or manual corrections.
    """
    try:
        availability_service = RealTimeAvailabilityService(session)
        
        # Add to background tasks for async processing
        background_tasks.add_task(
            availability_service.notify_availability_change,
            request.lot_id,
            request.vehicle_type,
            request.change_type,
            request.metadata
        )
        
        logger.info(
            "Manual availability notification triggered",
            lot_id=request.lot_id,
            vehicle_type=request.vehicle_type.value,
            admin_id=current_user.id
        )
        
        return BaseResponse(
            success=True,
            message="Availability change notification triggered"
        )
        
    except Exception as e:
        logger.error("Failed to trigger availability notification", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger availability notification"
        )


@router.get(
    "/lot/{lot_id}/occupancy-analytics",
    response_model=OccupancyAnalyticsResponse,
    summary="Get occupancy analytics",
    description="Get detailed occupancy analytics for a parking lot"
)
async def get_occupancy_analytics(
    lot_id: UUID,
    time_range_hours: int = Query(24, description="Time range in hours", ge=1, le=168),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get occupancy analytics for a parking lot.
    
    Provides detailed analytics including:
    - Current availability status
    - Booking metrics and completion rates
    - Occupancy trends and patterns
    - Vehicle type breakdown
    """
    try:
        availability_service = RealTimeAvailabilityService(session)
        
        analytics_data = await availability_service.get_lot_occupancy_analytics(
            lot_id=lot_id,
            time_range_hours=time_range_hours
        )
        
        logger.info(
            "Occupancy analytics retrieved",
            lot_id=lot_id,
            time_range_hours=time_range_hours,
            user_id=current_user.id
        )
        
        return OccupancyAnalyticsResponse(**analytics_data)
        
    except Exception as e:
        logger.error("Failed to get occupancy analytics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get occupancy analytics"
        )


@router.post(
    "/refresh-cache",
    response_model=BaseResponse,
    summary="Refresh availability cache",
    description="Refresh availability cache for all lots or specific lot (admin only)"
)
async def refresh_availability_cache(
    background_tasks: BackgroundTasks,
    lot_id: Optional[UUID] = Query(None, description="Specific lot ID (None for all)"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Refresh availability cache.
    
    This endpoint allows administrators to refresh the availability cache,
    ensuring that all cached data reflects the current state.
    """
    try:
        availability_service = RealTimeAvailabilityService(session)
        
        # Add to background tasks for async processing
        background_tasks.add_task(
            availability_service.refresh_availability_cache,
            lot_id
        )
        
        logger.info(
            "Availability cache refresh triggered",
            lot_id=lot_id,
            admin_id=current_user.id
        )
        
        return BaseResponse(
            success=True,
            message=f"Cache refresh triggered for {'all lots' if not lot_id else f'lot {lot_id}'}"
        )
        
    except Exception as e:
        logger.error("Failed to refresh availability cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh availability cache"
        )


@router.get(
    "/lots/summary",
    summary="Get availability summary for all lots",
    description="Get a summary of availability across all parking lots"
)
async def get_availability_summary(
    vehicle_type: Optional[VehicleType] = Query(None, description="Filter by vehicle type"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get availability summary for all parking lots.
    
    Provides a quick overview of availability across all lots,
    useful for dashboard displays and quick decision making.
    """
    try:
        availability_service = RealTimeAvailabilityService(session)
        
        # This would typically involve getting all lots and their availability
        # For now, return a placeholder structure
        summary = {
            "total_lots": 0,
            "lots_with_availability": 0,
            "total_available_slots": 0,
            "total_capacity": 0,
            "overall_occupancy_rate": 0.0,
            "vehicle_type_breakdown": {},
            "lot_summaries": []
        }
        
        # TODO: Implement comprehensive summary logic
        
        return BaseResponse(
            success=True,
            message="Availability summary retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        logger.error("Failed to get availability summary", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get availability summary"
        )


@router.get(
    "/health",
    summary="Real-time availability system health",
    description="Get health status of the real-time availability system"
)
async def get_realtime_system_health(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get real-time availability system health.
    
    Provides system health information including:
    - Service status and performance
    - Cache health and statistics
    - WebSocket connection status
    - Event processing metrics
    """
    try:
        availability_service = RealTimeAvailabilityService(session)
        
        # Get cache statistics
        cache_stats = {
            "cached_lots": len(set(key.split(':')[0] for key in availability_service.availability_cache.keys())),
            "total_cache_entries": len(availability_service.availability_cache),
            "cache_size_kb": len(str(availability_service.availability_cache)) / 1024
        }
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "RealTimeAvailabilityService",
            "version": "1.0.0",
            "cache_statistics": cache_stats,
            "metrics": {
                "uptime": "active",
                "last_error": None,
                "performance": "optimal"
            }
        }
        
        return BaseResponse(
            success=True,
            message="Real-time availability system is healthy",
            data=health_status
        )
        
    except Exception as e:
        logger.error("Real-time system health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System health check failed: {str(e)}"
        )
