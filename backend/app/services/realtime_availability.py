"""Real-time availability service for broadcasting parking updates."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from app.models.parking import ParkingLot, ParkingSlot, VehicleType, SlotStatus
from app.models.booking import Booking, BookingStatus, SlotAllocation
from app.repositories.parking import ParkingLotRepository, ParkingSlotRepository
from app.repositories.booking import BookingRepository, SlotAllocationRepository
from app.services.base import BaseService
from app.events.domain_events import DomainEventFactory, DomainEventType
from app.events.event_publisher import event_publisher
from app.core.exceptions import NotFoundError, BusinessLogicError

logger = structlog.get_logger(__name__)


class RealTimeAvailabilityService(BaseService):
    """
    Service for managing real-time availability updates and broadcasting.
    
    Provides comprehensive availability tracking, change detection,
    and real-time event broadcasting for parking operations.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.lot_repository = ParkingLotRepository(session)
        self.slot_repository = ParkingSlotRepository(session)
        self.booking_repository = BookingRepository(session)
        self.allocation_repository = SlotAllocationRepository(session)
        
        # Availability cache for change detection
        self.availability_cache: Dict[str, Dict[str, Any]] = {}
        
        self.logger = logger.bind(service="RealTimeAvailabilityService")
    
    async def get_lot_availability(
        self,
        lot_id: UUID,
        vehicle_type: Optional[VehicleType] = None,
        real_time: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive availability for a parking lot.
        
        Args:
            lot_id: Parking lot ID
            vehicle_type: Specific vehicle type (None for all types)
            real_time: Whether to include real-time booking data
            
        Returns:
            Comprehensive availability data
        """
        try:
            # Get parking lot
            lot = await self.lot_repository.get_by_id(lot_id)
            if not lot:
                raise NotFoundError(f"Parking lot {lot_id} not found")
            
            # Calculate availability for each vehicle type
            availability_data = {
                "lot_id": str(lot_id),
                "lot_name": lot.name,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "vehicle_types": {}
            }
            
            # Vehicle types to check
            types_to_check = [vehicle_type] if vehicle_type else [VehicleType.CAR, VehicleType.BIKE]
            
            total_available = 0
            total_capacity = 0
            
            for vtype in types_to_check:
                type_availability = await self._calculate_vehicle_type_availability(
                    lot_id, vtype, real_time
                )
                availability_data["vehicle_types"][vtype.value] = type_availability
                
                total_available += type_availability["available_slots"]
                total_capacity += type_availability["total_slots"]
            
            # Overall availability
            availability_data.update({
                "total_available_slots": total_available,
                "total_capacity": total_capacity,
                "overall_occupancy_rate": round((total_capacity - total_available) / total_capacity * 100, 2) if total_capacity > 0 else 0,
                "is_full": total_available == 0,
                "has_capacity": total_available > 0
            })
            
            return availability_data
            
        except Exception as e:
            self.logger.error("Failed to get lot availability", lot_id=lot_id, error=str(e))
            raise BusinessLogicError(f"Failed to get availability for lot {lot_id}")
    
    async def _calculate_vehicle_type_availability(
        self,
        lot_id: UUID,
        vehicle_type: VehicleType,
        real_time: bool = True
    ) -> Dict[str, Any]:
        """Calculate availability for a specific vehicle type."""
        
        # Get all slots for this vehicle type
        all_slots = await self.slot_repository.get_multi(
            lot_id=lot_id,
            slot_type=vehicle_type.value,
            limit=1000
        )
        
        # Count available slots based on status
        available_slots = len([
            slot for slot in all_slots 
            if slot.status == SlotStatus.AVAILABLE.value
        ])
        
        occupied_slots = len([
            slot for slot in all_slots 
            if slot.status == SlotStatus.OCCUPIED.value
        ])
        
        reserved_slots = len([
            slot for slot in all_slots 
            if slot.status == SlotStatus.RESERVED.value
        ])
        
        maintenance_slots = len([
            slot for slot in all_slots 
            if slot.status == SlotStatus.MAINTENANCE.value
        ])
        
        # For bike type, also check car slots that can accommodate bikes
        if vehicle_type == VehicleType.BIKE and real_time:
            bike_in_car_availability = await self._calculate_bike_in_car_availability(lot_id)
            available_slots += bike_in_car_availability["additional_bike_slots"]
        else:
            bike_in_car_availability = {"additional_bike_slots": 0, "car_slots_with_space": 0}
        
        total_slots = len(all_slots)
        occupancy_rate = (occupied_slots / total_slots * 100) if total_slots > 0 else 0
        
        return {
            "vehicle_type": vehicle_type.value,
            "total_slots": total_slots,
            "available_slots": available_slots,
            "occupied_slots": occupied_slots,
            "reserved_slots": reserved_slots,
            "maintenance_slots": maintenance_slots,
            "occupancy_rate": round(occupancy_rate, 2),
            "bike_in_car_availability": bike_in_car_availability
        }
    
    async def _calculate_bike_in_car_availability(self, lot_id: UUID) -> Dict[str, Any]:
        """Calculate how many bikes can fit in car slots."""
        
        # Get all car slots
        car_slots = await self.slot_repository.get_multi(
            lot_id=lot_id,
            slot_type=VehicleType.CAR.value,
            limit=1000
        )
        
        additional_bike_slots = 0
        car_slots_with_space = 0
        
        for car_slot in car_slots:
            if car_slot.status == SlotStatus.AVAILABLE.value:
                # Empty car slot can accommodate 2 bikes
                additional_bike_slots += 2
                car_slots_with_space += 1
            elif car_slot.status in [SlotStatus.OCCUPIED.value, SlotStatus.RESERVED.value]:
                # Check how many bikes are already in this slot
                # This would require checking allocations, for now assume partially available
                # In real implementation, check SlotAllocation records
                pass
        
        return {
            "additional_bike_slots": additional_bike_slots,
            "car_slots_with_space": car_slots_with_space
        }
    
    async def notify_availability_change(
        self,
        lot_id: UUID,
        vehicle_type: VehicleType,
        change_type: str = "slot_update",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Notify about availability changes and broadcast to WebSocket clients.
        
        Args:
            lot_id: Parking lot ID
            vehicle_type: Vehicle type affected
            change_type: Type of change (slot_update, booking_change, etc.)
            metadata: Additional change metadata
            
        Returns:
            True if notification was sent successfully
        """
        try:
            # Get current availability
            current_availability = await self._calculate_vehicle_type_availability(
                lot_id, vehicle_type, real_time=True
            )
            
            # Get cached availability for comparison
            cache_key = f"{lot_id}:{vehicle_type.value}"
            cached_availability = self.availability_cache.get(cache_key)
            
            # Detect changes
            if cached_availability:
                old_available = cached_availability.get("available_slots", 0)
                new_available = current_availability["available_slots"]
                
                if old_available != new_available:
                    # Availability changed - create domain event
                    event = DomainEventFactory.availability_changed(
                        lot_id=lot_id,
                        vehicle_type=vehicle_type.value,
                        old_available=old_available,
                        new_available=new_available,
                        total_slots=current_availability["total_slots"]
                    )
                    
                    # Add change metadata
                    event.data.metadata.update({
                        "change_type": change_type,
                        "occupancy_change": current_availability["occupancy_rate"] - cached_availability.get("occupancy_rate", 0),
                        **(metadata or {})
                    })
                    
                    # Publish event
                    await event_publisher.publish(event)
                    
                    self.logger.info(
                        "Availability change published",
                        lot_id=lot_id,
                        vehicle_type=vehicle_type.value,
                        old_available=old_available,
                        new_available=new_available,
                        change=new_available - old_available
                    )
            
            # Update cache
            self.availability_cache[cache_key] = current_availability
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to notify availability change",
                lot_id=lot_id,
                vehicle_type=vehicle_type.value,
                error=str(e)
            )
            return False
    
    async def notify_slot_status_change(
        self,
        slot_id: UUID,
        old_status: SlotStatus,
        new_status: SlotStatus,
        booking_id: Optional[UUID] = None
    ) -> bool:
        """
        Notify about slot status changes.
        
        Args:
            slot_id: Slot ID
            old_status: Previous slot status
            new_status: New slot status
            booking_id: Associated booking ID (if applicable)
            
        Returns:
            True if notification was sent successfully
        """
        try:
            # Get slot information
            slot = await self.slot_repository.get_by_id(slot_id)
            if not slot:
                return False
            
            # Create slot status change event
            event = DomainEventFactory.slot_status_changed(
                slot_id=slot_id,
                lot_id=slot.lot_id,
                old_status=old_status.value,
                new_status=new_status.value,
                booking_id=booking_id
            )
            
            # Publish event
            await event_publisher.publish(event)
            
            # Also notify availability change for the lot
            vehicle_type = VehicleType(slot.slot_type)
            await self.notify_availability_change(
                lot_id=slot.lot_id,
                vehicle_type=vehicle_type,
                change_type="slot_status_change",
                metadata={
                    "slot_id": str(slot_id),
                    "status_change": f"{old_status.value} -> {new_status.value}",
                    "booking_id": str(booking_id) if booking_id else None
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to notify slot status change",
                slot_id=slot_id,
                error=str(e)
            )
            return False
    
    async def notify_capacity_update(
        self,
        lot_id: UUID,
        capacity_changes: Dict[str, int]
    ) -> bool:
        """
        Notify about capacity updates (new slots added/removed).
        
        Args:
            lot_id: Parking lot ID
            capacity_changes: Dict of vehicle_type -> capacity_change
            
        Returns:
            True if notification was sent successfully
        """
        try:
            for vehicle_type_str, change in capacity_changes.items():
                if change != 0:
                    # Create capacity update event
                    event = DomainEventFactory.availability_changed(
                        lot_id=lot_id,
                        vehicle_type=vehicle_type_str,
                        old_available=0,  # Will be filled by availability service
                        new_available=0,  # Will be filled by availability service
                        total_slots=0     # Will be filled by availability service
                    )
                    
                    event.event_type = DomainEventType.CAPACITY_UPDATED
                    event.data.metadata.update({
                        "capacity_change": change,
                        "change_type": "capacity_update"
                    })
                    
                    # Publish event
                    await event_publisher.publish(event)
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to notify capacity update",
                lot_id=lot_id,
                error=str(e)
            )
            return False
    
    async def get_lot_occupancy_analytics(
        self,
        lot_id: UUID,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get occupancy analytics for a parking lot.
        
        Args:
            lot_id: Parking lot ID
            time_range_hours: Time range for analytics in hours
            
        Returns:
            Occupancy analytics data
        """
        try:
            # Get current availability
            current_availability = await self.get_lot_availability(lot_id)
            
            # Calculate time-based metrics
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # Get booking history for analytics
            booking_query = select(Booking).where(
                Booking.lot_id == lot_id,
                Booking.start_time >= start_time,
                Booking.start_time <= end_time
            )
            
            result = await self.session.execute(booking_query)
            bookings = result.scalars().all()
            
            # Calculate analytics
            total_bookings = len(bookings)
            completed_bookings = len([b for b in bookings if b.status == BookingStatus.COMPLETED.value])
            cancelled_bookings = len([b for b in bookings if b.status == BookingStatus.CANCELLED.value])
            
            vehicle_type_breakdown = {}
            for booking in bookings:
                vtype = booking.vehicle_type
                if vtype not in vehicle_type_breakdown:
                    vehicle_type_breakdown[vtype] = 0
                vehicle_type_breakdown[vtype] += 1
            
            analytics = {
                "lot_id": str(lot_id),
                "time_range_hours": time_range_hours,
                "current_availability": current_availability,
                "booking_metrics": {
                    "total_bookings": total_bookings,
                    "completed_bookings": completed_bookings,
                    "cancelled_bookings": cancelled_bookings,
                    "completion_rate": round(completed_bookings / total_bookings * 100, 2) if total_bookings > 0 else 0,
                    "vehicle_type_breakdown": vehicle_type_breakdown
                },
                "occupancy_trends": {
                    # This would include hourly occupancy data
                    # For now, return placeholder
                    "peak_hours": [],
                    "average_occupancy": current_availability["overall_occupancy_rate"]
                }
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(
                "Failed to get occupancy analytics",
                lot_id=lot_id,
                error=str(e)
            )
            raise BusinessLogicError(f"Failed to get analytics for lot {lot_id}")
    
    async def refresh_availability_cache(self, lot_id: Optional[UUID] = None) -> int:
        """
        Refresh availability cache for all lots or a specific lot.
        
        Args:
            lot_id: Specific lot ID (None for all lots)
            
        Returns:
            Number of lots refreshed
        """
        try:
            lots_to_refresh = []
            
            if lot_id:
                lot = await self.lot_repository.get_by_id(lot_id)
                if lot:
                    lots_to_refresh = [lot]
            else:
                lots_to_refresh = await self.lot_repository.get_multi(limit=1000)
            
            refreshed_count = 0
            
            for lot in lots_to_refresh:
                for vehicle_type in [VehicleType.CAR, VehicleType.BIKE]:
                    availability = await self._calculate_vehicle_type_availability(
                        lot.id, vehicle_type, real_time=True
                    )
                    
                    cache_key = f"{lot.id}:{vehicle_type.value}"
                    self.availability_cache[cache_key] = availability
                
                refreshed_count += 1
            
            self.logger.info(
                "Availability cache refreshed",
                lots_refreshed=refreshed_count,
                specific_lot=str(lot_id) if lot_id else "all"
            )
            
            return refreshed_count
            
        except Exception as e:
            self.logger.error("Failed to refresh availability cache", error=str(e))
            return 0
