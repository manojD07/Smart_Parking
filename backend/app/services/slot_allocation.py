"""Advanced slot allocation service with optimization algorithms."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.parking import ParkingSlot, VehicleType, SlotStatus
from app.models.booking import AllocationType
from app.repositories.parking import ParkingSlotRepository
from app.repositories.slot_allocation import SlotAllocationRepository
from app.core.exceptions import (
    InsufficientSlotsError,
    BusinessLogicError,
    ValidationError
)

logger = structlog.get_logger(__name__)


class AllocationStrategy(Enum):
    """Slot allocation strategies."""
    FIRST_FIT = "first_fit"
    BEST_FIT = "best_fit"
    OPTIMAL = "optimal"


@dataclass
class SlotAllocationRequest:
    """Request for slot allocation."""
    vehicle_type: VehicleType
    start_time: datetime
    end_time: datetime
    priority_level: int = 0
    user_preferences: Optional[Dict[str, Any]] = None
    user_id: Optional[UUID] = None


@dataclass
class AllocationResult:
    """Result of slot allocation."""
    slot: ParkingSlot
    allocation_type: AllocationType
    space_designation: Optional[str]
    confidence_score: float
    alternative_slots: Optional[List[ParkingSlot]] = None
    allocation_reason: str = ""


class OptimizedSlotAllocator:
    """
    Production-grade slot allocation with optimization algorithms.
    
    Implements the critical business logic:
    - 1 car slot can accommodate 2 bikes when empty
    - Advanced scoring system for optimal space utilization
    - Atomic allocation with conflict prevention
    """
    
    def __init__(
        self, 
        session: AsyncSession,
        strategy: AllocationStrategy = AllocationStrategy.OPTIMAL
    ):
        self.session = session
        self.strategy = strategy
        self.slot_repository = ParkingSlotRepository(session)
        self.allocation_repository = SlotAllocationRepository(session)
        self.logger = logger.bind(service="OptimizedSlotAllocator")
        
        # Scoring weights (must sum to 100)
        self.SCORING_WEIGHTS = {
            "slot_type_preference": 40,      # Bike slot > car slot for bikes
            "space_utilization": 25,         # Maximize overall occupancy
            "fragmentation_prevention": 20,  # Minimize unused partial spaces
            "user_preferences": 10,          # Distance, accessibility, etc.
            "future_availability": 5         # Consider upcoming patterns
        }
    
    async def allocate_slot(
        self, 
        request: SlotAllocationRequest,
        lot_id: UUID
    ) -> AllocationResult:
        """
        Main allocation method with strategy pattern.
        
        Args:
            request: Slot allocation request with vehicle type and time range
            lot_id: Parking lot ID
            
        Returns:
            AllocationResult with slot, type, and scoring details
            
        Raises:
            InsufficientSlotsError: No available slots found
            ValidationError: Invalid request parameters
        """
        try:
            self.logger.info(
                "Starting slot allocation",
                lot_id=lot_id,
                vehicle_type=request.vehicle_type.value,
                strategy=self.strategy.value
            )
            
            # Validate request
            self._validate_allocation_request(request)
            
            # Get available slots
            available_slots = await self._get_available_slots(lot_id, request)
            
            if not available_slots:
                raise InsufficientSlotsError(
                    f"No available slots for {request.vehicle_type.value} "
                    f"from {request.start_time} to {request.end_time}"
                )
            
            # Apply allocation strategy
            if self.strategy == AllocationStrategy.OPTIMAL:
                result = await self._optimal_allocation(available_slots, request)
            elif self.strategy == AllocationStrategy.BEST_FIT:
                result = await self._best_fit_allocation(available_slots, request)
            else:  # FIRST_FIT
                result = await self._first_fit_allocation(available_slots, request)
            
            self.logger.info(
                "Slot allocation successful",
                slot_id=result.slot.id,
                slot_number=result.slot.slot_number,
                allocation_type=result.allocation_type.value,
                confidence_score=result.confidence_score,
                reason=result.allocation_reason
            )
            
            return result
            
        except (InsufficientSlotsError, ValidationError):
            raise
        except Exception as e:
            self.logger.error("Slot allocation failed", error=str(e))
            raise BusinessLogicError(f"Failed to allocate slot: {str(e)}")
    
    async def _optimal_allocation(
        self, 
        slots: List[ParkingSlot], 
        request: SlotAllocationRequest
    ) -> AllocationResult:
        """
        Optimal allocation considering:
        1. Space utilization efficiency
        2. Future booking optimization  
        3. User preference matching
        4. Fragmentation minimization
        """
        if request.vehicle_type == VehicleType.CAR:
            return await self._allocate_car_optimal(slots, request)
        else:
            return await self._allocate_bike_optimal(slots, request)
    
    async def _allocate_bike_optimal(
        self,
        slots: List[ParkingSlot],
        request: SlotAllocationRequest
    ) -> AllocationResult:
        """
        Bike allocation optimization following the business rule:
        1. Dedicated bike slots (highest priority)
        2. Car slots with existing bike (optimal space sharing)
        3. Empty car slots (create new shared space)
        4. Score-based selection within each category
        """
        # Score each slot based on multiple factors
        slot_scores = []
        
        for slot in slots:
            score = await self._calculate_slot_score(slot, request)
            slot_scores.append((slot, score))
        
        # Sort by score (highest first)
        slot_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Try allocation in order of preference
        for slot, score in slot_scores:
            allocation_result = await self._attempt_bike_allocation(slot, request)
            if allocation_result:
                allocation_result.confidence_score = score
                return allocation_result
        
        raise InsufficientSlotsError("Unable to allocate bike slot")
    
    async def _allocate_car_optimal(
        self,
        slots: List[ParkingSlot],
        request: SlotAllocationRequest
    ) -> AllocationResult:
        """
        Car allocation optimization.
        Cars can only use dedicated car slots (no sharing).
        """
        car_slots = [s for s in slots if s.slot_type == VehicleType.CAR.value]
        
        if not car_slots:
            raise InsufficientSlotsError("No available car slots")
        
        # Score car slots
        slot_scores = []
        for slot in car_slots:
            score = await self._calculate_slot_score(slot, request)
            slot_scores.append((slot, score))
        
        # Sort by score and select best
        slot_scores.sort(key=lambda x: x[1], reverse=True)
        best_slot, best_score = slot_scores[0]
        
        return AllocationResult(
            slot=best_slot,
            allocation_type=AllocationType.FULL,
            space_designation=None,
            confidence_score=best_score,
            allocation_reason="Optimal car slot allocation"
        )
    
    async def _calculate_slot_score(
        self, 
        slot: ParkingSlot, 
        request: SlotAllocationRequest
    ) -> float:
        """
        Multi-factor scoring algorithm (100-point scale):
        - Slot type preference (40% weight)
        - Space utilization efficiency (25% weight)
        - Fragmentation impact (20% weight)
        - User preferences (10% weight)
        - Future availability impact (5% weight)
        """
        base_score = 0.0
        
        # Factor 1: Slot type preference (40% weight)
        type_score = await self._calculate_type_preference_score(slot, request)
        base_score += type_score * (self.SCORING_WEIGHTS["slot_type_preference"] / 100)
        
        # Factor 2: Space utilization efficiency (25% weight)
        utilization_score = await self._calculate_utilization_score(slot, request)
        base_score += utilization_score * (self.SCORING_WEIGHTS["space_utilization"] / 100)
        
        # Factor 3: Fragmentation impact (20% weight)
        fragmentation_score = await self._calculate_fragmentation_score(slot, request)
        base_score += fragmentation_score * (self.SCORING_WEIGHTS["fragmentation_prevention"] / 100)
        
        # Factor 4: User preferences (10% weight)
        if request.user_preferences:
            preference_score = await self._calculate_preference_score(slot, request.user_preferences)
            base_score += preference_score * (self.SCORING_WEIGHTS["user_preferences"] / 100)
        
        # Factor 5: Future availability impact (5% weight)
        future_score = await self._calculate_future_impact_score(slot, request)
        base_score += future_score * (self.SCORING_WEIGHTS["future_availability"] / 100)
        
        return min(base_score, 100.0)  # Cap at 100
    
    async def _calculate_type_preference_score(
        self, 
        slot: ParkingSlot, 
        request: SlotAllocationRequest
    ) -> float:
        """Calculate slot type preference score (0-100)."""
        if slot.slot_type == request.vehicle_type.value:
            return 100.0  # Perfect match
        elif (slot.slot_type == VehicleType.CAR.value and 
              request.vehicle_type == VehicleType.BIKE):
            # Check existing bike allocations in this car slot
            existing_bikes = await self._count_bikes_in_car_slot(
                slot.id, request.start_time, request.end_time
            )
            if existing_bikes == 0:
                return 60.0  # New shared space
            elif existing_bikes == 1:
                return 85.0  # Optimal space sharing (2nd bike)
            # existing_bikes == 2 would not be in available slots
        
        return 0.0  # No compatibility
    
    async def _calculate_utilization_score(
        self, 
        slot: ParkingSlot, 
        request: SlotAllocationRequest
    ) -> float:
        """Calculate space utilization efficiency score (0-100)."""
        # Higher score for better space utilization
        if (slot.slot_type == VehicleType.CAR.value and 
            request.vehicle_type == VehicleType.BIKE):
            # Bike using car slot - good utilization
            return 80.0
        elif slot.slot_type == request.vehicle_type.value:
            # Perfect type match - excellent utilization
            return 100.0
        
        return 50.0  # Default score
    
    async def _calculate_fragmentation_score(
        self, 
        slot: ParkingSlot, 
        request: SlotAllocationRequest
    ) -> float:
        """Calculate fragmentation prevention score (0-100)."""
        # Higher score for choices that minimize fragmentation
        if (slot.slot_type == VehicleType.CAR.value and 
            request.vehicle_type == VehicleType.BIKE):
            existing_bikes = await self._count_bikes_in_car_slot(
                slot.id, request.start_time, request.end_time
            )
            if existing_bikes == 1:
                return 100.0  # Completing a car slot (no fragmentation)
            else:
                return 70.0   # Creating new partial allocation
        
        return 90.0  # Default high score for dedicated slots
    
    async def _calculate_preference_score(
        self, 
        slot: ParkingSlot, 
        preferences: Dict[str, Any]
    ) -> float:
        """Calculate user preference matching score (0-100)."""
        # TODO: Implement based on user preferences like:
        # - Distance from entrance
        # - Accessibility requirements
        # - Previous usage patterns
        return 75.0  # Default score
    
    async def _calculate_future_impact_score(
        self, 
        slot: ParkingSlot, 
        request: SlotAllocationRequest
    ) -> float:
        """Calculate future availability impact score (0-100)."""
        # TODO: Implement based on historical data and upcoming bookings
        # Higher score for allocations that don't impact future availability
        return 80.0  # Default score
    
    async def _attempt_bike_allocation(
        self, 
        slot: ParkingSlot, 
        request: SlotAllocationRequest
    ) -> Optional[AllocationResult]:
        """
        Attempt to allocate a bike to the given slot.
        Handles both dedicated bike slots and car slots.
        """
        if slot.slot_type == VehicleType.BIKE.value:
            # Dedicated bike slot
            return AllocationResult(
                slot=slot,
                allocation_type=AllocationType.FULL,
                space_designation=None,
                confidence_score=0.0,  # Will be set by caller
                allocation_reason="Dedicated bike slot allocation"
            )
        
        elif slot.slot_type == VehicleType.CAR.value:
            # Car slot - check bike capacity
            existing_bikes = await self._count_bikes_in_car_slot(
                slot.id, request.start_time, request.end_time
            )
            
            if existing_bikes == 0:
                # Empty car slot - allocate first bike
                return AllocationResult(
                    slot=slot,
                    allocation_type=AllocationType.PARTIAL,
                    space_designation="left_half",
                    confidence_score=0.0,
                    allocation_reason="First bike in car slot"
                )
            elif existing_bikes == 1:
                # Car slot with one bike - allocate second bike
                existing_space = await self._get_existing_bike_space(
                    slot.id, request.start_time, request.end_time
                )
                new_space = "right_half" if existing_space == "left_half" else "left_half"
                
                return AllocationResult(
                    slot=slot,
                    allocation_type=AllocationType.PARTIAL,
                    space_designation=new_space,
                    confidence_score=0.0,
                    allocation_reason="Second bike in car slot (optimal sharing)"
                )
            # existing_bikes >= 2: slot is full (shouldn't be in available list)
        
        return None  # Cannot allocate
    
    async def _first_fit_allocation(
        self, 
        slots: List[ParkingSlot], 
        request: SlotAllocationRequest
    ) -> AllocationResult:
        """Simple first-fit allocation strategy."""
        for slot in slots:
            result = await self._attempt_bike_allocation(slot, request) if request.vehicle_type == VehicleType.BIKE else self._attempt_car_allocation(slot, request)
            if result:
                result.confidence_score = 50.0  # Default score for first-fit
                result.allocation_reason = "First-fit allocation"
                return result
        
        raise InsufficientSlotsError("No suitable slots found")
    
    async def _best_fit_allocation(
        self, 
        slots: List[ParkingSlot], 
        request: SlotAllocationRequest
    ) -> AllocationResult:
        """Best-fit allocation strategy (simplified scoring)."""
        return await self._optimal_allocation(slots, request)
    
    def _attempt_car_allocation(
        self, 
        slot: ParkingSlot, 
        request: SlotAllocationRequest
    ) -> Optional[AllocationResult]:
        """Attempt to allocate a car to the given slot."""
        if slot.slot_type == VehicleType.CAR.value:
            return AllocationResult(
                slot=slot,
                allocation_type=AllocationType.FULL,
                space_designation=None,
                confidence_score=0.0,
                allocation_reason="Car slot allocation"
            )
        return None
    
    async def _get_available_slots(
        self, 
        lot_id: UUID, 
        request: SlotAllocationRequest
    ) -> List[ParkingSlot]:
        """Get available slots for the allocation request."""
        return await self.slot_repository.get_available_slots(
            lot_id=lot_id,
            vehicle_type=request.vehicle_type,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=50  # Get more slots for better optimization
        )
    
    async def _count_bikes_in_car_slot(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> int:
        """Count existing bike allocations in a car slot for the given time period."""
        return await self.allocation_repository.count_bikes_in_car_slot(
            slot_id, start_time, end_time
        )
    
    async def _get_existing_bike_space(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> str:
        """Get the space designation of existing bike in car slot."""
        space = await self.allocation_repository.get_existing_bike_space(
            slot_id, start_time, end_time
        )
        return space or "left_half"  # Default if no existing space found
    
    def _validate_allocation_request(self, request: SlotAllocationRequest) -> None:
        """Validate allocation request parameters."""
        if request.start_time >= request.end_time:
            raise ValidationError("Start time must be before end time")
        
        if request.start_time < datetime.now(timezone.utc):
            raise ValidationError("Start time cannot be in the past")
        
        if not isinstance(request.vehicle_type, VehicleType):
            raise ValidationError("Invalid vehicle type")
        
        if request.priority_level < 0 or request.priority_level > 10:
            raise ValidationError("Priority level must be between 0 and 10")
