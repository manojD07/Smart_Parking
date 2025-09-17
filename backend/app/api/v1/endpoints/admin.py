"""Admin management endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, timezone
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
        today = datetime.now(timezone.utc).date()
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


@router.get("/users")
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    search: Optional[str] = Query(None, description="Search term for email, first_name, or last_name"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all users for admin with filtering options."""
    try:
        user_service = UserService(session)
        
        # Get users with filters
        users = await user_service.get_all_users_admin(
            skip=skip,
            limit=limit,
            search=search,
            is_admin=is_admin,
            is_active=is_active
        )
        
        return users
        
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


@router.post("/parking/lots")
async def create_parking_lot(
    lot_data: dict,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new parking lot with automatic slot generation."""
    try:
        from app.models.parking import ParkingLot, ParkingSlot, VehicleType
        from decimal import Decimal
        
        # Create parking lot
        parking_lot = ParkingLot(
            name=lot_data["name"],
            address=lot_data["address"],
            latitude=float(lot_data["latitude"]),
            longitude=float(lot_data["longitude"]),
            total_car_slots=int(lot_data["total_car_slots"]),
            total_bike_slots=int(lot_data["total_bike_slots"]),
            hourly_rate_car=Decimal(str(lot_data["hourly_rate_car"])),
            hourly_rate_bike=Decimal(str(lot_data["hourly_rate_bike"])),
            is_active=True
        )
        
        session.add(parking_lot)
        await session.commit()
        await session.refresh(parking_lot)
        
        # Auto-generate parking slots
        slots = []
        
        # Create car slots
        for i in range(1, parking_lot.total_car_slots + 1):
            slot = ParkingSlot(
                lot_id=parking_lot.id,
                slot_number=f"C{i:03d}",
                slot_type=VehicleType.CAR,
                is_occupied=False,
                is_reserved=False
            )
            slots.append(slot)
        
        # Create bike slots
        for i in range(1, parking_lot.total_bike_slots + 1):
            slot = ParkingSlot(
                lot_id=parking_lot.id,
                slot_number=f"B{i:03d}",
                slot_type=VehicleType.BIKE,
                is_occupied=False,
                is_reserved=False
            )
            slots.append(slot)
        
        session.add_all(slots)
        await session.commit()
        
        return {
            "success": True,
            "message": f"Created parking lot '{parking_lot.name}' with {len(slots)} slots",
            "lot_id": str(parking_lot.id),
            "car_slots": parking_lot.total_car_slots,
            "bike_slots": parking_lot.total_bike_slots,
            "total_slots": len(slots)
        }
        
    except Exception as e:
        await session.rollback()
        return {"success": False, "error": str(e)}


@router.post("/parking/lots/{lot_id}/slots")
async def add_parking_slots(
    lot_id: UUID,
    slot_data: dict,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Add parking slots to an existing lot."""
    try:
        from app.models.parking import ParkingSlot, VehicleType, ParkingLot
        from sqlalchemy import select
        
        # Verify lot exists
        lot_result = await session.execute(
            select(ParkingLot).where(ParkingLot.id == lot_id)
        )
        lot = lot_result.scalar_one_or_none()
        
        if not lot:
            return {"success": False, "error": "Parking lot not found"}
        
        # Get existing slots count
        existing_result = await session.execute(
            select(ParkingSlot).where(ParkingSlot.lot_id == lot_id)
        )
        existing_slots = list(existing_result.scalars().all())
        
        # Determine next slot numbers
        car_slots = [s for s in existing_slots if s.slot_type == VehicleType.CAR]
        bike_slots = [s for s in existing_slots if s.slot_type == VehicleType.BIKE]
        
        next_car_num = len(car_slots) + 1
        next_bike_num = len(bike_slots) + 1
        
        new_slots = []
        
        # Add car slots if requested
        car_count = slot_data.get("car_slots", 0)
        if car_count > 0:
            for i in range(car_count):
                slot = ParkingSlot(
                    lot_id=lot_id,
                    slot_number=f"C{next_car_num + i:03d}",
                    slot_type=VehicleType.CAR,
                    is_occupied=False,
                    is_reserved=False
                )
                new_slots.append(slot)
        
        # Add bike slots if requested
        bike_count = slot_data.get("bike_slots", 0)
        if bike_count > 0:
            for i in range(bike_count):
                slot = ParkingSlot(
                    lot_id=lot_id,
                    slot_number=f"B{next_bike_num + i:03d}",
                    slot_type=VehicleType.BIKE,
                    is_occupied=False,
                    is_reserved=False
                )
                new_slots.append(slot)
        
        if new_slots:
            session.add_all(new_slots)
            
            # Update lot totals
            lot.total_car_slots += car_count
            lot.total_bike_slots += bike_count
            
            await session.commit()
            
            return {
                "success": True,
                "message": f"Added {len(new_slots)} slots to {lot.name}",
                "car_slots_added": car_count,
                "bike_slots_added": bike_count,
                "total_slots_now": len(existing_slots) + len(new_slots)
            }
        else:
            return {"success": False, "error": "No slots specified to add"}
        
    except Exception as e:
        await session.rollback()
        return {"success": False, "error": str(e)}

@router.get("/debug/lots/{lot_id}/slots")
async def debug_lot_slots(
    lot_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Debug endpoint to check slot data directly."""
    try:
        from app.models.parking import ParkingSlot
        from sqlalchemy import select
        
        # Direct database query
        result = await session.execute(
            select(ParkingSlot).where(ParkingSlot.lot_id == lot_id)
        )
        slots = list(result.scalars().all())
        
        return {
            "lot_id": str(lot_id),
            "slots_found": len(slots),
            "slots": [
                {
                    "id": str(s.id),
                    "slot_number": s.slot_number,
                    "slot_type": s.slot_type.value if hasattr(s.slot_type, 'value') else str(s.slot_type),
                    "is_occupied": s.is_occupied,
                    "is_reserved": s.is_reserved
                } for s in slots[:5]  # Show first 5 slots
            ]
        }
        
    except Exception as e:
        return {"error": str(e)}
