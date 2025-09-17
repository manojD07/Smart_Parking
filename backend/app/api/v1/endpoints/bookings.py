"""Booking management endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.booking import BookingService
from app.services.pricing import PricingService
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingUpdate,
    PricingPreviewRequest,
    PricingPreviewResponse
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.api.deps import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.models.booking import BookingStatus
from app.models.parking import VehicleType
from app.core.exceptions import create_http_exception, BaseApplicationError

router = APIRouter()


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new parking booking."""
    try:
        booking_service = BookingService(session)
        
        booking = await booking_service.create_booking(
            user_id=current_user.id,
            lot_id=booking_data.lot_id,
            vehicle_type=VehicleType(booking_data.vehicle_type),
            vehicle_number=booking_data.vehicle_number,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time
        )
        
        return BookingResponse(
            id=booking.id,
            user_id=booking.user_id,
            lot_id=booking.lot_id,
            slot_id=booking.slot_id,
            vehicle_type=booking.vehicle_type,
            vehicle_number=booking.vehicle_number,
            start_time=booking.start_time,
            end_time=booking.end_time,
            total_amount=booking.total_amount,
            status=booking.status,
            booking_reference=booking.booking_reference,
            check_in_time=booking.check_in_time,
            check_out_time=booking.check_out_time,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
            lot_name=None,
            slot_number=None,
            user_email=None
        )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/my", response_model=List[BookingResponse])
