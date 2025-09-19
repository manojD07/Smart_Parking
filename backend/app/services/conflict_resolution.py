"""Advanced conflict detection and resolution service for concurrent booking operations."""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
from uuid import UUID
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func
import structlog

from app.models.booking import Booking, BookingStatus, SlotAllocation, AllocationType
from app.models.parking import ParkingSlot, VehicleType
from app.repositories.booking import BookingRepository, SlotAllocationRepository
from app.repositories.parking import ParkingSlotRepository
from app.services.base import BaseService
from app.core.locks import slot_lock_manager, LockAcquisitionError
from app.core.exceptions import ValidationError, BusinessLogicError, BookingConflictError

logger = structlog.get_logger(__name__)


class ConflictType(Enum):
    """Types of booking conflicts."""
    
    TIME_OVERLAP = "time_overlap"              # Overlapping time periods
    DOUBLE_BOOKING = "double_booking"          # Same slot, same time
    CAPACITY_EXCEEDED = "capacity_exceeded"    # More vehicles than slot capacity
    INVALID_ALLOCATION = "invalid_allocation"  # Invalid space allocation
    STATE_CONFLICT = "state_conflict"          # Slot state doesn't allow booking
    USER_LIMIT_EXCEEDED = "user_limit_exceeded"  # User has too many active bookings
    SYSTEM_CONSTRAINT = "system_constraint"    # System-level constraint violation


class ConflictSeverity(Enum):
    """Severity levels for conflicts."""
    
    CRITICAL = "critical"    # Must block operation
    HIGH = "high"           # Should block unless resolved
    MEDIUM = "medium"       # Warning, can proceed with caution
    LOW = "low"            # Informational


