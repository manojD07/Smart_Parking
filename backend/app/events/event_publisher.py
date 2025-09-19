"""Event publisher for publishing domain events to WebSocket clients."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from uuid import UUID
import structlog

from app.events.domain_events import (
    DomainEvent, DomainEventType, DomainEventHandler, domain_event_registry
)
from app.websockets.events import (
    WebSocketEvent, WebSocketEventType, WebSocketEventPriority, WebSocketEventFactory
)
from app.websockets.manager import websocket_manager

logger = structlog.get_logger(__name__)


class WebSocketEventHandler(DomainEventHandler):
    """Handler that converts domain events to WebSocket events."""
    
    def __init__(self):
        self.logger = logger.bind(handler="WebSocketEventHandler")
        
        # Mapping of domain events to WebSocket events
        self.event_mapping = {
            DomainEventType.BOOKING_CREATED: WebSocketEventType.BOOKING_CREATED,
            DomainEventType.BOOKING_CONFIRMED: WebSocketEventType.BOOKING_CONFIRMED,
            DomainEventType.BOOKING_CANCELLED: WebSocketEventType.BOOKING_CANCELLED,
            DomainEventType.BOOKING_CHECKED_IN: WebSocketEventType.BOOKING_CHECKED_IN,
            DomainEventType.BOOKING_CHECKED_OUT: WebSocketEventType.BOOKING_CHECKED_OUT,
            DomainEventType.BOOKING_EXPIRED: WebSocketEventType.BOOKING_EXPIRED,
            DomainEventType.SLOT_STATUS_CHANGED: WebSocketEventType.SLOT_STATUS_CHANGED,
            DomainEventType.AVAILABILITY_CHANGED: WebSocketEventType.AVAILABILITY_UPDATE,
            DomainEventType.CAPACITY_UPDATED: WebSocketEventType.LOT_CAPACITY_CHANGED,
            DomainEventType.SLOT_MAINTENANCE_STARTED: WebSocketEventType.MAINTENANCE_ALERT,
            DomainEventType.SLOT_MAINTENANCE_COMPLETED: WebSocketEventType.MAINTENANCE_ALERT,
        }
    
    def can_handle(self, event_type: DomainEventType) -> bool:
        """Check if this handler can handle the given event type."""
        return event_type in self.event_mapping
    
    async def handle(self, event: DomainEvent) -> bool:
        """Convert domain event to WebSocket event and broadcast."""
        try:
            websocket_event = await self._convert_to_websocket_event(event)
            if websocket_event:
                await websocket_manager.broadcast(websocket_event)
                return True
            return False
            
        except Exception as e:
            self.logger.error(
                "Failed to handle domain event",
                event_id=event.event_id,
                event_type=event.event_type.value,
                error=str(e)
            )
            return False
    
    async def _convert_to_websocket_event(self, domain_event: DomainEvent) -> Optional[WebSocketEvent]:
        """Convert domain event to WebSocket event."""
        
        if domain_event.event_type == DomainEventType.BOOKING_CREATED:
            return await self._create_booking_event(domain_event)
        
        elif domain_event.event_type == DomainEventType.BOOKING_CANCELLED:
            return await self._create_booking_cancelled_event(domain_event)
        
        elif domain_event.event_type == DomainEventType.SLOT_STATUS_CHANGED:
            return await self._create_slot_status_event(domain_event)
        
        elif domain_event.event_type == DomainEventType.AVAILABILITY_CHANGED:
            return await self._create_availability_event(domain_event)
        
        elif domain_event.event_type == DomainEventType.SLOT_MAINTENANCE_STARTED:
            return await self._create_maintenance_event(domain_event)
        
        # Add more conversions as needed
        return None
    
    async def _create_booking_event(self, domain_event: DomainEvent) -> WebSocketEvent:
        """Create WebSocket event for booking creation."""
        data = domain_event.data
        
        return WebSocketEventFactory.booking_created(
            booking_id=str(data.booking_id),
            user_id=str(data.user_id),
            lot_id=str(data.lot_id),
            slot_id=str(data.slot_id)
        )
    
    async def _create_booking_cancelled_event(self, domain_event: DomainEvent) -> WebSocketEvent:
        """Create WebSocket event for booking cancellation."""
        data = domain_event.data
        
        return WebSocketEventFactory.booking_cancelled(
            booking_id=str(data.booking_id),
            user_id=str(data.user_id),
            lot_id=str(data.lot_id),
            slot_id=str(data.slot_id),
            reason=data.metadata.get("cancellation_reason", "cancelled")
        )
    
    async def _create_slot_status_event(self, domain_event: DomainEvent) -> WebSocketEvent:
        """Create WebSocket event for slot status change."""
        data = domain_event.data
        
        return WebSocketEventFactory.slot_status_changed(
            slot_id=str(data.slot_id),
            old_status=str(data.old_value),
            new_status=str(data.new_value),
            lot_id=str(data.lot_id)
        )
    
    async def _create_availability_event(self, domain_event: DomainEvent) -> WebSocketEvent:
        """Create WebSocket event for availability change."""
        data = domain_event.data
        metadata = data.metadata
        
        return WebSocketEventFactory.availability_update(
            lot_id=str(data.lot_id),
            available_slots=int(data.new_value),
            total_slots=metadata.get("total_slots", 0),
            vehicle_type=metadata.get("vehicle_type")
        )
    
    async def _create_maintenance_event(self, domain_event: DomainEvent) -> WebSocketEvent:
        """Create WebSocket event for maintenance alert."""
        data = domain_event.data
        metadata = data.metadata
        
        return WebSocketEventFactory.maintenance_alert(
            lot_id=str(data.lot_id),
            slot_id=str(data.slot_id),
            message=f"Maintenance {metadata.get('maintenance_type', 'activity')} on slot {data.slot_id}",
            maintenance_type=metadata.get("maintenance_type", "scheduled")
        )


class AvailabilityUpdateHandler(DomainEventHandler):
    """Handler specifically for availability update aggregation."""
    
    def __init__(self):
        self.logger = logger.bind(handler="AvailabilityUpdateHandler")
        self.update_buffer: Dict[str, Dict[str, Any]] = {}
        self.buffer_timeout = 5  # seconds
        self.pending_updates: Set[str] = set()
    
    def can_handle(self, event_type: DomainEventType) -> bool:
        """Check if this handler can handle the given event type."""
        return event_type in [
            DomainEventType.AVAILABILITY_CHANGED,
            DomainEventType.SLOT_STATUS_CHANGED,
            DomainEventType.CAPACITY_UPDATED
        ]
    
    async def handle(self, event: DomainEvent) -> bool:
        """Buffer and aggregate availability updates."""
        try:
            lot_id = str(event.data.lot_id) if event.data.lot_id else "unknown"
            
            # Buffer the update
            if lot_id not in self.update_buffer:
                self.update_buffer[lot_id] = {
                    "lot_id": lot_id,
                    "events": [],
                    "last_update": datetime.now(timezone.utc)
                }
            
            self.update_buffer[lot_id]["events"].append(event)
            self.update_buffer[lot_id]["last_update"] = datetime.now(timezone.utc)
            
            # Schedule processing if not already pending
            if lot_id not in self.pending_updates:
                self.pending_updates.add(lot_id)
                asyncio.create_task(self._process_buffered_updates(lot_id))
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to handle availability event",
                event_id=event.event_id,
                error=str(e)
            )
            return False
    
    async def _process_buffered_updates(self, lot_id: str) -> None:
        """Process buffered updates for a lot after timeout."""
        await asyncio.sleep(self.buffer_timeout)
        
        try:
            if lot_id in self.update_buffer:
                buffer_data = self.update_buffer.pop(lot_id)
                self.pending_updates.discard(lot_id)
                
                # Create aggregated availability update
                await self._send_aggregated_update(buffer_data)
                
        except Exception as e:
            self.logger.error("Failed to process buffered updates", lot_id=lot_id, error=str(e))
    
    async def _send_aggregated_update(self, buffer_data: Dict[str, Any]) -> None:
        """Send aggregated availability update."""
        lot_id = buffer_data["lot_id"]
        events = buffer_data["events"]
        
        # Calculate aggregated data from events
        total_events = len(events)
        vehicle_types = set()
        latest_availability = {}
        
        for event in events:
            if event.data.metadata.get("vehicle_type"):
                vehicle_types.add(event.data.metadata["vehicle_type"])
            
            if event.event_type == DomainEventType.AVAILABILITY_CHANGED:
                vtype = event.data.metadata.get("vehicle_type", "all")
                latest_availability[vtype] = {
                    "available": event.data.new_value,
                    "total": event.data.metadata.get("total_slots", 0)
                }
        
        # Create aggregated WebSocket event
        aggregated_event = WebSocketEventFactory.availability_update(
            lot_id=lot_id,
            available_slots=latest_availability.get("all", {}).get("available", 0),
            total_slots=latest_availability.get("all", {}).get("total", 0)
        )
        
        # Add aggregation metadata
        aggregated_event.data.update({
            "aggregated_events_count": total_events,
            "vehicle_types_affected": list(vehicle_types),
            "detailed_availability": latest_availability,
            "aggregation_window_seconds": self.buffer_timeout
        })
        
        await websocket_manager.broadcast(aggregated_event)
        
        self.logger.debug(
            "Sent aggregated availability update",
            lot_id=lot_id,
            events_count=total_events,
            vehicle_types=list(vehicle_types)
        )


class NotificationHandler(DomainEventHandler):
    """Handler for creating user notifications from domain events."""
    
    def __init__(self):
        self.logger = logger.bind(handler="NotificationHandler")
    
    def can_handle(self, event_type: DomainEventType) -> bool:
        """Check if this handler can handle the given event type."""
        return event_type in [
            DomainEventType.BOOKING_CREATED,
            DomainEventType.BOOKING_CONFIRMED,
            DomainEventType.BOOKING_CANCELLED,
            DomainEventType.BOOKING_EXPIRED,
            DomainEventType.PAYMENT_COMPLETED,
            DomainEventType.PAYMENT_FAILED
        ]
    
    async def handle(self, event: DomainEvent) -> bool:
        """Create user notifications from domain events."""
        try:
            notification_event = await self._create_notification_event(event)
            if notification_event:
                await websocket_manager.broadcast(notification_event)
                return True
            return False
            
        except Exception as e:
            self.logger.error(
                "Failed to create notification",
                event_id=event.event_id,
                error=str(e)
            )
            return False
    
    async def _create_notification_event(self, domain_event: DomainEvent) -> Optional[WebSocketEvent]:
        """Create notification event from domain event."""
        data = domain_event.data
        user_id = str(data.user_id) if data.user_id else None
        
        if not user_id:
            return None
        
        if domain_event.event_type == DomainEventType.BOOKING_CREATED:
            return WebSocketEventFactory.user_notification(
                user_id=user_id,
                title="Booking Created",
                message=f"Your booking has been created successfully. Booking ID: {data.booking_id}",
                notification_type="success"
            )
        
        elif domain_event.event_type == DomainEventType.BOOKING_CONFIRMED:
            return WebSocketEventFactory.user_notification(
                user_id=user_id,
                title="Booking Confirmed",
                message=f"Your booking has been confirmed. You can now check in.",
                notification_type="success"
            )
        
        elif domain_event.event_type == DomainEventType.BOOKING_CANCELLED:
            reason = data.metadata.get("cancellation_reason", "cancelled")
            return WebSocketEventFactory.user_notification(
                user_id=user_id,
                title="Booking Cancelled",
                message=f"Your booking has been cancelled. Reason: {reason}",
                notification_type="warning"
            )
        
        elif domain_event.event_type == DomainEventType.PAYMENT_COMPLETED:
            amount = data.metadata.get("amount", data.new_value)
            return WebSocketEventFactory.user_notification(
                user_id=user_id,
                title="Payment Successful",
                message=f"Payment of ${amount} has been processed successfully.",
                notification_type="success"
            )
        
        elif domain_event.event_type == DomainEventType.PAYMENT_FAILED:
            return WebSocketEventFactory.user_notification(
                user_id=user_id,
                title="Payment Failed",
                message="Your payment could not be processed. Please try again or contact support.",
                notification_type="error"
            )
        
        return None


class AdminAlertHandler(DomainEventHandler):
    """Handler for creating admin alerts from domain events."""
    
    def __init__(self):
        self.logger = logger.bind(handler="AdminAlertHandler")
    
    def can_handle(self, event_type: DomainEventType) -> bool:
        """Check if this handler can handle the given event type."""
        return event_type in [
            DomainEventType.SLOT_MAINTENANCE_STARTED,
            DomainEventType.PAYMENT_FAILED,
            DomainEventType.SYSTEM_MAINTENANCE_STARTED
        ]
    
    async def handle(self, event: DomainEvent) -> bool:
        """Create admin alerts from domain events."""
        try:
            alert_event = await self._create_alert_event(event)
            if alert_event:
                await websocket_manager.broadcast(alert_event)
                return True
            return False
            
        except Exception as e:
            self.logger.error(
                "Failed to create admin alert",
                event_id=event.event_id,
                error=str(e)
            )
            return False
    
    async def _create_alert_event(self, domain_event: DomainEvent) -> Optional[WebSocketEvent]:
        """Create admin alert event from domain event."""
        data = domain_event.data
        
        if domain_event.event_type == DomainEventType.SLOT_MAINTENANCE_STARTED:
            maintenance_type = data.metadata.get("maintenance_type", "unknown")
            return WebSocketEventFactory.admin_alert(
                message=f"Maintenance started on slot {data.slot_id} in lot {data.lot_id}",
                alert_type="info" if maintenance_type == "scheduled" else "warning",
                data={
                    "slot_id": str(data.slot_id),
                    "lot_id": str(data.lot_id),
                    "maintenance_type": maintenance_type
                }
            )
        
        elif domain_event.event_type == DomainEventType.PAYMENT_FAILED:
            return WebSocketEventFactory.admin_alert(
                message=f"Payment failed for user {data.user_id}, booking {data.booking_id}",
                alert_type="warning",
                data={
                    "user_id": str(data.user_id),
                    "booking_id": str(data.booking_id),
                    "payment_id": str(data.payment_id) if data.payment_id else None
                }
            )
        
        return None


class EventPublisher:
    """Central event publisher for domain events."""
    
    def __init__(self):
        self.logger = logger.bind(service="EventPublisher")
        self.is_started = False
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register all event handlers."""
        # WebSocket event handler
        websocket_handler = WebSocketEventHandler()
        for event_type in [
            DomainEventType.BOOKING_CREATED,
            DomainEventType.BOOKING_CANCELLED,
            DomainEventType.SLOT_STATUS_CHANGED,
            DomainEventType.SLOT_MAINTENANCE_STARTED,
        ]:
            domain_event_registry.register_handler(event_type, websocket_handler)
        
        # Availability update handler
        availability_handler = AvailabilityUpdateHandler()
        for event_type in [
            DomainEventType.AVAILABILITY_CHANGED,
            DomainEventType.SLOT_STATUS_CHANGED,
            DomainEventType.CAPACITY_UPDATED,
        ]:
            domain_event_registry.register_handler(event_type, availability_handler)
        
        # Notification handler
        notification_handler = NotificationHandler()
        for event_type in [
            DomainEventType.BOOKING_CREATED,
            DomainEventType.BOOKING_CONFIRMED,
            DomainEventType.BOOKING_CANCELLED,
            DomainEventType.PAYMENT_COMPLETED,
            DomainEventType.PAYMENT_FAILED,
        ]:
            domain_event_registry.register_handler(event_type, notification_handler)
        
        # Admin alert handler
        admin_handler = AdminAlertHandler()
        for event_type in [
            DomainEventType.SLOT_MAINTENANCE_STARTED,
            DomainEventType.PAYMENT_FAILED,
        ]:
            domain_event_registry.register_handler(event_type, admin_handler)
    
    async def start(self) -> None:
        """Start the event publisher."""
        if self.is_started:
            return
        
        # Start WebSocket manager if not already started
        if not websocket_manager._heartbeat_task:
            await websocket_manager.start()
        
        self.is_started = True
        self.logger.info("Event publisher started")
    
    async def stop(self) -> None:
        """Stop the event publisher."""
        if not self.is_started:
            return
        
        self.is_started = False
        self.logger.info("Event publisher stopped")
    
    async def publish(self, event: DomainEvent) -> bool:
        """
        Publish a domain event.
        
        Args:
            event: Domain event to publish
            
        Returns:
            True if published successfully
        """
        if not self.is_started:
            await self.start()
        
        try:
            # Dispatch to registered handlers
            results = await domain_event_registry.dispatch(event)
            
            # Mark event as processed if at least one handler succeeded
            if any(results):
                event.mark_processed()
                
                self.logger.info(
                    "Domain event published",
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    handlers_success=sum(results),
                    handlers_total=len(results)
                )
                return True
            else:
                self.logger.warning(
                    "Domain event publishing failed - no handlers succeeded",
                    event_id=event.event_id,
                    event_type=event.event_type.value
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Failed to publish domain event",
                event_id=event.event_id,
                event_type=event.event_type.value,
                error=str(e)
            )
            return False
    
    async def publish_many(self, events: List[DomainEvent]) -> List[bool]:
        """
        Publish multiple domain events.
        
        Args:
            events: List of domain events to publish
            
        Returns:
            List of publish results
        """
        results = []
        for event in events:
            result = await self.publish(event)
            results.append(result)
        
        return results


# Global event publisher instance
event_publisher = EventPublisher()
