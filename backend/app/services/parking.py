"""Parking service for lot and slot management."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService
from app.repositories.parking import ParkingLotRepository, ParkingSlotRepository
from app.models.parking import ParkingLot, ParkingSlot, VehicleType
from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
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
        return await self.slot_repository.get_slots_by_lot(lot_id, skip, limit)
    
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
    
    def _get_entity_name(self) -> str:
        """Get entity name for base service."""
        return "ParkingLot"
