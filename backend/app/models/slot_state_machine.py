"""Slot state machine for managing parking slot lifecycle."""

from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any
from uuid import UUID
import structlog

from app.models.parking import SlotStatus

logger = structlog.get_logger(__name__)


class SlotEvent(Enum):
    """Events that can trigger slot state transitions."""
    
    # Allocation events
    RESERVE = "reserve"              # Slot reserved for booking
    ALLOCATE = "allocate"           # Slot allocated to active booking
    OCCUPY = "occupy"               # Vehicle checked in
    
    # Release events  
    RELEASE = "release"             # Slot released from booking
    VACATE = "vacate"              # Vehicle checked out
    
    # Administrative events
    START_MAINTENANCE = "start_maintenance"  # Begin maintenance
    END_MAINTENANCE = "end_maintenance"      # End maintenance
    ACTIVATE = "activate"                    # Activate inactive slot
    DEACTIVATE = "deactivate"               # Deactivate slot
    
    # System events
    EXPIRE_RESERVATION = "expire_reservation"  # Reservation expired
    FORCE_RELEASE = "force_release"           # Admin force release
    EMERGENCY_CLEAR = "emergency_clear"       # Emergency evacuation


class SlotStateTransition:
    """Represents a state transition with metadata."""
    
    def __init__(
        self,
        from_state: SlotStatus,
        to_state: SlotStatus,
        event: SlotEvent,
        condition: Optional[str] = None,
        side_effects: Optional[List[str]] = None
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.event = event
        self.condition = condition or "Always allowed"
        self.side_effects = side_effects or []
    
    def __repr__(self) -> str:
        return f"{self.from_state.value} --[{self.event.value}]--> {self.to_state.value}"


class SlotStateMachine:
    """
    State machine for parking slot lifecycle management.
    
    Manages valid state transitions and enforces business rules:
    - Prevents invalid state changes
    - Tracks transition history
    - Validates transition conditions
    - Executes side effects
    """
    
    def __init__(self, slot_id: UUID, initial_state: SlotStatus = SlotStatus.AVAILABLE):
        self.slot_id = slot_id
        self.current_state = initial_state
        self.transition_history: List[Dict[str, Any]] = []
        self.logger = logger.bind(slot_id=str(slot_id))
        
        # Define valid state transitions
        self._setup_transitions()
    
    def _setup_transitions(self) -> None:
        """Setup the state transition table."""
        
        self.transitions: Dict[SlotStatus, Dict[SlotEvent, SlotStateTransition]] = {
            
            # FROM: AVAILABLE
            SlotStatus.AVAILABLE: {
                SlotEvent.RESERVE: SlotStateTransition(
                    SlotStatus.AVAILABLE, SlotStatus.RESERVED, SlotEvent.RESERVE,
                    condition="Slot is not blocked or in maintenance",
                    side_effects=["set_reservation_timer", "notify_allocation"]
                ),
                SlotEvent.ALLOCATE: SlotStateTransition(
                    SlotStatus.AVAILABLE, SlotStatus.OCCUPIED, SlotEvent.ALLOCATE,
                    condition="Direct allocation without reservation",
                    side_effects=["mark_occupied", "start_billing"]
                ),
                SlotEvent.START_MAINTENANCE: SlotStateTransition(
                    SlotStatus.AVAILABLE, SlotStatus.MAINTENANCE, SlotEvent.START_MAINTENANCE,
                    condition="Admin or system maintenance request",
                    side_effects=["block_new_allocations", "notify_maintenance"]
                ),
                SlotEvent.DEACTIVATE: SlotStateTransition(
                    SlotStatus.AVAILABLE, SlotStatus.INACTIVE, SlotEvent.DEACTIVATE,
                    condition="Admin deactivation",
                    side_effects=["block_all_operations", "notify_deactivation"]
                )
            },
            
            # FROM: RESERVED
            SlotStatus.RESERVED: {
                SlotEvent.OCCUPY: SlotStateTransition(
                    SlotStatus.RESERVED, SlotStatus.OCCUPIED, SlotEvent.OCCUPY,
                    condition="Valid booking and check-in time",
                    side_effects=["start_billing", "clear_reservation_timer"]
                ),
                SlotEvent.RELEASE: SlotStateTransition(
                    SlotStatus.RESERVED, SlotStatus.AVAILABLE, SlotEvent.RELEASE,
                    condition="Booking cancelled or released",
                    side_effects=["clear_reservation_timer", "notify_release"]
                ),
                SlotEvent.EXPIRE_RESERVATION: SlotStateTransition(
                    SlotStatus.RESERVED, SlotStatus.AVAILABLE, SlotEvent.EXPIRE_RESERVATION,
                    condition="Reservation timeout exceeded",
                    side_effects=["auto_release", "notify_expiry", "mark_no_show"]
                ),
                SlotEvent.FORCE_RELEASE: SlotStateTransition(
                    SlotStatus.RESERVED, SlotStatus.AVAILABLE, SlotEvent.FORCE_RELEASE,
                    condition="Admin override",
                    side_effects=["admin_release", "notify_forced_release"]
                ),
                SlotEvent.START_MAINTENANCE: SlotStateTransition(
                    SlotStatus.RESERVED, SlotStatus.MAINTENANCE, SlotEvent.START_MAINTENANCE,
                    condition="Emergency maintenance required",
                    side_effects=["force_release_booking", "notify_emergency"]
                )
            },
            
            # FROM: OCCUPIED
            SlotStatus.OCCUPIED: {
                SlotEvent.VACATE: SlotStateTransition(
                    SlotStatus.OCCUPIED, SlotStatus.AVAILABLE, SlotEvent.VACATE,
                    condition="Valid check-out",
                    side_effects=["stop_billing", "calculate_charges", "clean_slot"]
                ),
                SlotEvent.FORCE_RELEASE: SlotStateTransition(
                    SlotStatus.OCCUPIED, SlotStatus.AVAILABLE, SlotEvent.FORCE_RELEASE,
                    condition="Admin or emergency override",
                    side_effects=["emergency_billing", "notify_forced_release"]
                ),
                SlotEvent.START_MAINTENANCE: SlotStateTransition(
                    SlotStatus.OCCUPIED, SlotStatus.MAINTENANCE, SlotEvent.START_MAINTENANCE,
                    condition="Emergency maintenance with occupied slot",
                    side_effects=["emergency_eviction", "notify_emergency"]
                ),
                SlotEvent.EMERGENCY_CLEAR: SlotStateTransition(
                    SlotStatus.OCCUPIED, SlotStatus.AVAILABLE, SlotEvent.EMERGENCY_CLEAR,
                    condition="Emergency evacuation",
                    side_effects=["emergency_billing", "log_emergency", "notify_authorities"]
                )
            },
            
            # FROM: MAINTENANCE
            SlotStatus.MAINTENANCE: {
                SlotEvent.END_MAINTENANCE: SlotStateTransition(
                    SlotStatus.MAINTENANCE, SlotStatus.AVAILABLE, SlotEvent.END_MAINTENANCE,
                    condition="Maintenance completed and approved",
                    side_effects=["validate_slot_condition", "enable_allocations"]
                ),
                SlotEvent.DEACTIVATE: SlotStateTransition(
                    SlotStatus.MAINTENANCE, SlotStatus.INACTIVE, SlotEvent.DEACTIVATE,
                    condition="Maintenance reveals permanent issues",
                    side_effects=["mark_permanent_unavailable", "update_lot_capacity"]
                )
            },
            
            # FROM: INACTIVE
            SlotStatus.INACTIVE: {
                SlotEvent.ACTIVATE: SlotStateTransition(
                    SlotStatus.INACTIVE, SlotStatus.AVAILABLE, SlotEvent.ACTIVATE,
                    condition="Admin reactivation with safety approval",
                    side_effects=["safety_check", "restore_slot_capacity"]
                ),
                SlotEvent.START_MAINTENANCE: SlotStateTransition(
                    SlotStatus.INACTIVE, SlotStatus.MAINTENANCE, SlotEvent.START_MAINTENANCE,
                    condition="Repair attempt on inactive slot",
                    side_effects=["begin_repair_process"]
                )
            }
        }
    
    def can_transition(self, event: SlotEvent) -> bool:
        """
        Check if a state transition is valid for the current state.
        
        Args:
            event: The event to trigger
            
        Returns:
            True if transition is allowed
        """
        return (
            self.current_state in self.transitions and
            event in self.transitions[self.current_state]
        )
    
    def get_valid_events(self) -> List[SlotEvent]:
        """Get list of valid events for current state."""
        if self.current_state in self.transitions:
            return list(self.transitions[self.current_state].keys())
        return []
    
    def get_transition_info(self, event: SlotEvent) -> Optional[SlotStateTransition]:
        """Get detailed information about a transition."""
        if self.can_transition(event):
            return self.transitions[self.current_state][event]
        return None
    
    def transition(
        self, 
        event: SlotEvent, 
        context: Optional[Dict[str, Any]] = None,
        triggered_by: Optional[str] = None
    ) -> bool:
        """
        Execute a state transition.
        
        Args:
            event: The event to trigger
            context: Additional context for the transition
            triggered_by: User or system that triggered the transition
            
        Returns:
            True if transition was successful
            
        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        if not self.can_transition(event):
            valid_events = [e.value for e in self.get_valid_events()]
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.current_state.value} with event {event.value}. "
                f"Valid events: {valid_events}"
            )
        
        transition = self.transitions[self.current_state][event]
        old_state = self.current_state
        
        try:
            # Execute the transition
            self.current_state = transition.to_state
            
            # Record transition in history
            history_entry = {
                "timestamp": datetime.now(timezone.utc),
                "from_state": old_state.value,
                "to_state": transition.to_state.value,
                "event": event.value,
                "condition": transition.condition,
                "side_effects": transition.side_effects,
                "context": context or {},
                "triggered_by": triggered_by or "system"
            }
            self.transition_history.append(history_entry)
            
            self.logger.info(
                "Slot state transition executed",
                from_state=old_state.value,
                to_state=transition.to_state.value,
                event=event.value,
                triggered_by=triggered_by
            )
            
            return True
            
        except Exception as e:
            # Rollback on failure
            self.current_state = old_state
            self.logger.error(
                "Slot state transition failed, rolled back",
                event=event.value,
                error=str(e)
            )
            raise StateTransitionError(f"Failed to execute transition: {str(e)}")
    
    def get_transition_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get transition history, optionally limited to recent entries."""
        if limit:
            return self.transition_history[-limit:]
        return self.transition_history.copy()
    
    def get_state_duration(self) -> Optional[float]:
        """Get how long the slot has been in current state (in seconds)."""
        if not self.transition_history:
            return None
        
        last_transition = self.transition_history[-1]
        last_timestamp = last_transition["timestamp"]
        current_time = datetime.now(timezone.utc)
        
        return (current_time - last_timestamp).total_seconds()
    
    def is_in_terminal_state(self) -> bool:
        """Check if slot is in a terminal state (no outgoing transitions)."""
        return len(self.get_valid_events()) == 0
    
    def is_available_for_booking(self) -> bool:
        """Check if slot is available for new bookings."""
        return self.current_state == SlotStatus.AVAILABLE
    
    def is_occupied(self) -> bool:
        """Check if slot is currently occupied."""
        return self.current_state == SlotStatus.OCCUPIED
    
    def requires_admin_intervention(self) -> bool:
        """Check if slot requires admin intervention."""
        return self.current_state in [SlotStatus.MAINTENANCE, SlotStatus.INACTIVE]
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get comprehensive state summary."""
        return {
            "slot_id": str(self.slot_id),
            "current_state": self.current_state.value,
            "valid_events": [e.value for e in self.get_valid_events()],
            "state_duration_seconds": self.get_state_duration(),
            "is_available_for_booking": self.is_available_for_booking(),
            "is_occupied": self.is_occupied(),
            "requires_admin_intervention": self.requires_admin_intervention(),
            "transition_count": len(self.transition_history),
            "last_transition": self.transition_history[-1] if self.transition_history else None
        }
    
    def validate_business_rules(self, event: SlotEvent, context: Dict[str, Any]) -> bool:
        """
        Validate business rules for a transition.
        
        Override this method to add custom business logic validation.
        """
        # Example business rules (can be extended)
        
        if event == SlotEvent.RESERVE:
            # Check if reservation is allowed
            if context.get("booking_start_time"):
                start_time = context["booking_start_time"]
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                
                # Cannot reserve for past times
                if start_time <= datetime.now(timezone.utc):
                    return False
        
        if event == SlotEvent.OCCUPY:
            # Check if check-in is within allowed window
            if context.get("booking_start_time"):
                start_time = context["booking_start_time"]
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                
                current_time = datetime.now(timezone.utc)
                # Allow check-in up to 15 minutes before scheduled time
                earliest_checkin = start_time - timedelta(minutes=15)
                
                if current_time < earliest_checkin:
                    return False
        
        return True


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class StateTransitionError(Exception):
    """Raised when a state transition fails to execute."""
    pass


class SlotStateMachineFactory:
    """Factory for creating slot state machines."""
    
    @staticmethod
    def create_for_slot(slot_id: UUID, current_status: SlotStatus) -> SlotStateMachine:
        """Create a state machine for an existing slot."""
        return SlotStateMachine(slot_id=slot_id, initial_state=current_status)
    
    @staticmethod
    def create_new_slot(slot_id: UUID) -> SlotStateMachine:
        """Create a state machine for a new slot."""
        return SlotStateMachine(slot_id=slot_id, initial_state=SlotStatus.AVAILABLE)
    
    @staticmethod
    def create_maintenance_slot(slot_id: UUID) -> SlotStateMachine:
        """Create a state machine for a slot starting in maintenance."""
        return SlotStateMachine(slot_id=slot_id, initial_state=SlotStatus.MAINTENANCE)
