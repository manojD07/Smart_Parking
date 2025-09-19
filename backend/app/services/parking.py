"""Parking service for lot and slot management."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService
from app.repositories.parking import ParkingLotRepository, ParkingSlotRepository
from app.models.parking import ParkingLot, ParkingSlot, VehicleType, SlotStatus
from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.events.domain_events import DomainEventFactory
from app.events.event_publisher import event_publisher
import structlog

logger = structlog.get_logger(__name__)


class ParkingService(BaseService[ParkingLot, ParkingLotRepository]):
    """Service for parking lot and slot management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.lot_repository = ParkingLotRepository(session)
        self.slot_repository = ParkingSlotRepository(session)
        super().__init__(self.lot_repository)
        self.logger = logger.bind(service="ParkingService")
    
    async def create_parking_lot(
        self,
        name: str,
        address: str,
        latitude: float,
        longitude: float,
        total_car_slots: int,
        total_bike_slots: int,
        hourly_rate_car: float,
        hourly_rate_bike: float
    ) -> ParkingLot:
        """Create a new parking lot."""
        try:
            lot = await self.lot_repository.create(
                name=name,
                address=address,
                latitude=Decimal(str(latitude)),
                longitude=Decimal(str(longitude)),
                total_car_slots=total_car_slots,
                total_bike_slots=total_bike_slots,
                hourly_rate_car=Decimal(str(hourly_rate_car)),
                hourly_rate_bike=Decimal(str(hourly_rate_bike))
            )
            
            self.logger.info("Created parking lot", lot_id=lot.id, name=name)
            return lot
            
        except Exception as e:
            self.logger.error("Failed to create parking lot", error=str(e))
            raise BusinessLogicError("Failed to create parking lot")
    
    async def get_lot_availability(
        self,
        lot_id: UUID,
        vehicle_type: VehicleType,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get availability for a parking lot."""
        try:
            # Get the parking lot
            lot = await self.repository.get_by_id(lot_id)
            if not lot:
                raise NotFoundError("Parking lot not found")
            
            # Get slot repository
            slot_repository = ParkingSlotRepository(self.session)
            
            # Get all slots for this lot and vehicle type
            all_slots = await slot_repository.get_multi(
                lot_id=lot_id,
                slot_type=vehicle_type,
                limit=1000  # High limit to get all slots
            )
            
            # Count occupied slots (this is simplified - in a real system you'd check bookings)
            total_slots = len(all_slots)
            occupied_slots = len([slot for slot in all_slots if slot.is_occupied])
            available_slots = total_slots - occupied_slots
            occupancy_rate = (occupied_slots / total_slots * 100) if total_slots > 0 else 0
            
            return {
                "total_slots": total_slots,
                "occupied_slots": occupied_slots,
                "available_slots": available_slots,
                "occupancy_rate": round(occupancy_rate, 2)
            }
            
        except Exception as e:
            self.logger.error("Failed to get lot availability", lot_id=lot_id, error=str(e))
            raise BusinessLogicError("Failed to get lot availability")
    
    async def search_lots_near_location(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        skip: int = 0,
        limit: int = 20
    ) -> List[ParkingLot]:
        """Search parking lots near location."""
        return await self.lot_repository.get_lots_near_location(
            latitude, longitude, radius_km, skip, limit
        )
    
    async def get_lot_slots(self, lot_id: UUID, skip: int = 0, limit: int = 100, **filters) -> List[ParkingSlot]:
        """Get slots for a parking lot."""
        return await self.slot_repository.get_slots_by_lot(lot_id, skip, limit, **filters)
    
    async def create_parking_slot(self, lot_id: UUID, slot_number: str, slot_type: str) -> ParkingSlot:
        """Create a parking slot."""
        return await self.slot_repository.create(
            lot_id=lot_id,
            slot_number=slot_number,
            slot_type=slot_type
        )
    
    async def get_lot_statistics(self, lot_id: UUID) -> Dict[str, Any]:
        """Get statistics for a parking lot."""
        return await self.lot_repository.get_lot_statistics(lot_id)
    
    async def get_slot_by_id(self, slot_id: UUID) -> Optional[ParkingSlot]:
        """Get slot by ID."""
        return await self.slot_repository.get_by_id(slot_id)
    
    async def deactivate_slot(self, slot_id: UUID) -> ParkingSlot:
        """Deactivate a parking slot (admin only)."""
        try:
            # Get slot
            slot = await self.slot_repository.get_by_id(slot_id)
            if not slot:
                raise NotFoundError("Slot not found")
            
            self.logger.info("Attempting to deactivate slot", slot_id=slot_id, current_status=slot.status)
            
            # Simple validation: Only deactivate AVAILABLE slots
            if slot.status != SlotStatus.AVAILABLE.value:
                raise ValidationError(f"Cannot deactivate slot with status: {slot.status}")
            
            # Basic validation: Check occupancy flags
            if slot.is_occupied or slot.is_reserved:
                raise ValidationError("Cannot deactivate occupied or reserved slot")
            
            # Set to INACTIVE
            await self.slot_repository.update_slot_status(slot_id, SlotStatus.INACTIVE)
            
            self.logger.info("Slot deactivated successfully", slot_id=slot_id, slot_number=slot.slot_number)
            return await self.slot_repository.get_by_id(slot_id)
            
        except (NotFoundError, ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            self.logger.error("Failed to deactivate slot", slot_id=slot_id, error=str(e))
            raise BusinessLogicError("Failed to deactivate slot")
    
    async def reactivate_slot(self, slot_id: UUID) -> ParkingSlot:
        """Reactivate an inactive parking slot (admin only)."""
        try:
            # Get slot
            slot = await self.slot_repository.get_by_id(slot_id)
            if not slot:
                raise NotFoundError("Slot not found")
            
            # Validation: Only reactivate INACTIVE slots
            if slot.status != SlotStatus.INACTIVE.value:
                raise ValidationError("Can only reactivate inactive slots")
            
            # Set back to AVAILABLE
            await self.slot_repository.update_slot_status(slot_id, SlotStatus.AVAILABLE)
            
            self.logger.info("Slot reactivated", slot_id=slot_id, slot_number=slot.slot_number)
            return await self.slot_repository.get_by_id(slot_id)
            
        except Exception as e:
            self.logger.error("Failed to reactivate slot", slot_id=slot_id, error=str(e))
            raise
    
    async def delete_inactive_slot(self, slot_id: UUID) -> bool:
        """Delete an inactive parking slot (admin only)."""
        try:
            # Get slot
            slot = await self.slot_repository.get_by_id(slot_id)
            if not slot:
                raise NotFoundError("Slot not found")
            
            # Validation: Only delete INACTIVE slots
            if slot.status != SlotStatus.INACTIVE.value:
                raise ValidationError("Can only delete inactive slots")
            
            # Validation: Check booking history
            if await self._has_booking_history(slot_id):
                raise ValidationError("Cannot delete slot with booking history")
            
            # Delete slot
            success = await self.slot_repository.delete(slot_id)
            
            if success:
                self.logger.info("Slot deleted", slot_id=slot_id, slot_number=slot.slot_number)
            
            return success
            
        except Exception as e:
            self.logger.error("Failed to delete slot", slot_id=slot_id, error=str(e))
            raise
    
    async def _has_future_bookings(self, slot_id: UUID) -> bool:
        """Check if slot has future bookings."""
        try:
            from app.models.booking import Booking, BookingStatus
            from sqlalchemy import select, and_
            
            query = select(Booking.id).where(
                and_(
                    Booking.slot_id == slot_id,
                    Booking.start_time > datetime.now(timezone.utc),
                    Booking.status.in_([
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.ACTIVE.value,
                        BookingStatus.PENDING.value
                    ])
                )
            )
            
            result = await self.slot_repository.session.execute(query)
            return result.first() is not None
            
        except Exception as e:
            self.logger.error("Failed to check future bookings", slot_id=slot_id, error=str(e))
            return True  # Err on the side of caution
    
    async def _has_booking_history(self, slot_id: UUID) -> bool:
        """Check if slot has any booking history."""
        try:
            from app.models.booking import Booking
            from sqlalchemy import select
            
            query = select(Booking.id).where(Booking.slot_id == slot_id)
            result = await self.slot_repository.session.execute(query)
            return result.first() is not None
            
        except Exception as e:
            self.logger.error("Failed to check booking history", slot_id=slot_id, error=str(e))
            return True  # Err on the side of caution
    
    def _get_entity_name(self) -> str:
        """Get entity name for base service."""
        return "ParkingLot"
