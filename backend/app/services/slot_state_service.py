"""Service for managing slot state transitions and lifecycle."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.slot_state_machine import (
    SlotStateMachine, SlotEvent, SlotStateMachineFactory,
    InvalidStateTransitionError, StateTransitionError
)
from app.models.parking import ParkingSlot, SlotStatus
from app.repositories.parking import ParkingSlotRepository
from app.services.base import BaseService
from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError

logger = structlog.get_logger(__name__)


class SlotStateService(BaseService):
    """
    Service for managing parking slot state transitions and lifecycle.
    
    Provides high-level interface for:
    - State transition management
    - Business rule validation
    - State history tracking
    - Batch state operations
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.slot_repository = ParkingSlotRepository(session)
        self.logger = logger.bind(service="SlotStateService")
        
        # Cache for active state machines
        self._state_machines: Dict[UUID, SlotStateMachine] = {}
    
    async def get_slot_state_machine(self, slot_id: UUID) -> SlotStateMachine:
        """
        Get or create state machine for a slot.
        
        Args:
            slot_id: Slot ID
            
        Returns:
            SlotStateMachine instance
        """
        # Check cache first
        if slot_id in self._state_machines:
            return self._state_machines[slot_id]
        
        # Get slot from database
        slot = await self.slot_repository.get_by_id(slot_id)
        if not slot:
            raise NotFoundError(f"Slot {slot_id} not found")
        
        # Create state machine
        state_machine = SlotStateMachineFactory.create_for_slot(
            slot_id=slot_id,
            current_status=SlotStatus(slot.status)
        )
        
        # Cache it
        self._state_machines[slot_id] = state_machine
        
        return state_machine
    
    async def transition_slot(
        self,
        slot_id: UUID,
        event: SlotEvent,
        context: Optional[Dict[str, Any]] = None,
        triggered_by: Optional[str] = None
    ) -> bool:
        """
        Execute a state transition for a slot.
        
        Args:
            slot_id: Slot ID
            event: Event to trigger
            context: Additional context
            triggered_by: Who triggered the transition
            
        Returns:
            True if transition was successful
        """
        try:
            # Get state machine
            state_machine = await self.get_slot_state_machine(slot_id)
            
            # Validate business rules
            if context and not state_machine.validate_business_rules(event, context):
                raise ValidationError(f"Business rules validation failed for {event.value}")
            
            # Execute transition
            success = state_machine.transition(
                event=event,
                context=context,
                triggered_by=triggered_by
            )
            
            if success:
                # Update database
                await self._update_slot_status_in_db(slot_id, state_machine.current_state)
                
                # Execute side effects
                await self._execute_side_effects(
                    slot_id, event, state_machine.get_transition_info(event), context
                )
            
            return success
            
        except (InvalidStateTransitionError, StateTransitionError) as e:
            self.logger.error("State transition failed", slot_id=slot_id, error=str(e))
            raise BusinessLogicError(str(e))
    
    async def reserve_slot(
        self,
        slot_id: UUID,
        booking_id: UUID,
        user_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Reserve a slot for a booking.
        
        Args:
            slot_id: Slot to reserve
            booking_id: Booking ID
            user_id: User making the booking
            start_time: Booking start time
            end_time: Booking end time
            
        Returns:
            True if reservation was successful
        """
        context = {
            "booking_id": str(booking_id),
            "user_id": str(user_id),
            "booking_start_time": start_time.isoformat(),
            "booking_end_time": end_time.isoformat(),
            "operation": "reserve"
        }
        
        return await self.transition_slot(
            slot_id=slot_id,
            event=SlotEvent.RESERVE,
            context=context,
            triggered_by=f"user:{user_id}"
        )
    
    async def occupy_slot(
        self,
        slot_id: UUID,
        booking_id: UUID,
        user_id: UUID,
        check_in_time: Optional[datetime] = None
    ) -> bool:
        """
        Mark slot as occupied (check-in).
        
        Args:
            slot_id: Slot to occupy
            booking_id: Booking ID
            user_id: User checking in
            check_in_time: Check-in time (defaults to now)
            
        Returns:
            True if occupation was successful
        """
        if check_in_time is None:
            check_in_time = datetime.now(timezone.utc)
        
        context = {
            "booking_id": str(booking_id),
            "user_id": str(user_id),
            "check_in_time": check_in_time.isoformat(),
            "operation": "occupy"
        }
        
        return await self.transition_slot(
            slot_id=slot_id,
            event=SlotEvent.OCCUPY,
            context=context,
            triggered_by=f"user:{user_id}"
        )
    
    async def vacate_slot(
        self,
        slot_id: UUID,
        booking_id: UUID,
        user_id: UUID,
        check_out_time: Optional[datetime] = None
    ) -> bool:
        """
        Mark slot as vacated (check-out).
        
        Args:
            slot_id: Slot to vacate
            booking_id: Booking ID
            user_id: User checking out
            check_out_time: Check-out time (defaults to now)
            
        Returns:
            True if vacation was successful
        """
        if check_out_time is None:
            check_out_time = datetime.now(timezone.utc)
        
        context = {
            "booking_id": str(booking_id),
            "user_id": str(user_id),
            "check_out_time": check_out_time.isoformat(),
            "operation": "vacate"
        }
        
        return await self.transition_slot(
            slot_id=slot_id,
            event=SlotEvent.VACATE,
            context=context,
            triggered_by=f"user:{user_id}"
        )
    
    async def release_slot(
        self,
        slot_id: UUID,
        booking_id: Optional[UUID] = None,
        reason: str = "booking_cancelled"
    ) -> bool:
        """
        Release a slot (cancellation or expiry).
        
        Args:
            slot_id: Slot to release
            booking_id: Booking ID (if applicable)
            reason: Reason for release
            
        Returns:
            True if release was successful
        """
        context = {
            "booking_id": str(booking_id) if booking_id else None,
            "reason": reason,
            "operation": "release"
        }
        
        return await self.transition_slot(
            slot_id=slot_id,
            event=SlotEvent.RELEASE,
            context=context,
            triggered_by="system"
        )
    
    async def start_maintenance(
        self,
        slot_id: UUID,
        admin_id: UUID,
        maintenance_reason: str,
        estimated_duration: Optional[timedelta] = None
    ) -> bool:
        """
        Start maintenance on a slot.
        
        Args:
            slot_id: Slot to maintain
            admin_id: Admin starting maintenance
            maintenance_reason: Reason for maintenance
            estimated_duration: Estimated maintenance duration
            
        Returns:
            True if maintenance started successfully
        """
        context = {
            "admin_id": str(admin_id),
            "maintenance_reason": maintenance_reason,
            "estimated_duration": estimated_duration.total_seconds() if estimated_duration else None,
            "operation": "start_maintenance"
        }
        
        return await self.transition_slot(
            slot_id=slot_id,
            event=SlotEvent.START_MAINTENANCE,
            context=context,
            triggered_by=f"admin:{admin_id}"
        )
    
    async def end_maintenance(
        self,
        slot_id: UUID,
        admin_id: UUID,
        maintenance_notes: Optional[str] = None
    ) -> bool:
        """
        End maintenance on a slot.
        
        Args:
            slot_id: Slot to complete maintenance
            admin_id: Admin ending maintenance
            maintenance_notes: Notes about completed work
            
        Returns:
            True if maintenance ended successfully
        """
        context = {
            "admin_id": str(admin_id),
            "maintenance_notes": maintenance_notes,
            "operation": "end_maintenance"
        }
        
        return await self.transition_slot(
            slot_id=slot_id,
            event=SlotEvent.END_MAINTENANCE,
            context=context,
            triggered_by=f"admin:{admin_id}"
        )
    
    async def force_release_slot(
        self,
        slot_id: UUID,
        admin_id: UUID,
        reason: str
    ) -> bool:
        """
        Force release a slot (admin override).
        
        Args:
            slot_id: Slot to force release
            admin_id: Admin performing override
            reason: Reason for force release
            
        Returns:
            True if force release was successful
        """
        context = {
            "admin_id": str(admin_id),
            "reason": reason,
            "operation": "force_release"
        }
        
        return await self.transition_slot(
            slot_id=slot_id,
            event=SlotEvent.FORCE_RELEASE,
            context=context,
            triggered_by=f"admin:{admin_id}"
        )
    
    async def get_slot_state_info(self, slot_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive state information for a slot.
        
        Args:
            slot_id: Slot ID
            
        Returns:
            Dict with state information
        """
        try:
            state_machine = await self.get_slot_state_machine(slot_id)
            return state_machine.get_state_summary()
        except Exception as e:
            self.logger.error("Failed to get slot state info", slot_id=slot_id, error=str(e))
            raise BusinessLogicError("Failed to get slot state information")
    
    async def get_slots_requiring_attention(self, lot_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """
        Get slots that require admin attention.
        
        Args:
            lot_id: Optional lot ID to filter by
            
        Returns:
            List of slots requiring attention
        """
        try:
            # Get slots in maintenance or inactive status
            attention_states = [SlotStatus.MAINTENANCE, SlotStatus.INACTIVE]
            slots_needing_attention = []
            
            # This would typically involve a repository query
            # For now, return empty list as placeholder
            # TODO: Implement repository method for slots by status
            
            return slots_needing_attention
            
        except Exception as e:
            self.logger.error("Failed to get slots requiring attention", error=str(e))
            return []
    
    async def expire_reservations(self, expiry_threshold: timedelta = timedelta(minutes=15)) -> int:
        """
        Expire reservations that have exceeded the threshold.
        
        Args:
            expiry_threshold: Time threshold for expiration
            
        Returns:
            Number of reservations expired
        """
        try:
            expired_count = 0
            
            # Get all reserved slots
            # This would typically involve a repository query
            # TODO: Implement repository method for reserved slots
            
            self.logger.info("Expired reservations", count=expired_count)
            return expired_count
            
        except Exception as e:
            self.logger.error("Failed to expire reservations", error=str(e))
            return 0
    
    async def batch_state_transition(
        self,
        transitions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute multiple state transitions in batch.
        
        Args:
            transitions: List of transition specifications
            
        Returns:
            Results summary
        """
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for transition in transitions:
            try:
                slot_id = UUID(transition["slot_id"])
                event = SlotEvent(transition["event"])
                context = transition.get("context", {})
                triggered_by = transition.get("triggered_by", "batch_operation")
                
                success = await self.transition_slot(
                    slot_id=slot_id,
                    event=event,
                    context=context,
                    triggered_by=triggered_by
                )
                
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "slot_id": transition.get("slot_id"),
                    "event": transition.get("event"),
                    "error": str(e)
                })
        
        return results
    
    async def _update_slot_status_in_db(self, slot_id: UUID, new_status: SlotStatus) -> None:
        """Update slot status in database."""
        try:
            slot = await self.slot_repository.get_by_id(slot_id)
            if slot:
                slot.status = new_status.value
                
                # Update related flags based on status
                if new_status == SlotStatus.AVAILABLE:
                    slot.is_occupied = False
                    slot.is_reserved = False
                elif new_status == SlotStatus.RESERVED:
                    slot.is_reserved = True
                    slot.is_occupied = False
                elif new_status == SlotStatus.OCCUPIED:
                    slot.is_occupied = True
                    slot.is_reserved = False
                
                self.logger.debug(
                    "Updated slot status in database",
                    slot_id=slot_id,
                    new_status=new_status.value
                )
                
        except Exception as e:
            self.logger.error("Failed to update slot status in database", error=str(e))
            raise
    
    async def _execute_side_effects(
        self,
        slot_id: UUID,
        event: SlotEvent,
        transition: Optional[Any],
        context: Optional[Dict[str, Any]]
    ) -> None:
        """Execute side effects for a state transition."""
        if not transition or not transition.side_effects:
            return
        
        for side_effect in transition.side_effects:
            try:
                await self._execute_single_side_effect(slot_id, side_effect, context)
            except Exception as e:
                self.logger.warning(
                    "Side effect execution failed",
                    slot_id=slot_id,
                    side_effect=side_effect,
                    error=str(e)
                )
    
    async def _execute_single_side_effect(
        self,
        slot_id: UUID,
        side_effect: str,
        context: Optional[Dict[str, Any]]
    ) -> None:
        """Execute a single side effect."""
        
        if side_effect == "set_reservation_timer":
            # TODO: Set timer for reservation expiry
            pass
        elif side_effect == "notify_allocation":
            # TODO: Send allocation notification
            pass
        elif side_effect == "start_billing":
            # TODO: Start billing process
            pass
        elif side_effect == "stop_billing":
            # TODO: Stop billing and calculate final amount
            pass
        elif side_effect == "clear_reservation_timer":
            # TODO: Clear reservation timer
            pass
        elif side_effect == "notify_maintenance":
            # TODO: Notify maintenance team
            pass
        elif side_effect == "log_emergency":
            # TODO: Log emergency event
            pass
        # Add more side effects as needed
        
        self.logger.debug(
            "Executed side effect",
            slot_id=slot_id,
            side_effect=side_effect
        )
