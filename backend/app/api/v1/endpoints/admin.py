"""Admin management endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.booking import BookingService
from app.services.parking import ParkingService
from app.services.user import UserService
from app.schemas.common import SuccessResponse
from app.schemas.booking import BookingResponse
from app.models.booking import BookingStatus
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.core.exceptions import create_http_exception, BaseApplicationError

router = APIRouter()


@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get admin dashboard overview."""
    try:
        user_service = UserService(session)
        booking_service = BookingService(session)
        parking_service = ParkingService(session)
        
        # Get basic statistics
        total_users = await user_service.count(is_active=True)
        total_lots = await parking_service.count(is_active=True)
        
        # Get today's bookings
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_stats = await booking_service.get_booking_statistics(
            start_date=today_start,
            end_date=today_end
        )
        
        return {
            "overview": {
                "total_users": total_users,
                "total_parking_lots": total_lots,
                "today_bookings": today_stats.get("total_bookings", 0),
                "today_revenue": float(today_stats.get("total_revenue", 0))
            },
            "today_statistics": today_stats
        }
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/bookings", response_model=List[BookingResponse])
async def get_all_bookings(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    status: Optional[str] = Query(None, description="Filter by booking status"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    lot_id: Optional[UUID] = Query(None, description="Filter by parking lot ID"),
    start_date: Optional[str] = Query(None, description="Filter bookings from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter bookings to date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all bookings for admin with filtering options."""
    try:
        booking_service = BookingService(session)
        
        # Convert status string to enum if provided
        booking_status = BookingStatus(status) if status else None
        
        # Parse date strings if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            start_datetime = datetime.fromisoformat(start_date)
        if end_date:
            end_datetime = datetime.fromisoformat(end_date + "T23:59:59")
        
        # Get bookings with filters
        bookings = await booking_service.get_all_bookings_admin(
            skip=skip,
            limit=limit,
            status=booking_status,
            user_id=user_id,
            lot_id=lot_id,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return [BookingResponse.from_orm(booking) for booking in bookings]
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.put("/bookings/{booking_id}/cancel", response_model=SuccessResponse)
async def admin_cancel_booking(
    booking_id: UUID,
    reason: Optional[str] = Query(None, description="Reason for cancellation"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Admin cancel any booking."""
    try:
        booking_service = BookingService(session)
        
        success = await booking_service.admin_cancel_booking(booking_id, reason)
        
        if success:
            return SuccessResponse(message="Booking cancelled successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel booking"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/bookings/{booking_id}/refund", response_model=SuccessResponse)
async def process_refund(
    booking_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Process refund for a cancelled booking."""
    try:
        booking_service = BookingService(session)
        
        success = await booking_service.process_refund(booking_id)
        
        if success:
            return SuccessResponse(message="Refund processed successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process refund"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/reports/revenue")
async def get_revenue_report(
    start_date: date = Query(..., description="Start date for report"),
    end_date: date = Query(..., description="End date for report"),
    lot_id: Optional[UUID] = Query(None, description="Filter by specific parking lot"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get revenue report for date range."""
    try:
        booking_service = BookingService(session)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        statistics = await booking_service.get_booking_statistics(
            start_date=start_datetime,
            end_date=end_datetime,
            lot_id=lot_id
        )
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "summary": {
                "total_revenue": float(statistics.get("total_revenue", 0)),
                "total_bookings": statistics.get("total_bookings", 0),
                "average_booking_value": float(statistics.get("average_booking_value", 0)),
                "status_breakdown": statistics.get("status_breakdown", {}),
                "vehicle_type_breakdown": statistics.get("vehicle_type_breakdown", {})
            }
        }
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/users/statistics")
async def get_user_statistics(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user statistics."""
    try:
        user_service = UserService(session)
        
        total_users = await user_service.count()
        active_users = await user_service.count(is_active=True)
        admin_users = await user_service.count(is_admin=True)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users
        }
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/maintenance/cleanup-expired", response_model=SuccessResponse)
async def cleanup_expired_bookings(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Manually trigger cleanup of expired bookings."""
    try:
        booking_service = BookingService(session)
        
        expired_count = await booking_service.process_expired_bookings()
        no_show_count = await booking_service.process_no_show_bookings()
        
        return SuccessResponse(
            message=f"Cleanup completed: {expired_count} expired, {no_show_count} no-show bookings processed"
        )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)