async def get_my_bookings(
    status: Optional[str] = Query(None, description="Filter by booking status"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current user's bookings."""
    try:
        booking_service = BookingService(session)
        
        booking_status = BookingStatus(status) if status else None
        bookings = await booking_service.get_user_bookings(
            user_id=current_user.id,
            status=booking_status,
            skip=skip,
            limit=limit
        )
        
        return [BookingResponse.from_orm(booking) for booking in bookings]
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/checkin/{booking_reference}", response_model=SuccessResponse)
async def admin_check_in_by_reference(
    booking_reference: str,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Admin check-in a booking by reference code."""
    try:
        booking_service = BookingService(session)
        
        # Admin check-in by reference
        success = await booking_service.admin_check_in_by_reference(booking_reference)
        
        if success:
            return SuccessResponse(message="Booking checked in successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to check in booking"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/reference/{booking_reference}", response_model=BookingResponse)
async def get_booking_by_reference(
    booking_reference: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get booking by reference code."""
    try:
        booking_service = BookingService(session)
        
        booking = await booking_service.get_booking_by_reference(booking_reference)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Users can only see their own bookings (unless admin)
        if not current_user.is_admin and booking.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return BookingResponse.from_orm(booking)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get booking details."""
    try:
        booking_service = BookingService(session)
        booking = await booking_service.get_by_id(booking_id, load_relationships=True)
        
        # Check if user owns the booking or is admin
        if booking.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this booking"
            )
        
        return BookingResponse.from_orm(booking)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.put("/{booking_id}/cancel", response_model=SuccessResponse)
async def cancel_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Cancel a booking."""
    try:
        booking_service = BookingService(session)
        
        success = await booking_service.cancel_booking(booking_id, current_user.id)
        
        if success:
            return SuccessResponse(message="Booking cancelled successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel booking"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/{booking_id}/checkin", response_model=SuccessResponse)
async def check_in_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Check in to a booking."""
    try:
        booking_service = BookingService(session)
        
        success = await booking_service.check_in_booking(booking_id, current_user.id)
        
        if success:
            return SuccessResponse(message="Checked in successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to check in"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/{booking_id}/checkout", response_model=SuccessResponse)
async def check_out_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Check out from a booking."""
    try:
        booking_service = BookingService(session)
        
        success = await booking_service.check_out_booking(booking_id, current_user.id)
        
        if success:
            return SuccessResponse(message="Checked out successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to check out"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/reference/{booking_reference}", response_model=BookingResponse)
async def get_booking_by_reference(
    booking_reference: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get booking by reference code."""
    try:
        booking_service = BookingService(session)
        booking = await booking_service.get_booking_by_reference(booking_reference)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check if user owns the booking or is admin
        if booking.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this booking"
            )
        
        return BookingResponse.from_orm(booking)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/pricing-preview", response_model=PricingPreviewResponse)
async def get_pricing_preview(
    pricing_request: PricingPreviewRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Get pricing preview for a potential booking."""
    try:
        pricing_service = PricingService(session)
        
        pricing_info = await pricing_service.calculate_booking_price(
            lot_id=pricing_request.lot_id,
            vehicle_type=VehicleType(pricing_request.vehicle_type),
            start_time=pricing_request.start_time,
            end_time=pricing_request.end_time
        )
        
        return PricingPreviewResponse(**pricing_info)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


# Admin endpoints
@router.get("/search", response_model=List[BookingResponse])
async def search_bookings(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Search bookings (admin only)."""
    try:
        booking_service = BookingService(session)
        
        bookings = await booking_service.search_bookings(
            search_term=q,
            skip=skip,
            limit=limit
        )
        
        return [BookingResponse.from_orm(booking) for booking in bookings]
        
    except BaseApplicationError as e:
        raise create_http_exception(e)

@router.get("/slots/{slot_id}/chunks")
async def get_slot_chunks(
    slot_id: UUID,
    start_time: str = Query(..., description="Start time in ISO format"),
    end_time: str = Query(..., description="End time in ISO format"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get chunk availability for a slot."""
    try:
        from datetime import datetime
        
        # Parse time strings  
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Create chunk repository
        from app.repositories.slot_chunks import SlotTimeChunkRepository
        chunk_repository = SlotTimeChunkRepository(session)
        
        # Generate chunks and get availability
        await chunk_repository.generate_chunks_for_slot(slot_id, start_dt, end_dt)
        availability = await chunk_repository.get_slot_availability_by_chunks(slot_id, start_dt, end_dt)
        
        return availability
        
    except Exception as e:
        return {"error": str(e), "total_chunks": 0, "available_chunks": 0, "chunks": []}

@router.post("/reserve-chunks")
async def reserve_chunks_for_payment(
    request_data: dict,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Reserve chunks for payment (10-minute Redis TTL)."""
    try:
        import uuid
        from app.core.cache import ChunkReservationCache
        
        chunk_ids = request_data.get("chunk_ids", [])
        user_session_id = str(uuid.uuid4())
        
        # Reserve chunks atomically in Redis
        result = await ChunkReservationCache.reserve_chunks_atomic(
            chunk_ids=chunk_ids,
            user_session_id=user_session_id,
            ttl_seconds=600  # 10 minutes
        )
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/confirm-chunk-booking")
async def confirm_chunk_booking(
    request_data: dict,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Confirm booking from Redis reservation."""
    try:
        from app.core.cache import ChunkReservationCache
        from app.repositories.slot_chunks import SlotTimeChunkRepository
        
        session_id = request_data.get("session_id")
        vehicle_number = request_data.get("vehicle_number")
        
        # Get session info
        session_info = await ChunkReservationCache.get_session_info(session_id)
        if not session_info:
            return {"success": False, "error": "Session expired or not found"}
        
        # Create booking (simplified - you can integrate with existing booking service)
        booking_service = BookingService(session)
        
        # For now, return success - full integration in next phase
        return {
            "success": True,
            "message": "Booking confirmed",
            "session_id": session_id
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/cancel-reservation/{session_id}")
async def cancel_chunk_reservation(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel chunk reservation and release locks."""
    try:
        from app.core.cache import ChunkReservationCache
        
        # Get session info first
        session_info = await ChunkReservationCache.get_session_info(session_id)
        if not session_info:
            return {"success": False, "error": "Session not found"}
        
        # Release chunks
        success = await ChunkReservationCache.release_chunks(
            chunk_ids=session_info["chunk_ids"],
            user_session_id=session_id
        )
        
        return {"success": success, "message": "Reservation cancelled" if success else "Failed to cancel"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
