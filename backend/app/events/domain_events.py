"""Domain events for business logic integration."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List, Type
from uuid import UUID, uuid4
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)


class DomainEventType(str, Enum):
    """Types of domain events in the parking system."""
    
    # Booking domain events
    BOOKING_REQUESTED = "booking_requested"
    BOOKING_CREATED = "booking_created"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_EXPIRED = "booking_expired"
    BOOKING_CHECKED_IN = "booking_checked_in"
    BOOKING_CHECKED_OUT = "booking_checked_out"
    BOOKING_MODIFIED = "booking_modified"
    
    # Slot domain events
    SLOT_ALLOCATED = "slot_allocated"
    SLOT_RELEASED = "slot_released"
    SLOT_STATUS_CHANGED = "slot_status_changed"
    SLOT_MAINTENANCE_STARTED = "slot_maintenance_started"
    SLOT_MAINTENANCE_COMPLETED = "slot_maintenance_completed"
    SLOT_OCCUPIED = "slot_occupied"
    SLOT_VACATED = "slot_vacated"
    
    # Availability domain events
    AVAILABILITY_CHANGED = "availability_changed"
    CAPACITY_UPDATED = "capacity_updated"
    LOT_STATUS_CHANGED = "lot_status_changed"
    
    # Payment domain events
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REFUNDED = "payment_refunded"
    
    # User domain events
    USER_REGISTERED = "user_registered"
    USER_PROFILE_UPDATED = "user_profile_updated"
    USER_PREFERENCES_CHANGED = "user_preferences_changed"
    
    # System domain events
    SYSTEM_MAINTENANCE_STARTED = "system_maintenance_started"
    SYSTEM_MAINTENANCE_COMPLETED = "system_maintenance_completed"
    PRICING_RULE_UPDATED = "pricing_rule_updated"


@dataclass
class EventData:
    """Base event data structure."""
    
    # Core identifiers
    booking_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    lot_id: Optional[UUID] = None
    slot_id: Optional[UUID] = None
    payment_id: Optional[UUID] = None
    
    # Event-specific data
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timing information
    effective_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {}
        
        # Add non-None fields
        for field_name, field_value in self.__dict__.items():
            if field_value is not None:
                if isinstance(field_value, UUID):
                    result[field_name] = str(field_value)
                elif isinstance(field_value, datetime):
                    result[field_name] = field_value.isoformat()
                else:
                    result[field_name] = field_value
        
        return result


@dataclass
class DomainEvent:
    """Base domain event class."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: DomainEventType = field(default=DomainEventType.BOOKING_CREATED)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "domain"
    version: str = "1.0"
    
    # Event data
    data: EventData = field(default_factory=EventData)
    
    # Event context
    correlation_id: Optional[str] = None  # For tracking related events
    causation_id: Optional[str] = None    # ID of the event that caused this event
    
    # Event processing
    retry_count: int = 0
    max_retries: int = 3
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "version": self.version,
            "data": self.data.to_dict(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "retry_count": self.retry_count,
            "processed": self.processed
        }
    
    def should_retry(self) -> bool:
        """Check if event should be retried."""
        return self.retry_count < self.max_retries and not self.processed
    
    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1
    
    def mark_processed(self) -> None:
        """Mark event as processed."""
        self.processed = True


# Specific domain event classes
class BookingDomainEvent(DomainEvent):
    """Domain event for booking-related operations."""
    
    def __init__(self, event_type: DomainEventType, data: EventData, **kwargs):
        super().__init__(event_type=event_type, data=data, source="booking_service", **kwargs)


class SlotDomainEvent(DomainEvent):
    """Domain event for slot-related operations."""
    
    def __init__(self, event_type: DomainEventType, data: EventData, **kwargs):
        super().__init__(event_type=event_type, data=data, source="slot_service", **kwargs)