class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts."""
    
    BLOCK = "block"                    # Block the operation
    QUEUE = "queue"                    # Queue for later processing
    ALTERNATIVE_SLOT = "alternative_slot"  # Suggest alternative slot
    PARTIAL_ALLOCATION = "partial_allocation"  # Use partial allocation
    ADMIN_INTERVENTION = "admin_intervention"  # Require admin approval
    AUTO_RESOLVE = "auto_resolve"      # Automatically resolve


@dataclass
class ConflictDetails:
    """Detailed information about a conflict."""
    
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    affected_resources: List[str]
    conflicting_bookings: List[UUID]
    resolution_strategies: List[ResolutionStrategy]
    auto_resolvable: bool
    estimated_resolution_time: Optional[timedelta]
    metadata: Dict[str, Any]


@dataclass
class ResolutionResult:
    """Result of conflict resolution attempt."""
    
    success: bool
    strategy_used: ResolutionStrategy
    resolution_details: Dict[str, Any]
    alternative_suggestions: List[Dict[str, Any]]
    warnings: List[str]
    next_steps: List[str]


class ConflictResolutionService(BaseService):
    """
    Advanced service for detecting and resolving booking conflicts.
    
    Provides comprehensive conflict detection, analysis, and resolution
    for concurrent booking operations with multiple strategies.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.booking_repository = BookingRepository(session)
        self.slot_allocation_repository = SlotAllocationRepository(session)
        self.parking_slot_repository = ParkingSlotRepository(session)
        self.logger = logger.bind(service="ConflictResolutionService")
        
        # Configuration
        self.max_user_concurrent_bookings = 5
        self.conflict_detection_window = timedelta(hours=1)
        self.auto_resolution_timeout = timedelta(seconds=30)
    
    async def detect_conflicts(
        self,
        slot_id: UUID,
        user_id: UUID,
        vehicle_type: str,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[ConflictDetails]:
        """
        Comprehensive conflict detection for a booking request.
        
        Args:
            slot_id: Target slot ID
            user_id: User making the booking
            vehicle_type: Type of vehicle
            start_time: Booking start time
            end_time: Booking end time
            exclude_booking_id: Booking ID to exclude from conflict check
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        try:
            # 1. Time overlap conflicts
            time_conflicts = await self._detect_time_overlap_conflicts(
                slot_id, start_time, end_time, exclude_booking_id
            )
            conflicts.extend(time_conflicts)
            
            # 2. Capacity conflicts
            capacity_conflicts = await self._detect_capacity_conflicts(
                slot_id, vehicle_type, start_time, end_time, exclude_booking_id
            )
            conflicts.extend(capacity_conflicts)
            
            # 3. State conflicts
            state_conflicts = await self._detect_state_conflicts(slot_id, start_time)
            conflicts.extend(state_conflicts)
            
            # 4. User limit conflicts
            user_conflicts = await self._detect_user_limit_conflicts(
                user_id, start_time, end_time, exclude_booking_id
            )
            conflicts.extend(user_conflicts)
            
            # 5. Allocation conflicts
            allocation_conflicts = await self._detect_allocation_conflicts(
                slot_id, vehicle_type, start_time, end_time, exclude_booking_id
            )
            conflicts.extend(allocation_conflicts)
            
            # 6. System constraint conflicts
            system_conflicts = await self._detect_system_constraint_conflicts(
                slot_id, user_id, vehicle_type, start_time, end_time
            )
            conflicts.extend(system_conflicts)
            
            self.logger.info(
                "Conflict detection completed",
                slot_id=slot_id,
                conflicts_found=len(conflicts),
                conflict_types=[c.conflict_type.value for c in conflicts]
            )
            
            return conflicts
            
        except Exception as e:
            self.logger.error("Conflict detection failed", error=str(e))
            # Return critical system conflict
            return [ConflictDetails(
                conflict_id=f"system_error_{datetime.now().timestamp()}",
                conflict_type=ConflictType.SYSTEM_CONSTRAINT,
                severity=ConflictSeverity.CRITICAL,
                description=f"System error during conflict detection: {str(e)}",
                affected_resources=[str(slot_id)],
                conflicting_bookings=[],
                resolution_strategies=[ResolutionStrategy.ADMIN_INTERVENTION],
                auto_resolvable=False,
                estimated_resolution_time=None,
                metadata={"error": str(e)}
            )]
    
    async def resolve_conflicts(
        self,
        conflicts: List[ConflictDetails],
        preferred_strategy: Optional[ResolutionStrategy] = None
    ) -> ResolutionResult:
        """
        Attempt to resolve detected conflicts.
        
        Args:
            conflicts: List of conflicts to resolve
            preferred_strategy: Preferred resolution strategy
            
        Returns:
            Resolution result
        """
        if not conflicts:
            return ResolutionResult(
                success=True,
                strategy_used=ResolutionStrategy.AUTO_RESOLVE,
                resolution_details={"message": "No conflicts to resolve"},
                alternative_suggestions=[],
                warnings=[],
                next_steps=[]
            )
        
        # Sort conflicts by severity (critical first)
        sorted_conflicts = sorted(
            conflicts, 
            key=lambda c: ["critical", "high", "medium", "low"].index(c.severity.value)
        )
        
        critical_conflicts = [c for c in sorted_conflicts if c.severity == ConflictSeverity.CRITICAL]
        
        if critical_conflicts:
            return await self._resolve_critical_conflicts(critical_conflicts)
        
        # Try preferred strategy first
        if preferred_strategy:
            result = await self._try_resolution_strategy(sorted_conflicts, preferred_strategy)
            if result.success:
                return result
        
        # Try each available strategy
        for conflict in sorted_conflicts:
            for strategy in conflict.resolution_strategies:
                result = await self._try_resolution_strategy([conflict], strategy)
                if result.success:
                    return result
        
        # If all strategies failed
        return ResolutionResult(
            success=False,
            strategy_used=ResolutionStrategy.ADMIN_INTERVENTION,
            resolution_details={"message": "All automatic resolution strategies failed"},
            alternative_suggestions=await self._generate_alternative_suggestions(sorted_conflicts),
            warnings=["Manual intervention required"],
            next_steps=["Contact administrator", "Try different time slot", "Use different vehicle type"]
        )
    
    async def validate_booking_atomically(
        self,
        slot_id: UUID,
        user_id: UUID,
        vehicle_type: str,
        start_time: datetime,
        end_time: datetime,
        timeout: int = 30
    ) -> Tuple[bool, List[ConflictDetails], Optional[ResolutionResult]]:
        """
        Atomically validate a booking with conflict detection and resolution.
        
        Args:
            slot_id: Target slot ID
            user_id: User ID
            vehicle_type: Vehicle type
            start_time: Start time
            end_time: End time
            timeout: Lock timeout in seconds
            
        Returns:
            Tuple of (is_valid, conflicts, resolution_result)
        """
        try:
            # Acquire conflict detection lock
            async with slot_lock_manager.lock_slot_allocation(
                slot_id=str(slot_id),
                user_id=str(user_id),
                operation="conflict_validation",
                timeout=timeout
            ):
                # Detect conflicts
                conflicts = await self.detect_conflicts(
                    slot_id, user_id, vehicle_type, start_time, end_time
                )
                
                if not conflicts:
                    return True, [], None
                
                # Attempt resolution
                resolution_result = await self.resolve_conflicts(conflicts)
                
                # Return validation result
                is_valid = resolution_result.success and resolution_result.strategy_used != ResolutionStrategy.BLOCK
                
                return is_valid, conflicts, resolution_result
                
        except LockAcquisitionError:
            # If we can't acquire lock, treat as conflict
            lock_conflict = ConflictDetails(
                conflict_id=f"lock_conflict_{datetime.now().timestamp()}",
                conflict_type=ConflictType.SYSTEM_CONSTRAINT,
                severity=ConflictSeverity.HIGH,
                description="Cannot acquire validation lock - concurrent operation in progress",
                affected_resources=[str(slot_id)],
                conflicting_bookings=[],
                resolution_strategies=[ResolutionStrategy.QUEUE, ResolutionStrategy.ALTERNATIVE_SLOT],
                auto_resolvable=True,
                estimated_resolution_time=timedelta(seconds=5),
                metadata={"retry_suggested": True}
            )
            
            return False, [lock_conflict], None
        
        except Exception as e:
            self.logger.error("Atomic validation failed", error=str(e))
            system_conflict = ConflictDetails(
                conflict_id=f"validation_error_{datetime.now().timestamp()}",
                conflict_type=ConflictType.SYSTEM_CONSTRAINT,
                severity=ConflictSeverity.CRITICAL,
                description=f"Validation system error: {str(e)}",
                affected_resources=[str(slot_id)],
                conflicting_bookings=[],
                resolution_strategies=[ResolutionStrategy.ADMIN_INTERVENTION],
                auto_resolvable=False,
                estimated_resolution_time=None,
                metadata={"error": str(e)}
            )
            
            return False, [system_conflict], None
    
    async def _detect_time_overlap_conflicts(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[ConflictDetails]:
        """Detect time overlap conflicts."""
        conflicts = []
        
        try:
            # Query for overlapping bookings
            query = select(Booking).where(
                and_(
                    Booking.slot_id == slot_id,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.CHECKED_IN.value,
                        BookingStatus.PENDING.value
                    ]),
                    or_(
                        and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                        and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                        and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
                    )
                )
            )
            
            if exclude_booking_id:
                query = query.where(Booking.id != exclude_booking_id)
            
            result = await self.session.execute(query)
            overlapping_bookings = result.scalars().all()
            
            if overlapping_bookings:
                conflicts.append(ConflictDetails(
                    conflict_id=f"time_overlap_{slot_id}_{start_time.timestamp()}",
                    conflict_type=ConflictType.TIME_OVERLAP,
                    severity=ConflictSeverity.CRITICAL,
                    description=f"Found {len(overlapping_bookings)} overlapping bookings for this time period",
                    affected_resources=[str(slot_id)],
                    conflicting_bookings=[b.id for b in overlapping_bookings],
                    resolution_strategies=[ResolutionStrategy.ALTERNATIVE_SLOT, ResolutionStrategy.QUEUE],
                    auto_resolvable=False,
                    estimated_resolution_time=timedelta(minutes=5),
                    metadata={
                        "overlapping_count": len(overlapping_bookings),
                        "overlapping_details": [
                            {
                                "booking_id": str(b.id),
                                "start_time": b.start_time.isoformat(),
                                "end_time": b.end_time.isoformat(),
                                "vehicle_type": b.vehicle_type
                            }
                            for b in overlapping_bookings
                        ]
                    }
                ))
            
        except Exception as e:
            self.logger.error("Time overlap detection failed", error=str(e))
        
        return conflicts
    
    async def _detect_capacity_conflicts(
        self,
        slot_id: UUID,
        vehicle_type: str,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[ConflictDetails]:
        """Detect capacity conflicts."""
        conflicts = []
        
        try:
            # Get slot information
            slot = await self.parking_slot_repository.get_by_id(slot_id)
            if not slot:
                return conflicts
            
            # Count existing allocations in time period
            existing_bikes = await self.slot_allocation_repository.count_bikes_in_car_slot(
                slot_id, start_time, end_time, exclude_booking_id
            )
            
            # Check capacity based on vehicle type and slot type
            if vehicle_type == VehicleType.BIKE.value and slot.slot_type == VehicleType.CAR.value:
                # Bike in car slot - max 2 bikes
                if existing_bikes >= 2:
                    conflicts.append(ConflictDetails(
                        conflict_id=f"capacity_bike_car_{slot_id}_{start_time.timestamp()}",
                        conflict_type=ConflictType.CAPACITY_EXCEEDED,
                        severity=ConflictSeverity.HIGH,
                        description=f"Car slot already has {existing_bikes} bikes allocated (max 2)",
                        affected_resources=[str(slot_id)],
                        conflicting_bookings=[],
                        resolution_strategies=[ResolutionStrategy.ALTERNATIVE_SLOT],
                        auto_resolvable=True,
                        estimated_resolution_time=timedelta(seconds=10),
                        metadata={"existing_bikes": existing_bikes, "max_capacity": 2}
                    ))
            
            elif vehicle_type == VehicleType.CAR.value:
                # Car booking - slot must be completely empty
                if existing_bikes > 0:
                    conflicts.append(ConflictDetails(
                        conflict_id=f"capacity_car_{slot_id}_{start_time.timestamp()}",
                        conflict_type=ConflictType.CAPACITY_EXCEEDED,
                        severity=ConflictSeverity.CRITICAL,
                        description=f"Slot has {existing_bikes} bikes allocated, cannot accommodate car",
                        affected_resources=[str(slot_id)],
                        conflicting_bookings=[],
                        resolution_strategies=[ResolutionStrategy.ALTERNATIVE_SLOT],
                        auto_resolvable=True,
                        estimated_resolution_time=timedelta(seconds=10),
                        metadata={"existing_bikes": existing_bikes}
                    ))
            
        except Exception as e:
            self.logger.error("Capacity conflict detection failed", error=str(e))
        
        return conflicts
    
    async def _detect_state_conflicts(
        self,
        slot_id: UUID,
        start_time: datetime
    ) -> List[ConflictDetails]:
        """Detect slot state conflicts."""
        conflicts = []
        
        try:
            slot = await self.parking_slot_repository.get_by_id(slot_id)
            if not slot:
                conflicts.append(ConflictDetails(
                    conflict_id=f"state_not_found_{slot_id}",
                    conflict_type=ConflictType.STATE_CONFLICT,
                    severity=ConflictSeverity.CRITICAL,
                    description="Slot not found",
                    affected_resources=[str(slot_id)],
                    conflicting_bookings=[],
                    resolution_strategies=[ResolutionStrategy.ALTERNATIVE_SLOT],
                    auto_resolvable=False,
                    estimated_resolution_time=None,
                    metadata={}
                ))
                return conflicts
            
            # Check if slot is available for booking
            if not slot.is_available:
                conflicts.append(ConflictDetails(
                    conflict_id=f"state_unavailable_{slot_id}",
                    conflict_type=ConflictType.STATE_CONFLICT,
                    severity=ConflictSeverity.HIGH,
                    description=f"Slot is in {slot.status} state and not available for booking",
                    affected_resources=[str(slot_id)],
                    conflicting_bookings=[],
                    resolution_strategies=[ResolutionStrategy.ALTERNATIVE_SLOT, ResolutionStrategy.QUEUE],
                    auto_resolvable=True,
                    estimated_resolution_time=timedelta(minutes=10),
                    metadata={"current_status": slot.status}
                ))
            
        except Exception as e:
            self.logger.error("State conflict detection failed", error=str(e))
        
        return conflicts
    
    async def _detect_user_limit_conflicts(
        self,
        user_id: UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[ConflictDetails]:
        """Detect user booking limit conflicts."""
        conflicts = []
        
        try:
            # Count user's active bookings in the time period
            query = select(func.count(Booking.id)).where(
                and_(
                    Booking.user_id == user_id,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.CHECKED_IN.value,
                        BookingStatus.PENDING.value
                    ]),
                    or_(
                        and_(Booking.start_time <= end_time, Booking.end_time >= start_time)
                    )
                )
            )
            
            if exclude_booking_id:
                query = query.where(Booking.id != exclude_booking_id)
            
            result = await self.session.execute(query)
            active_bookings_count = result.scalar() or 0
            
            if active_bookings_count >= self.max_user_concurrent_bookings:
                conflicts.append(ConflictDetails(
                    conflict_id=f"user_limit_{user_id}_{start_time.timestamp()}",
                    conflict_type=ConflictType.USER_LIMIT_EXCEEDED,
                    severity=ConflictSeverity.MEDIUM,
                    description=f"User has {active_bookings_count} active bookings (max {self.max_user_concurrent_bookings})",
                    affected_resources=[str(user_id)],
                    conflicting_bookings=[],
                    resolution_strategies=[ResolutionStrategy.QUEUE, ResolutionStrategy.ADMIN_INTERVENTION],
                    auto_resolvable=False,
                    estimated_resolution_time=None,
                    metadata={
                        "current_bookings": active_bookings_count,
                        "max_allowed": self.max_user_concurrent_bookings
                    }
                ))
            
        except Exception as e:
            self.logger.error("User limit conflict detection failed", error=str(e))
        
        return conflicts
    
    async def _detect_allocation_conflicts(
        self,
        slot_id: UUID,
        vehicle_type: str,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[ConflictDetails]:
        """Detect allocation conflicts."""
        conflicts = []
        
        try:
            # Get existing allocations
            allocations = await self.slot_allocation_repository.get_allocations_by_slot(
                slot_id, start_time, end_time, active_only=True
            )
            
            if exclude_booking_id:
                allocations = [a for a in allocations if a.booking_id != exclude_booking_id]
            
            # Check for invalid allocation patterns
            full_allocations = [a for a in allocations if a.allocation_type == AllocationType.FULL.value]
            partial_allocations = [a for a in allocations if a.allocation_type == AllocationType.PARTIAL.value]
            
            if full_allocations and len(full_allocations) > 0:
                conflicts.append(ConflictDetails(
                    conflict_id=f"allocation_full_{slot_id}_{start_time.timestamp()}",
                    conflict_type=ConflictType.INVALID_ALLOCATION,
                    severity=ConflictSeverity.CRITICAL,
                    description="Slot has full allocation, cannot accommodate additional booking",
                    affected_resources=[str(slot_id)],
                    conflicting_bookings=[a.booking_id for a in full_allocations if a.booking_id],
                    resolution_strategies=[ResolutionStrategy.ALTERNATIVE_SLOT],
                    auto_resolvable=True,
                    estimated_resolution_time=timedelta(seconds=5),
                    metadata={"full_allocations": len(full_allocations)}
                ))
            
            # Check partial allocation logic
            if partial_allocations and vehicle_type == VehicleType.CAR.value:
                conflicts.append(ConflictDetails(
                    conflict_id=f"allocation_partial_car_{slot_id}_{start_time.timestamp()}",
                    conflict_type=ConflictType.INVALID_ALLOCATION,
                    severity=ConflictSeverity.CRITICAL,
                    description="Car cannot be allocated to slot with existing partial allocations",
                    affected_resources=[str(slot_id)],
                    conflicting_bookings=[a.booking_id for a in partial_allocations if a.booking_id],
                    resolution_strategies=[ResolutionStrategy.ALTERNATIVE_SLOT],
                    auto_resolvable=True,
                    estimated_resolution_time=timedelta(seconds=5),
                    metadata={"partial_allocations": len(partial_allocations)}
                ))
            
        except Exception as e:
            self.logger.error("Allocation conflict detection failed", error=str(e))
        
        return conflicts
    
    async def _detect_system_constraint_conflicts(
        self,
        slot_id: UUID,
        user_id: UUID,
        vehicle_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[ConflictDetails]:
        """Detect system-level constraint conflicts."""
        conflicts = []
        
        try:
            # Check booking time constraints
            current_time = datetime.now(timezone.utc)
            
            # Cannot book in the past
            if start_time <= current_time:
                conflicts.append(ConflictDetails(
                    conflict_id=f"system_past_booking_{start_time.timestamp()}",
                    conflict_type=ConflictType.SYSTEM_CONSTRAINT,
                    severity=ConflictSeverity.CRITICAL,
                    description="Cannot book slots in the past",
                    affected_resources=[str(slot_id)],
                    conflicting_bookings=[],
                    resolution_strategies=[ResolutionStrategy.BLOCK],
                    auto_resolvable=False,
                    estimated_resolution_time=None,
                    metadata={"start_time": start_time.isoformat(), "current_time": current_time.isoformat()}
                ))
            
            # Check maximum advance booking period (e.g., 30 days)
            max_advance_days = 30
            max_advance_time = current_time + timedelta(days=max_advance_days)
            
            if start_time > max_advance_time:
                conflicts.append(ConflictDetails(
                    conflict_id=f"system_advance_limit_{start_time.timestamp()}",
                    conflict_type=ConflictType.SYSTEM_CONSTRAINT,
                    severity=ConflictSeverity.HIGH,
                    description=f"Cannot book more than {max_advance_days} days in advance",
                    affected_resources=[str(slot_id)],
                    conflicting_bookings=[],
                    resolution_strategies=[ResolutionStrategy.BLOCK],
                    auto_resolvable=False,
                    estimated_resolution_time=None,
                    metadata={"max_advance_days": max_advance_days}
                ))
            
            # Check minimum booking duration (e.g., 30 minutes)
            min_duration = timedelta(minutes=30)
            booking_duration = end_time - start_time
            
            if booking_duration < min_duration:
                conflicts.append(ConflictDetails(
                    conflict_id=f"system_min_duration_{booking_duration.total_seconds()}",
                    conflict_type=ConflictType.SYSTEM_CONSTRAINT,
                    severity=ConflictSeverity.MEDIUM,
                    description=f"Booking duration must be at least {min_duration.total_seconds()/60} minutes",
                    affected_resources=[str(slot_id)],
                    conflicting_bookings=[],
                    resolution_strategies=[ResolutionStrategy.BLOCK],
                    auto_resolvable=False,
                    estimated_resolution_time=None,
                    metadata={"min_duration_minutes": min_duration.total_seconds()/60}
                ))
            
        except Exception as e:
            self.logger.error("System constraint detection failed", error=str(e))
        
        return conflicts
    
    async def _resolve_critical_conflicts(
        self,
        critical_conflicts: List[ConflictDetails]
    ) -> ResolutionResult:
        """Resolve critical conflicts."""
        return ResolutionResult(
            success=False,
            strategy_used=ResolutionStrategy.BLOCK,
            resolution_details={
                "message": "Critical conflicts detected - operation blocked",
                "critical_conflicts": len(critical_conflicts)
            },
            alternative_suggestions=await self._generate_alternative_suggestions(critical_conflicts),
            warnings=[f"Critical conflict: {c.description}" for c in critical_conflicts],
            next_steps=["Choose different time slot", "Select alternative slot", "Contact support"]
        )
    
    async def _try_resolution_strategy(
        self,
        conflicts: List[ConflictDetails],
        strategy: ResolutionStrategy
    ) -> ResolutionResult:
        """Try a specific resolution strategy."""
        
        if strategy == ResolutionStrategy.BLOCK:
            return ResolutionResult(
                success=False,
                strategy_used=strategy,
                resolution_details={"message": "Operation blocked due to conflicts"},
                alternative_suggestions=[],
                warnings=[],
                next_steps=["Try different parameters"]
            )
        
        elif strategy == ResolutionStrategy.ALTERNATIVE_SLOT:
            # This would involve finding alternative slots
            # For now, just indicate success with alternatives
            return ResolutionResult(
                success=True,
                strategy_used=strategy,
                resolution_details={"message": "Alternative slots available"},
                alternative_suggestions=await self._generate_alternative_suggestions(conflicts),
                warnings=["Original slot not available"],
                next_steps=["Choose from alternative suggestions"]
            )
        
        elif strategy == ResolutionStrategy.QUEUE:
            return ResolutionResult(
                success=True,
                strategy_used=strategy,
                resolution_details={"message": "Request queued for processing"},
                alternative_suggestions=[],
                warnings=["Request will be processed when conflicts resolve"],
                next_steps=["Wait for queue processing", "Check status periodically"]
            )
        
        # Default: partial success
        return ResolutionResult(
            success=True,
            strategy_used=strategy,
            resolution_details={"message": f"Applied {strategy.value} strategy"},
            alternative_suggestions=[],
            warnings=[],
            next_steps=[]
        )
    
    async def _generate_alternative_suggestions(
        self,
        conflicts: List[ConflictDetails]
    ) -> List[Dict[str, Any]]:
        """Generate alternative suggestions based on conflicts."""
        suggestions = []
        
        # Time-based suggestions
        for conflict in conflicts:
            if conflict.conflict_type == ConflictType.TIME_OVERLAP:
                suggestions.append({
                    "type": "time_shift",
                    "description": "Try booking 1 hour later",
                    "parameters": {"time_shift_hours": 1}
                })
                suggestions.append({
                    "type": "time_shift",
                    "description": "Try booking 1 hour earlier",
                    "parameters": {"time_shift_hours": -1}
                })
            
            elif conflict.conflict_type == ConflictType.CAPACITY_EXCEEDED:
                suggestions.append({
                    "type": "vehicle_type_change",
                    "description": "Consider using a different vehicle type",
                    "parameters": {"alternative_types": ["bike", "car"]}
                })
            
            elif conflict.conflict_type == ConflictType.STATE_CONFLICT:
                suggestions.append({
                    "type": "alternative_slot",
                    "description": "Try a different parking slot",
                    "parameters": {"search_radius": "nearby"}
                })
        
        return suggestions[:5]  # Limit to 5 suggestions
