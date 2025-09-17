"""Booking and slot allocation repositories."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.repositories.base import BaseRepository
from app.models.booking import Booking, SlotAllocation, BookingStatus, AllocationType
from app.models.parking import ParkingSlot, VehicleType
from app.models.user import User


class BookingRepository(BaseRepository[Booking]):
    """Repository for Booking model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Booking)
    
    async def get_by_reference(self, booking_reference: str) -> Optional[Booking]:
        """Get booking by reference code."""
        try:
            query = (
                select(Booking)
                .options(
                    joinedload(Booking.user),
                    joinedload(Booking.lot),
                    joinedload(Booking.slot)
                )
                .where(Booking.booking_reference == booking_reference)
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error("Failed to get booking by reference", reference=booking_reference, error=str(e))
            raise
    
    async def get_user_bookings(
        self, 
        user_id: UUID, 
        status: Optional[BookingStatus] = None,
        skip: int = 0, 
        limit: int = 20
    ) -> List[Booking]:
        """Get bookings for a specific user."""
        try:
            query = (
                select(Booking)
                .options(
                    joinedload(Booking.lot),
                    joinedload(Booking.slot)
                )
                .where(Booking.user_id == user_id)
            )
            
            if status:
                query = query.where(Booking.status == status.value)
            
            query = query.order_by(desc(Booking.created_at)).offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get user bookings", user_id=user_id, error=str(e))
            raise
    
    async def get_all_bookings_admin(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[BookingStatus] = None,
        user_id: Optional[UUID] = None,
        lot_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Booking]:
        """Get all bookings for admin with filtering."""
        try:
            query = (
                select(Booking)
                .options(
                    joinedload(Booking.user),
                    joinedload(Booking.lot),
                    joinedload(Booking.slot)
                )
            )
            
            # Apply filters
            if status:
                query = query.where(Booking.status == status.value)
            
            if user_id:
                query = query.where(Booking.user_id == user_id)
            
            if lot_id:
                query = query.where(Booking.lot_id == lot_id)
            
            if start_date:
                query = query.where(Booking.start_time >= start_date)
            
            if end_date:
                query = query.where(Booking.end_time <= end_date)
            
            # Order by most recent first
            query = query.order_by(desc(Booking.created_at))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get all bookings for admin", error=str(e))
            raise
    
    async def get_lot_bookings(
        self, 
        lot_id: UUID, 
        status: Optional[BookingStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0, 
        limit: int = 50
    ) -> List[Booking]:
        """Get bookings for a specific parking lot."""
        try:
            query = (
                select(Booking)
                .options(
                    joinedload(Booking.user),
                    joinedload(Booking.slot)
                )
                .where(Booking.lot_id == lot_id)
            )
            
            if status:
                query = query.where(Booking.status == status.value)
            
            if start_date:
                query = query.where(Booking.start_time >= start_date)
            
            if end_date:
                query = query.where(Booking.end_time <= end_date)
            
            query = query.order_by(desc(Booking.created_at)).offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get lot bookings", lot_id=lot_id, error=str(e))
            raise
    
    async def get_active_bookings_in_timeframe(
        self, 
        start_time: datetime, 
        end_time: datetime,
        lot_id: Optional[UUID] = None
    ) -> List[Booking]:
        """Get active bookings that overlap with given timeframe."""
        try:
            query = (
                select(Booking)
                .where(
                    and_(
                        Booking.status == BookingStatus.ACTIVE.value,
                        or_(
                            and_(Booking.start_time < end_time, Booking.end_time > start_time)
                        )
                    )
                )
            )
            
            if lot_id:
                query = query.where(Booking.lot_id == lot_id)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get active bookings in timeframe", error=str(e))
            raise
    
    async def get_conflicting_bookings(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[Booking]:
        """Get bookings that conflict with given time range for a slot."""
        try:
            query = (
                select(Booking)
                .where(
                    and_(
                        Booking.slot_id == slot_id,
                        Booking.status == BookingStatus.ACTIVE.value,
                        or_(
                            and_(Booking.start_time < end_time, Booking.end_time > start_time)
                        )
                    )
                )
            )
            
            if exclude_booking_id:
                query = query.where(Booking.id != exclude_booking_id)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get conflicting bookings", slot_id=slot_id, error=str(e))
            raise
    
    async def get_expired_bookings(self, cutoff_time: Optional[datetime] = None) -> List[Booking]:
        """Get bookings that should be marked as expired."""
        try:
            if not cutoff_time:
                cutoff_time = datetime.now(timezone.utc)
            
            query = (
                select(Booking)
                .where(
                    and_(
                        Booking.status == BookingStatus.ACTIVE.value,
                        Booking.end_time < cutoff_time
                    )
                )
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get expired bookings", error=str(e))
            raise
    
    async def get_no_show_bookings(self, grace_period_minutes: int = 15) -> List[Booking]:
        """Get bookings that should be marked as no-show."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=grace_period_minutes)
            
            query = (
                select(Booking)
                .where(
                    and_(
                        Booking.status == BookingStatus.ACTIVE.value,
                        Booking.start_time < cutoff_time,
                        Booking.check_in_time.is_(None)
                    )
                )
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get no-show bookings", error=str(e))
            raise
    
    async def search_bookings(
        self, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Booking]:
        """Search bookings by reference, vehicle number, or user details."""
        try:
            search_pattern = f"%{search_term}%"
            
            query = (
                select(Booking)
                .join(Booking.user)
                .options(
                    joinedload(Booking.user),
                    joinedload(Booking.lot),
                    joinedload(Booking.slot)
                )
                .where(
                    or_(
                        Booking.booking_reference.ilike(search_pattern),
                        Booking.vehicle_number.ilike(search_pattern),
                        Booking.user.has(
                            or_(
                                User.first_name.ilike(search_pattern),
                                User.last_name.ilike(search_pattern),
                                User.email.ilike(search_pattern)
                            )
                        )
                    )
                )
                .order_by(desc(Booking.created_at))
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to search bookings", search_term=search_term, error=str(e))
            raise
    
    async def get_booking_statistics(
        self, 
        start_date: datetime, 
        end_date: datetime,
        lot_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get booking statistics for a date range."""
        try:
            base_query = select(Booking).where(
                and_(
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date
                )
            )
            
            if lot_id:
                base_query = base_query.where(Booking.lot_id == lot_id)
            
            # Total bookings and revenue
            stats_query = (
                select(
                    func.count(Booking.id).label('total_bookings'),
                    func.sum(Booking.total_amount).label('total_revenue'),
                    func.avg(Booking.total_amount).label('average_booking_value')
                )
                .select_from(base_query.subquery())
            )
            
            stats_result = await self.session.execute(stats_query)
            stats = dict(stats_result.fetchone()._mapping)
            
            # Bookings by status
            status_query = (
                select(
                    Booking.status,
                    func.count(Booking.id).label('count')
                )
                .select_from(base_query.subquery())
                .group_by(Booking.status)
            )
            
            status_result = await self.session.execute(status_query)
            status_stats = {row.status: row.count for row in status_result.fetchall()}
            
            # Bookings by vehicle type
            vehicle_query = (
                select(
                    Booking.vehicle_type,
                    func.count(Booking.id).label('count'),
                    func.sum(Booking.total_amount).label('revenue')
                )
                .select_from(base_query.subquery())
                .group_by(Booking.vehicle_type)
            )
            
            vehicle_result = await self.session.execute(vehicle_query)
            vehicle_stats = {
                row.vehicle_type: {'count': row.count, 'revenue': float(row.revenue or 0)}
                for row in vehicle_result.fetchall()
            }
            
            return {
                **stats,
                'total_revenue': float(stats['total_revenue'] or 0),
                'average_booking_value': float(stats['average_booking_value'] or 0),
                'status_breakdown': status_stats,
                'vehicle_type_breakdown': vehicle_stats
            }
            
        except Exception as e:
            self.logger.error("Failed to get booking statistics", error=str(e))
            raise
    
    async def bulk_update_status(self, booking_ids: List[UUID], status: BookingStatus) -> int:
        """Update status for multiple bookings."""
        try:
            if not booking_ids:
                return 0
            
            query = (
                update(Booking)
                .where(Booking.id.in_(booking_ids))
                .values(status=status.value, updated_at=datetime.now(timezone.utc))
            )
            
            result = await self.session.execute(query)
            updated_count = result.rowcount
            
            self.logger.info("Bulk updated booking status", count=updated_count, status=status.value)
            return updated_count
            
        except Exception as e:
            self.logger.error("Failed to bulk update booking status", error=str(e))
            raise
    
    def _add_relationship_loading(self, query):
        """Add relationship loading for booking queries."""
        return query.options(
            joinedload(Booking.user),
            joinedload(Booking.lot),
            joinedload(Booking.slot),
            selectinload(Booking.slot_allocations)
        )


class SlotAllocationRepository(BaseRepository[SlotAllocation]):
    """Repository for SlotAllocation model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, SlotAllocation)
    
    async def get_by_booking(self, booking_id: UUID) -> List[SlotAllocation]:
        """Get slot allocations for a booking."""
        try:
            query = (
                select(SlotAllocation)
                .options(
                    joinedload(SlotAllocation.slot),
                    joinedload(SlotAllocation.booking)
                )
                .where(SlotAllocation.booking_id == booking_id)
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get allocations by booking", booking_id=booking_id, error=str(e))
            raise
    
    async def get_by_slot(self, slot_id: UUID, start_time: datetime, end_time: datetime) -> List[SlotAllocation]:
        """Get slot allocations for a slot in a time range."""
        try:
            query = (
                select(SlotAllocation)
                .join(SlotAllocation.booking)
                .options(
                    joinedload(SlotAllocation.booking),
                    joinedload(SlotAllocation.slot)
                )
                .where(
                    and_(
                        SlotAllocation.slot_id == slot_id,
                        Booking.status == BookingStatus.ACTIVE.value,
                        or_(
                            and_(Booking.start_time < end_time, Booking.end_time > start_time)
                        )
                    )
                )
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get allocations by slot", slot_id=slot_id, error=str(e))
            raise
    
    async def create_allocation(
        self, 
        booking_id: UUID, 
        slot_id: UUID, 
        allocation_type: AllocationType,
        allocated_space: Optional[str] = None
    ) -> SlotAllocation:
        """Create a new slot allocation."""
        try:
            allocation = await self.create(
                booking_id=booking_id,
                slot_id=slot_id,
                allocation_type=allocation_type.value,
                allocated_space=allocated_space
            )
            
            self.logger.info(
                "Created slot allocation", 
                booking_id=booking_id, 
                slot_id=slot_id, 
                type=allocation_type.value
            )
            
            return allocation
            
        except Exception as e:
            self.logger.error("Failed to create slot allocation", error=str(e))
            raise
    
    async def get_slot_utilization(self, slot_id: UUID, date: datetime) -> Dict[str, Any]:
        """Get utilization statistics for a slot on a given date."""
        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            # Get all allocations for the day
            allocations = await self.get_by_slot(slot_id, start_of_day, end_of_day)
            
            total_duration = 0
            allocation_count = len(allocations)
            allocation_types = {}
            
            for allocation in allocations:
                booking = allocation.booking
                if booking:
                    # Calculate overlap with the day
                    booking_start = max(booking.start_time, start_of_day)
                    booking_end = min(booking.end_time, end_of_day)
                    
                    if booking_start < booking_end:
                        duration = (booking_end - booking_start).total_seconds() / 3600
                        total_duration += duration
                        
                        allocation_type = allocation.allocation_type
                        if allocation_type not in allocation_types:
                            allocation_types[allocation_type] = 0
                        allocation_types[allocation_type] += duration
            
            # Calculate utilization percentage (24 hours = 100%)
            utilization_rate = (total_duration / 24) * 100
            
            return {
                'slot_id': slot_id,
                'date': date.date(),
                'total_hours_occupied': total_duration,
                'utilization_rate': min(utilization_rate, 100),  # Cap at 100%
                'allocation_count': allocation_count,
                'allocation_types': allocation_types
            }
            
        except Exception as e:
            self.logger.error("Failed to get slot utilization", slot_id=slot_id, error=str(e))
            raise
    
    def _add_relationship_loading(self, query):
        """Add relationship loading for slot allocation queries."""
        return query.options(
            joinedload(SlotAllocation.booking),
            joinedload(SlotAllocation.slot)
        )
