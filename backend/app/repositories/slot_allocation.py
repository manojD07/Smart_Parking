"""Repository for SlotAllocation model operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.repositories.base import BaseRepository
from app.models.booking import SlotAllocation, AllocationType, BookingStatus, Booking
from app.models.parking import VehicleType

logger = structlog.get_logger(__name__)


class SlotAllocationRepository(BaseRepository[SlotAllocation]):
    """Repository for SlotAllocation model operations with bike-in-car logic."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, SlotAllocation)
        self.logger = logger.bind(repository="SlotAllocationRepository")
    
    async def create_allocation(
        self,
        booking_id: UUID,
        slot_id: UUID,
        allocation_type: AllocationType,
        allocated_space: Optional[str] = None
    ) -> SlotAllocation:
        """
        Create a new slot allocation with space designation.
        
        Args:
            booking_id: ID of the booking
            slot_id: ID of the allocated slot
            allocation_type: FULL or PARTIAL allocation
            allocated_space: Space designation (e.g., 'left_half', 'right_half')
            
        Returns:
            Created SlotAllocation instance
        """
        try:
            allocation = SlotAllocation(
                booking_id=booking_id,
                slot_id=slot_id,
                allocation_type=allocation_type.value,
                allocated_space=allocated_space
            )
            
            self.session.add(allocation)
            await self.session.flush()  # Get ID without committing
            
            self.logger.info(
                "Slot allocation created",
                allocation_id=allocation.id,
                booking_id=booking_id,
                slot_id=slot_id,
                allocation_type=allocation_type.value,
                allocated_space=allocated_space
            )
            
            return allocation
            
        except Exception as e:
            self.logger.error("Failed to create slot allocation", error=str(e))
            raise
    
    async def get_allocations_by_slot(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime,
        active_only: bool = True
    ) -> List[SlotAllocation]:
        """
        Get all allocations for a slot within a time range.
        
        Args:
            slot_id: Slot ID to check
            start_time: Start of time range
            end_time: End of time range
            active_only: Only include active bookings
            
        Returns:
            List of SlotAllocation instances
        """
        try:
            query = (
                select(SlotAllocation)
                .options(
                    selectinload(SlotAllocation.booking),
                    selectinload(SlotAllocation.slot)
                )
                .join(SlotAllocation.booking)
                .where(SlotAllocation.slot_id == slot_id)
            )
            
            # Add time range filter
            query = query.where(
                and_(
                    # Booking overlaps with requested time range
                    Booking.start_time < end_time,
                    Booking.end_time > start_time
                )
            )
            
            # Filter for active bookings only
            if active_only:
                active_statuses = [
                    BookingStatus.CONFIRMED.value,
                    BookingStatus.ACTIVE.value
                ]
                query = query.where(
                    Booking.status.in_(active_statuses)
                )
            
            result = await self.session.execute(query)
            allocations = list(result.scalars().all())
            
            self.logger.debug(
                "Retrieved slot allocations",
                slot_id=slot_id,
                count=len(allocations),
                active_only=active_only
            )
            
            return allocations
            
        except Exception as e:
            self.logger.error("Failed to get slot allocations", error=str(e))
            raise
    
    async def count_bikes_in_car_slot(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """
        Count the number of bikes currently allocated to a car slot
        within the specified time range.
        
        Args:
            slot_id: Car slot ID
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Number of bikes (0, 1, or 2)
        """
        try:
            # Get all allocations for this slot in the time range
            allocations = await self.get_allocations_by_slot(
                slot_id, start_time, end_time, active_only=True
            )
            
            # Count bike allocations (partial allocations in car slots)
            bike_count = 0
            for allocation in allocations:
                if (allocation.allocation_type == AllocationType.PARTIAL.value and
                    allocation.booking and
                    allocation.booking.vehicle_type == VehicleType.BIKE.value):
                    bike_count += 1
            
            self.logger.debug(
                "Counted bikes in car slot",
                slot_id=slot_id,
                bike_count=bike_count,
                total_allocations=len(allocations)
            )
            
            return bike_count
            
        except Exception as e:
            self.logger.error("Failed to count bikes in car slot", error=str(e))
            return 0
    
    async def get_existing_bike_space(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[str]:
        """
        Get the space designation of an existing bike in a car slot.
        
        Args:
            slot_id: Car slot ID
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Space designation ('left_half' or 'right_half') or None
        """
        try:
            allocations = await self.get_allocations_by_slot(
                slot_id, start_time, end_time, active_only=True
            )
            
            # Find bike allocation
            for allocation in allocations:
                if (allocation.allocation_type == AllocationType.PARTIAL.value and
                    allocation.booking and
                    allocation.booking.vehicle_type == VehicleType.BIKE.value and
                    allocation.allocated_space):
                    
                    self.logger.debug(
                        "Found existing bike space",
                        slot_id=slot_id,
                        space=allocation.allocated_space
                    )
                    
                    return allocation.allocated_space
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to get existing bike space", error=str(e))
            return None
    
    async def get_available_bike_spaces_in_car_slot(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[str]:
        """
        Get available space designations in a car slot for bikes.
        
        Args:
            slot_id: Car slot ID
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of available spaces ('left_half', 'right_half')
        """
        try:
            bike_count = await self.count_bikes_in_car_slot(slot_id, start_time, end_time)
            
            if bike_count == 0:
                # No bikes - both spaces available, prefer left_half first
                return ["left_half", "right_half"]
            elif bike_count == 1:
                # One bike - find which space is occupied
                existing_space = await self.get_existing_bike_space(slot_id, start_time, end_time)
                if existing_space == "left_half":
                    return ["right_half"]
                else:
                    return ["left_half"]
            else:
                # Two or more bikes - no space available
                return []
            
        except Exception as e:
            self.logger.error("Failed to get available bike spaces", error=str(e))
            return []
    
    async def can_accommodate_bike(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Check if a car slot can accommodate another bike.
        
        Args:
            slot_id: Car slot ID
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            True if slot can accommodate another bike
        """
        try:
            bike_count = await self.count_bikes_in_car_slot(slot_id, start_time, end_time)
            can_accommodate = bike_count < 2
            
            self.logger.debug(
                "Checked bike accommodation",
                slot_id=slot_id,
                current_bikes=bike_count,
                can_accommodate=can_accommodate
            )
            
            return can_accommodate
            
        except Exception as e:
            self.logger.error("Failed to check bike accommodation", error=str(e))
            return False
    
    async def get_car_slots_with_bike_capacity(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get car slots that can accommodate bikes with their current bike count.
        
        Args:
            lot_id: Parking lot ID
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of slots to return
            
        Returns:
            List of dicts with slot info and bike capacity
        """
        try:
            # This would typically join with parking_slots table
            # For now, we'll implement a simplified version
            # TODO: Implement proper join query with parking_slots
            
            result = []
            # This is a placeholder - in a real implementation, 
            # you would query parking_slots and check bike capacity for each
            
            self.logger.debug(
                "Retrieved car slots with bike capacity",
                lot_id=lot_id,
                count=len(result)
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to get car slots with bike capacity", error=str(e))
            return []
    
    async def get_allocations_by_booking(
        self,
        booking_id: UUID
    ) -> List[SlotAllocation]:
        """
        Get all allocations for a specific booking.
        
        Args:
            booking_id: Booking ID
            
        Returns:
            List of SlotAllocation instances
        """
        try:
            query = (
                select(SlotAllocation)
                .options(
                    selectinload(SlotAllocation.slot),
                    selectinload(SlotAllocation.booking)
                )
                .where(SlotAllocation.booking_id == booking_id)
            )
            
            result = await self.session.execute(query)
            allocations = list(result.scalars().all())
            
            self.logger.debug(
                "Retrieved allocations for booking",
                booking_id=booking_id,
                count=len(allocations)
            )
            
            return allocations
            
        except Exception as e:
            self.logger.error("Failed to get allocations by booking", error=str(e))
            return []
    
    async def delete_allocations_by_booking(
        self,
        booking_id: UUID
    ) -> int:
        """
        Delete all allocations for a booking (for cancellations).
        
        Args:
            booking_id: Booking ID
            
        Returns:
            Number of deleted allocations
        """
        try:
            allocations = await self.get_allocations_by_booking(booking_id)
            count = len(allocations)
            
            for allocation in allocations:
                await self.delete(allocation.id)
            
            self.logger.info(
                "Deleted allocations for booking",
                booking_id=booking_id,
                count=count
            )
            
            return count
            
        except Exception as e:
            self.logger.error("Failed to delete allocations", error=str(e))
            return 0
    
    def _add_relationship_loading(self, query):
        """Add relationship loading to query."""
        return query.options(
            selectinload(SlotAllocation.booking),
            selectinload(SlotAllocation.slot)
        )