class AvailabilityDomainEvent(DomainEvent):
    """Domain event for availability-related operations."""
    
    def __init__(self, event_type: DomainEventType, data: EventData, **kwargs):
        super().__init__(event_type=event_type, data=data, source="availability_service", **kwargs)


class PaymentDomainEvent(DomainEvent):
    """Domain event for payment-related operations."""
    
    def __init__(self, event_type: DomainEventType, data: EventData, **kwargs):
        super().__init__(event_type=event_type, data=data, source="payment_service", **kwargs)


class UserDomainEvent(DomainEvent):
    """Domain event for user-related operations."""
    
    def __init__(self, event_type: DomainEventType, data: EventData, **kwargs):
        super().__init__(event_type=event_type, data=data, source="user_service", **kwargs)


class SystemDomainEvent(DomainEvent):
    """Domain event for system-related operations."""
    
    def __init__(self, event_type: DomainEventType, data: EventData, **kwargs):
        super().__init__(event_type=event_type, data=data, source="system", **kwargs)


class DomainEventFactory:
    """Factory for creating domain events."""
    
    @staticmethod
    def booking_created(
        booking_id: UUID,
        user_id: UUID,
        lot_id: UUID,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime,
        vehicle_type: str,
        total_amount: float,
        correlation_id: Optional[str] = None
    ) -> BookingDomainEvent:
        """Create booking created event."""
        data = EventData(
            booking_id=booking_id,
            user_id=user_id,
            lot_id=lot_id,
            slot_id=slot_id,
            effective_time=start_time,
            expiry_time=end_time,
            metadata={
                "vehicle_type": vehicle_type,
                "total_amount": total_amount,
                "booking_duration_hours": (end_time - start_time).total_seconds() / 3600
            }
        )
        
        return BookingDomainEvent(
            event_type=DomainEventType.BOOKING_CREATED,
            data=data,
            correlation_id=correlation_id
        )
    
    @staticmethod
    def booking_cancelled(
        booking_id: UUID,
        user_id: UUID,
        lot_id: UUID,
        slot_id: UUID,
        reason: str = "user_cancelled",
        refund_amount: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> BookingDomainEvent:
        """Create booking cancelled event."""
        data = EventData(
            booking_id=booking_id,
            user_id=user_id,
            lot_id=lot_id,
            slot_id=slot_id,
            metadata={
                "cancellation_reason": reason,
                "refund_amount": refund_amount,
                "cancelled_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return BookingDomainEvent(
            event_type=DomainEventType.BOOKING_CANCELLED,
            data=data,
            correlation_id=correlation_id
        )
    
    @staticmethod
    def slot_status_changed(
        slot_id: UUID,
        lot_id: UUID,
        old_status: str,
        new_status: str,
        booking_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None
    ) -> SlotDomainEvent:
        """Create slot status changed event."""
        data = EventData(
            slot_id=slot_id,
            lot_id=lot_id,
            booking_id=booking_id,
            old_value=old_status,
            new_value=new_status,
            metadata={
                "status_change": f"{old_status} -> {new_status}",
                "changed_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return SlotDomainEvent(
            event_type=DomainEventType.SLOT_STATUS_CHANGED,
            data=data,
            correlation_id=correlation_id
        )
    
    @staticmethod
    def availability_changed(
        lot_id: UUID,
        vehicle_type: str,
        old_available: int,
        new_available: int,
        total_slots: int,
        correlation_id: Optional[str] = None
    ) -> AvailabilityDomainEvent:
        """Create availability changed event."""
        data = EventData(
            lot_id=lot_id,
            old_value=old_available,
            new_value=new_available,
            metadata={
                "vehicle_type": vehicle_type,
                "total_slots": total_slots,
                "old_occupancy_rate": round((total_slots - old_available) / total_slots * 100, 2) if total_slots > 0 else 0,
                "new_occupancy_rate": round((total_slots - new_available) / total_slots * 100, 2) if total_slots > 0 else 0,
                "availability_change": new_available - old_available
            }
        )
        
        return AvailabilityDomainEvent(
            event_type=DomainEventType.AVAILABILITY_CHANGED,
            data=data,
            correlation_id=correlation_id
        )
    
    @staticmethod
    def payment_completed(
        payment_id: UUID,
        booking_id: UUID,
        user_id: UUID,
        amount: float,
        payment_method: str,
        correlation_id: Optional[str] = None
    ) -> PaymentDomainEvent:
        """Create payment completed event."""
        data = EventData(
            payment_id=payment_id,
            booking_id=booking_id,
            user_id=user_id,
            new_value=amount,
            metadata={
                "payment_method": payment_method,
                "payment_status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return PaymentDomainEvent(
            event_type=DomainEventType.PAYMENT_COMPLETED,
            data=data,
            correlation_id=correlation_id
        )
    
    @staticmethod
    def user_registered(
        user_id: UUID,
        email: str,
        name: str,
        correlation_id: Optional[str] = None
    ) -> UserDomainEvent:
        """Create user registered event."""
        data = EventData(
            user_id=user_id,
            metadata={
                "email": email,
                "name": name,
                "registration_source": "web",
                "registered_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return UserDomainEvent(
            event_type=DomainEventType.USER_REGISTERED,
            data=data,
            correlation_id=correlation_id
        )
    
    @staticmethod
    def slot_maintenance_started(
        slot_id: UUID,
        lot_id: UUID,
        maintenance_type: str,
        estimated_duration: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> SlotDomainEvent:
        """Create slot maintenance started event."""
        data = EventData(
            slot_id=slot_id,
            lot_id=lot_id,
            metadata={
                "maintenance_type": maintenance_type,
                "estimated_duration_minutes": estimated_duration,
                "started_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return SlotDomainEvent(
            event_type=DomainEventType.SLOT_MAINTENANCE_STARTED,
            data=data,
            correlation_id=correlation_id
        )


class DomainEventHandler(ABC):
    """Abstract base class for domain event handlers."""
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> bool:
        """
        Handle a domain event.
        
        Args:
            event: Domain event to handle
            
        Returns:
            True if handled successfully
        """
        pass
    
    @abstractmethod
    def can_handle(self, event_type: DomainEventType) -> bool:
        """
        Check if this handler can handle the given event type.
        
        Args:
            event_type: Type of domain event
            
        Returns:
            True if this handler can handle the event type
        """
        pass


class DomainEventRegistry:
    """Registry for domain event handlers."""
    
    def __init__(self):
        self.handlers: Dict[DomainEventType, List[DomainEventHandler]] = {}
        self.logger = logger.bind(service="DomainEventRegistry")
    
    def register_handler(self, event_type: DomainEventType, handler: DomainEventHandler) -> None:
        """Register an event handler for a specific event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        
        self.logger.info(
            "Domain event handler registered",
            event_type=event_type.value,
            handler_class=handler.__class__.__name__
        )
    
    def get_handlers(self, event_type: DomainEventType) -> List[DomainEventHandler]:
        """Get all handlers for a specific event type."""
        return self.handlers.get(event_type, [])
    
    async def dispatch(self, event: DomainEvent) -> List[bool]:
        """
        Dispatch event to all registered handlers.
        
        Args:
            event: Domain event to dispatch
            
        Returns:
            List of handler results
        """
        handlers = self.get_handlers(event.event_type)
        results = []
        
        for handler in handlers:
            try:
                result = await handler.handle(event)
                results.append(result)
                
                self.logger.debug(
                    "Domain event handled",
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    handler_class=handler.__class__.__name__,
                    result=result
                )
                
            except Exception as e:
                self.logger.error(
                    "Domain event handler failed",
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    handler_class=handler.__class__.__name__,
                    error=str(e)
                )
                results.append(False)
        
        return results


# Global domain event registry
domain_event_registry = DomainEventRegistry()
