"""Parking lot and slot repositories."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.repositories.base import BaseRepository
from app.models.parking import ParkingLot, ParkingSlot, VehicleType, SlotStatus
from app.models.booking import Booking, BookingStatus


class ParkingLotRepository(BaseRepository[ParkingLot]):
    """Repository for ParkingLot model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ParkingLot)
    
    async def get_active_lots(self, skip: int = 0, limit: int = 100) -> List[ParkingLot]:
        """Get all active parking lots."""
        try:
            query = (
                select(ParkingLot)
                .where(ParkingLot.is_active == True)
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get active lots", error=str(e))
            raise
    
    async def get_lots_near_location(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 10.0,
        skip: int = 0,
        limit: int = 20
    ) -> List[ParkingLot]:
        """Get parking lots within radius of given coordinates."""
        try:
            # Haversine formula for distance calculation
            query = (
                select(ParkingLot)
                .where(
                    and_(
                        ParkingLot.is_active == True,
                        func.acos(
                            func.sin(func.radians(ParkingLot.latitude)) * func.sin(func.radians(latitude)) +
                            func.cos(func.radians(ParkingLot.latitude)) * func.cos(func.radians(latitude)) *
                            func.cos(func.radians(ParkingLot.longitude) - func.radians(longitude))
                        ) * 6371 <= radius_km  # Earth radius in km
                    )
                )
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get lots near location", error=str(e))
            raise
    
    async def get_lot_with_availability(
        self, 
        lot_id: UUID, 
        vehicle_type: VehicleType,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get parking lot with real-time availability."""
        try:
            # Get parking lot
            lot = await self.get_by_id(lot_id)
            if not lot or not lot.is_active:
                return None
            
            # Get availability for the time slot
            availability = await self._calculate_availability(
                lot_id, vehicle_type, start_time, end_time
            )
            
            return {
                "lot": lot,
                "availability": availability
            }
            
        except Exception as e:
            self.logger.error("Failed to get lot with availability", lot_id=lot_id, error=str(e))
            raise
    
    async def get_lots_with_availability(
        self, 
        vehicle_type: VehicleType,
        start_time: datetime,
        end_time: datetime,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all lots with availability for given criteria."""
        try:
            lots = await self.get_active_lots(skip=skip, limit=limit)
            
            results = []
            for lot in lots:
                availability = await self._calculate_availability(
                    lot.id, vehicle_type, start_time, end_time
                )
                
                if availability["available_slots"] > 0:
                    results.append({
                        "lot": lot,
                        "availability": availability
                    })
            
            return results
            
        except Exception as e:
            self.logger.error("Failed to get lots with availability", error=str(e))
            raise
    
    async def _calculate_availability(
        self, 
        lot_id: UUID, 
        vehicle_type: VehicleType,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Calculate availability for a parking lot."""
        try:
            # Get total slots for vehicle type
            total_slots_query = select(func.count(ParkingSlot.id)).where(
                and_(
                    ParkingSlot.lot_id == lot_id,
                    ParkingSlot.slot_type == vehicle_type.value,
                    ParkingSlot.status == SlotStatus.AVAILABLE.value
                )
            )
            total_result = await self.session.execute(total_slots_query)
            total_slots = total_result.scalar() or 0
            
            # Get occupied slots for the time period
            occupied_slots_query = (
                select(func.count(Booking.id))
                .join(ParkingSlot, Booking.slot_id == ParkingSlot.id)
                .where(
                    and_(
                        Booking.lot_id == lot_id,
                        Booking.vehicle_type == vehicle_type.value,
                        Booking.status == BookingStatus.ACTIVE.value,
                        or_(
                            and_(Booking.start_time < end_time, Booking.end_time > start_time)
                        )
                    )
                )
            )
            occupied_result = await self.session.execute(occupied_slots_query)
            occupied_slots = occupied_result.scalar() or 0
            
            # Handle bike allocation in car slots
            if vehicle_type == VehicleType.BIKE:
                # Check car slots that can accommodate bikes
                car_slots_capacity = await self._get_available_car_slots_for_bikes(
                    lot_id, start_time, end_time
                )
                total_slots += car_slots_capacity
            
            available_slots = max(0, total_slots - occupied_slots)
            
            return {
                "total_slots": total_slots,
                "occupied_slots": occupied_slots,
                "available_slots": available_slots,
                "occupancy_rate": (occupied_slots / total_slots * 100) if total_slots > 0 else 0
            }
            
        except Exception as e:
            self.logger.error("Failed to calculate availability", error=str(e))
            raise
    
    async def _get_available_car_slots_for_bikes(
        self, 
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Get number of bike spaces available in car slots."""
        try:
            # Get car slots that are not fully occupied by cars
            car_slots_query = (
                select(ParkingSlot.id)
                .where(
                    and_(
                        ParkingSlot.lot_id == lot_id,
                        ParkingSlot.slot_type == VehicleType.CAR.value,
                        ParkingSlot.status == SlotStatus.AVAILABLE.value
                    )
                )
            )
            car_slots_result = await self.session.execute(car_slots_query)
            car_slot_ids = [row[0] for row in car_slots_result.fetchall()]
            
            available_bike_spaces = 0
            
            for slot_id in car_slot_ids:
                # Check if car slot has any car bookings
                car_booking_query = (
                    select(func.count(Booking.id))
                    .where(
                        and_(
                            Booking.slot_id == slot_id,
                            Booking.vehicle_type == VehicleType.CAR.value,
                            Booking.status == BookingStatus.ACTIVE.value,
                            or_(
                                and_(Booking.start_time < end_time, Booking.end_time > start_time)
                            )
                        )
                    )
                )
                car_booking_result = await self.session.execute(car_booking_query)
                car_bookings = car_booking_result.scalar() or 0
                
                if car_bookings == 0:
                    # No car bookings, check bike bookings
                    bike_booking_query = (
                        select(func.count(Booking.id))
                        .where(
                            and_(
                                Booking.slot_id == slot_id,
                                Booking.vehicle_type == VehicleType.BIKE.value,
                                Booking.status == BookingStatus.ACTIVE.value,
                                or_(
                                    and_(Booking.start_time < end_time, Booking.end_time > start_time)
                                )
                            )
                        )
                    )
                    bike_booking_result = await self.session.execute(bike_booking_query)
                    bike_bookings = bike_booking_result.scalar() or 0
                    
                    # Each car slot can accommodate 2 bikes
                    available_bike_spaces += max(0, 2 - bike_bookings)
            
            return available_bike_spaces
            
        except Exception as e:
            self.logger.error("Failed to get available car slots for bikes", error=str(e))
            return 0
    
    async def get_lot_statistics(self, lot_id: UUID) -> Dict[str, Any]:
        """Get comprehensive statistics for a parking lot."""
        try:
            lot = await self.get_by_id(lot_id)
            if not lot:
                return {}
            
            # Total slots by type
            slots_stats_query = (
                select(
                    ParkingSlot.slot_type,
                    func.count(ParkingSlot.id).label('total'),
                    func.sum(case((ParkingSlot.is_occupied == True, 1), else_=0)).label('occupied'),
                    func.sum(case((ParkingSlot.is_reserved == True, 1), else_=0)).label('reserved')
                )
                .where(ParkingSlot.lot_id == lot_id)
                .group_by(ParkingSlot.slot_type)
            )
            slots_result = await self.session.execute(slots_stats_query)
            slots_stats = {row.slot_type: dict(row._mapping) for row in slots_result.fetchall()}
            
            # Booking statistics
            booking_stats_query = (
                select(
                    func.count(Booking.id).label('total_bookings'),
                    func.sum(case((Booking.status == BookingStatus.ACTIVE.value, 1), else_=0)).label('active_bookings'),
                    func.sum(Booking.total_amount).label('total_revenue')
                )
                .where(Booking.lot_id == lot_id)
            )
            booking_result = await self.session.execute(booking_stats_query)
            booking_stats = dict(booking_result.fetchone()._mapping)
            
            return {
                "lot": lot,
                "slots_statistics": slots_stats,
                "booking_statistics": booking_stats
            }
            
        except Exception as e:
            self.logger.error("Failed to get lot statistics", lot_id=lot_id, error=str(e))
            raise
    
    def _add_relationship_loading(self, query):
        """Add relationship loading for parking lot queries."""
        return query.options(
            selectinload(ParkingLot.slots),
            selectinload(ParkingLot.pricing_rules)
        )


class ParkingSlotRepository(BaseRepository[ParkingSlot]):
    """Repository for ParkingSlot model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ParkingSlot)
    
    async def get_available_slots(
        self, 
        lot_id: UUID, 
        vehicle_type: VehicleType,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10
    ) -> List[ParkingSlot]:
        """Get available slots for booking."""
        try:
            if vehicle_type == VehicleType.CAR:
                return await self._get_available_car_slots(lot_id, start_time, end_time, limit)
            else:
                return await self._get_available_bike_slots(lot_id, start_time, end_time, limit)
                
        except Exception as e:
            self.logger.error("Failed to get available slots", error=str(e))
            raise
    
    async def _get_available_car_slots(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime,
        limit: int
    ) -> List[ParkingSlot]:
        """Get available car slots."""
        try:
            # Get car slots that are not booked during the time period
            subquery = (
                select(Booking.slot_id)
                .where(
                    and_(
                        Booking.lot_id == lot_id,
                        Booking.status == BookingStatus.ACTIVE.value,
                        or_(
                            and_(Booking.start_time < end_time, Booking.end_time > start_time)
                        )
                    )
                )
            )
            
            query = (
                select(ParkingSlot)
                .where(
                    and_(
                        ParkingSlot.lot_id == lot_id,
                        ParkingSlot.slot_type == VehicleType.CAR.value,
                        ParkingSlot.status == SlotStatus.AVAILABLE.value,
                        ParkingSlot.id.not_in(subquery)
                    )
                )
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get available car slots", error=str(e))
            raise
    
    async def _get_available_bike_slots(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime,
        limit: int
    ) -> List[ParkingSlot]:
        """Get available bike slots or car slots that can accommodate bikes."""
        try:
            # First try dedicated bike slots
            bike_slots = await self._get_available_car_slots(lot_id, start_time, end_time, limit)
            bike_slots = [slot for slot in bike_slots if slot.slot_type == VehicleType.BIKE.value]
            
            if len(bike_slots) >= limit:
                return bike_slots[:limit]
            
            # Then try car slots that can accommodate bikes
            remaining_limit = limit - len(bike_slots)
            car_slots_for_bikes = await self._get_car_slots_for_bikes(
                lot_id, start_time, end_time, remaining_limit
            )
            
            return bike_slots + car_slots_for_bikes
            
        except Exception as e:
            self.logger.error("Failed to get available bike slots", error=str(e))
            raise
    
    async def _get_car_slots_for_bikes(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime,
        limit: int
    ) -> List[ParkingSlot]:
        """Get car slots that can accommodate bikes."""
        try:
            # Get car slots with no car bookings and less than 2 bike bookings
            query = (
                select(ParkingSlot)
                .where(
                    and_(
                        ParkingSlot.lot_id == lot_id,
                        ParkingSlot.slot_type == VehicleType.CAR.value,
                        ParkingSlot.status == SlotStatus.AVAILABLE.value
                    )
                )
            )
            
            result = await self.session.execute(query)
            car_slots = list(result.scalars().all())
            
            available_slots = []
            for slot in car_slots:
                if len(available_slots) >= limit:
                    break
                
                # Check if slot can accommodate more bikes
                if await self._can_slot_accommodate_bike(slot.id, start_time, end_time):
                    available_slots.append(slot)
            
            return available_slots
            
        except Exception as e:
            self.logger.error("Failed to get car slots for bikes", error=str(e))
            return []
    
    async def _can_slot_accommodate_bike(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Check if a car slot can accommodate another bike."""
        try:
            # Check for car bookings
            car_booking_query = (
                select(func.count(Booking.id))
                .where(
                    and_(
                        Booking.slot_id == slot_id,
                        Booking.vehicle_type == VehicleType.CAR.value,
                        Booking.status == BookingStatus.ACTIVE.value,
                        or_(
                            and_(Booking.start_time < end_time, Booking.end_time > start_time)
                        )
                    )
                )
            )
            car_result = await self.session.execute(car_booking_query)
            car_bookings = car_result.scalar() or 0
            
            if car_bookings > 0:
                return False
            
            # Check bike bookings (max 2 bikes per car slot)
            bike_booking_query = (
                select(func.count(Booking.id))
                .where(
                    and_(
                        Booking.slot_id == slot_id,
                        Booking.vehicle_type == VehicleType.BIKE.value,
                        Booking.status == BookingStatus.ACTIVE.value,
                        or_(
                            and_(Booking.start_time < end_time, Booking.end_time > start_time)
                        )
                    )
                )
            )
            bike_result = await self.session.execute(bike_booking_query)
            bike_bookings = bike_result.scalar() or 0
            
            return bike_bookings < 2
            
        except Exception as e:
            self.logger.error("Failed to check slot bike capacity", slot_id=slot_id, error=str(e))
            return False
    
    async def get_slots_by_lot(self, lot_id: UUID, skip: int = 0, limit: int = 100, **filters) -> List[ParkingSlot]:
        """Get all slots for a parking lot with optional filters."""
        try:
            query = select(ParkingSlot).where(ParkingSlot.lot_id == lot_id)
            
            # Apply filters
            if 'slot_type' in filters:
                query = query.where(ParkingSlot.slot_type == filters['slot_type'])
            
            if 'status' in filters:
                query = query.where(ParkingSlot.status == filters['status'])
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get slots by lot", lot_id=lot_id, filters=filters, error=str(e))
            raise
    
    async def update_slot_status(self, slot_id: UUID, status: SlotStatus) -> bool:
        """Update slot status."""
        try:
            updated_slot = await self.update(slot_id, status=status.value)
            return updated_slot is not None
            
        except Exception as e:
            self.logger.error("Failed to update slot status", slot_id=slot_id, error=str(e))
            raise
    
    def _add_relationship_loading(self, query):
        """Add relationship loading for parking slot queries."""
        return query.options(
            joinedload(ParkingSlot.lot),
            selectinload(ParkingSlot.bookings)
        )
