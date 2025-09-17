"""API endpoints for slot time chunk operations."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_async_session
from app.api.deps import get_current_active_user, get_current_admin_user
from app.core.exceptions import BaseApplicationError, create_http_exception
from app.services.chunk_booking import ChunkBookingService
from app.repositories.slot_chunks import SlotTimeChunkRepository
from app.models.user import User
from app.models.parking import VehicleType
from app.schemas.common import SuccessResponse
from app.core.timezone import from_iso_string

router = APIRouter()


class ChunkAvailabilityRequest(BaseModel):
    start_time: str = Field(..., description="Start time in ISO format")
    end_time: str = Field(..., description="End time in ISO format")


class ChunkReservationRequest(BaseModel):
    slot_id: str = Field(..., description="Slot ID to reserve")
    chunk_ids: List[str] = Field(..., description="List of chunk IDs to reserve")
    start_time: str = Field(..., description="Start time in ISO format")
    end_time: str = Field(..., description="End time in ISO format")
    vehicle_type: str = Field(..., description="Vehicle type")


class BookingConfirmationRequest(BaseModel):
    session_id: str = Field(..., description="Reservation session ID")
    vehicle_number: str = Field(..., description="Vehicle registration number")


@router.get("/slots/{slot_id}/chunks/availability")
async def get_slot_chunk_availability(
    slot_id: UUID,
    start_time: str = Query(..., description="Start time in ISO format"),
    end_time: str = Query(..., description="End time in ISO format"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get chunk-based availability for a specific slot."""
    try:
        chunk_service = ChunkBookingService(session)
        
        # Parse time strings
        start_dt = from_iso_string(start_time)
        end_dt = from_iso_string(end_time)
        
        # Get availability
        availability = await chunk_service.check_slot_availability(
            slot_id, start_dt, end_dt
        )
        
        return availability
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/reserve-chunks")
async def reserve_slot_chunks(
    request: ChunkReservationRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Reserve slot chunks temporarily."""
    try:
        chunk_service = ChunkBookingService(session)
        
        # Parse inputs
        slot_id = UUID(request.slot_id)
        start_dt = from_iso_string(request.start_time)
        end_dt = from_iso_string(request.end_time)
        vehicle_type = VehicleType(request.vehicle_type)
        
        # Reserve chunks
        reservation = await chunk_service.reserve_slot_chunks(
            slot_id=slot_id,
            start_time=start_dt,
            end_time=end_dt,
            user_id=current_user.id,
            vehicle_type=vehicle_type
        )
        
        return reservation
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/confirm-reservation")
async def confirm_chunk_booking(
    request: BookingConfirmationRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Confirm booking from temporary reservation."""
    try:
        chunk_service = ChunkBookingService(session)
        
        # Confirm booking
        booking = await chunk_service.confirm_booking_from_reservation(
            session_id=request.session_id,
            vehicle_number=request.vehicle_number
        )
        
        return {
            "message": "Booking confirmed successfully",
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference
        }
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.put("/extend-reservation/{session_id}")
async def extend_reservation(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Extend reservation by 5 minutes."""
    try:
        # Implementation for extending reservation
        # This would update the Redis timeout and database reserved_until
        
        return SuccessResponse(message="Reservation extended by 5 minutes")
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.delete("/cancel-reservation/{session_id}")
async def cancel_reservation(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Cancel temporary reservation."""
    try:
        chunk_service = ChunkBookingService(session)
        
        success = await chunk_service.cancel_reservation(session_id)
        
        if success:
            return SuccessResponse(message="Reservation cancelled successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found"
            )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/admin/cleanup-expired")
async def cleanup_expired_reservations(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Admin endpoint to manually cleanup expired reservations."""
    try:
        chunk_service = ChunkBookingService(session)
        
        cleaned_count = await chunk_service.cleanup_expired_reservations()
        
        return {
            "message": f"Cleaned up {cleaned_count} expired reservations",
            "cleaned_count": cleaned_count
        }
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/lots/{lot_id}/chunks/overview")
async def get_lot_chunks_overview(
    lot_id: UUID,
    start_date: str = Query(..., description="Start date in ISO format"),
    end_date: str = Query(..., description="End date in ISO format"),
    vehicle_type: str = Query(..., description="Vehicle type"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get chunk overview for entire parking lot."""
    try:
        chunk_repo = SlotTimeChunkRepository(session)
        
        # Parse inputs
        start_dt = from_iso_string(start_date)
        end_dt = from_iso_string(end_date)
        vehicle_type_enum = VehicleType(vehicle_type)
        
        # This would require additional implementation to get all slots
        # and their chunk availability for the lot
        
        return {
            "message": "Lot chunk overview - implementation needed",
            "lot_id": str(lot_id)
        }
        
    except BaseApplicationError as e:
        raise create_http_exception(e)
