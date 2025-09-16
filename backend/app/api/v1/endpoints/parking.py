"""Parking lot and slot management endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.parking import ParkingService
from app.schemas.parking import (
    ParkingLotCreate,
    ParkingLotUpdate,
    ParkingLotResponse,
    ParkingSlotResponse,
    AvailabilityRequest,
    AvailabilityResponse,
    LocationSearchRequest
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.api.deps import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.models.parking import VehicleType
from app.core.exceptions import create_http_exception, BaseApplicationError

router = APIRouter()


@router.get("/lots", response_model=List[ParkingLotResponse])
async def get_parking_lots(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all parking lots."""
    try:
        parking_service = ParkingService(session)
        
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        
        lots = await parking_service.get_multi(
            skip=skip,
            limit=limit,
            **filters
        )
        
        return [ParkingLotResponse.from_orm(lot) for lot in lots]
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/lots/{lot_id}", response_model=ParkingLotResponse)
async def get_parking_lot(
    lot_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get parking lot by ID."""
    try:
        parking_service = ParkingService(session)
        lot = await parking_service.get_by_id(lot_id, load_relationships=True)
        
        return ParkingLotResponse.from_orm(lot)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/lots/{lot_id}/availability", response_model=AvailabilityResponse)
async def get_lot_availability(
    lot_id: UUID,
    vehicle_type: str = Query(..., description="Vehicle type (car/bike)"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get real-time availability for a parking lot."""
    try:
        from datetime import datetime, timedelta
        
        parking_service = ParkingService(session)
        
        # Default to next hour if no time specified
        if not start_time:
            start_dt = datetime.utcnow()
        else:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        if not end_time:
            end_dt = start_dt + timedelta(hours=1)
        else:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        availability = await parking_service.get_lot_availability(
            lot_id=lot_id,
            vehicle_type=VehicleType(vehicle_type),
            start_time=start_dt,
            end_time=end_dt
        )
        
        return AvailabilityResponse(**availability)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/lots/{lot_id}/slots", response_model=List[ParkingSlotResponse])
async def get_lot_slots(
    lot_id: UUID,
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    status: Optional[str] = Query(None, description="Filter by slot status"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Number of items to return"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get slots for a parking lot."""
    try:
        parking_service = ParkingService(session)
        
        filters = {"lot_id": lot_id}
        if vehicle_type:
            filters["slot_type"] = vehicle_type
        if status:
            filters["status"] = status
        
        slots = await parking_service.get_lot_slots(
            lot_id=lot_id,
            skip=skip,
            limit=limit,
            **filters
        )
        
        return [ParkingSlotResponse.from_orm(slot) for slot in slots]
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/search", response_model=List[ParkingLotResponse])
async def search_parking_lots(
    search_request: LocationSearchRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Search parking lots by location."""
    try:
        parking_service = ParkingService(session)
        
        lots = await parking_service.search_lots_near_location(
            latitude=search_request.latitude,
            longitude=search_request.longitude,
            radius_km=search_request.radius_km,
            skip=search_request.skip,
            limit=search_request.limit
        )
        
        return [ParkingLotResponse.from_orm(lot) for lot in lots]
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/lots/{lot_id}/availability", response_model=AvailabilityResponse)
async def check_availability(
    lot_id: UUID,
    availability_request: AvailabilityRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Check availability for specific time and vehicle type."""
    try:
        parking_service = ParkingService(session)
        
        availability = await parking_service.get_lot_availability(
            lot_id=lot_id,
            vehicle_type=VehicleType(availability_request.vehicle_type),
            start_time=availability_request.start_time,
            end_time=availability_request.end_time
        )
        
        return AvailabilityResponse(**availability)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


# Admin endpoints
@router.post("/admin/lots", response_model=ParkingLotResponse, status_code=status.HTTP_201_CREATED)
async def create_parking_lot(
    lot_data: ParkingLotCreate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new parking lot (admin only)."""
    try:
        parking_service = ParkingService(session)
        
        lot = await parking_service.create_parking_lot(
            name=lot_data.name,
            address=lot_data.address,
            latitude=lot_data.latitude,
            longitude=lot_data.longitude,
            total_car_slots=lot_data.total_car_slots,
            total_bike_slots=lot_data.total_bike_slots,
            hourly_rate_car=lot_data.hourly_rate_car,
            hourly_rate_bike=lot_data.hourly_rate_bike
        )
        
        return ParkingLotResponse.from_orm(lot)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.put("/admin/lots/{lot_id}", response_model=ParkingLotResponse)
async def update_parking_lot(
    lot_id: UUID,
    lot_data: ParkingLotUpdate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update parking lot (admin only)."""
    try:
        parking_service = ParkingService(session)
        
        update_data = lot_data.dict(exclude_unset=True)
        lot = await parking_service.update(lot_id, **update_data)
        
        return ParkingLotResponse.from_orm(lot)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.delete("/admin/lots/{lot_id}", response_model=SuccessResponse)
async def delete_parking_lot(
    lot_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete parking lot (admin only)."""
    try:
        parking_service = ParkingService(session)
        
        success = await parking_service.delete(lot_id)
        
        if success:
            return SuccessResponse(message="Parking lot deleted successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete parking lot"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/admin/lots/{lot_id}/statistics")
async def get_lot_statistics(
    lot_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get parking lot statistics (admin only)."""
    try:
        parking_service = ParkingService(session)
        
        statistics = await parking_service.get_lot_statistics(lot_id)
        
        return statistics
        
    except BaseApplicationError as e:
        raise create_http_exception(e)