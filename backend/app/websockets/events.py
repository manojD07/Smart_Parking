"""WebSocket event definitions and management."""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from pydantic import BaseModel
import json
import structlog

logger = structlog.get_logger(__name__)


class WebSocketEventType(str, Enum):
    """Types of WebSocket events."""
    
    # Connection events
    CLIENT_CONNECTED = "client_connected"
    CLIENT_DISCONNECTED = "client_disconnected"
    
    # Availability events
    AVAILABILITY_UPDATE = "availability_update"
    SLOT_STATUS_CHANGED = "slot_status_changed"
    LOT_CAPACITY_CHANGED = "lot_capacity_changed"
    
    # Booking events
    BOOKING_CREATED = "booking_created"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_CHECKED_IN = "booking_checked_in"
    BOOKING_CHECKED_OUT = "booking_checked_out"
    BOOKING_EXPIRED = "booking_expired"
    
    # Notification events
    USER_NOTIFICATION = "user_notification"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    MAINTENANCE_ALERT = "maintenance_alert"
    
    # Admin events
    ADMIN_ALERT = "admin_alert"
    REVENUE_UPDATE = "revenue_update"
    OCCUPANCY_UPDATE = "occupancy_update"
    
    # System events
    SYSTEM_STATUS = "system_status"
    ERROR_NOTIFICATION = "error_notification"
    HEARTBEAT = "heartbeat"


class WebSocketEventPriority(str, Enum):
    """Priority levels for WebSocket events."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WebSocketEvent:
    """WebSocket event data structure."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: WebSocketEventType = field(default=WebSocketEventType.SYSTEM_STATUS)
    priority: WebSocketEventPriority = field(default=WebSocketEventPriority.NORMAL)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Event metadata
    source: str = "system"
    target_users: Optional[List[str]] = None  # None = broadcast to all
    target_roles: Optional[List[str]] = None  # user, admin, etc.
    target_lots: Optional[List[str]] = None   # Specific parking lots
    
    # Event data
    data: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None
    
    # Event lifecycle
    retry_count: int = 0
    max_retries: int = 3
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "target_users": self.target_users,
            "target_roles": self.target_roles,
            "target_lots": self.target_lots,
            "data": self.data,
            "message": self.message,
            "retry_count": self.retry_count,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebSocketEvent":
        """Create event from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid4())),
            event_type=WebSocketEventType(data["event_type"]),
            priority=WebSocketEventPriority(data.get("priority", "normal")),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(timezone.utc),
            source=data.get("source", "system"),
            target_users=data.get("target_users"),
            target_roles=data.get("target_roles"),
            target_lots=data.get("target_lots"),
            data=data.get("data", {}),
            message=data.get("message"),
            retry_count=data.get("retry_count", 0),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketEvent":
        """Create event from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def is_expired(self) -> bool:
        """Check if event has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def should_retry(self) -> bool:
        """Check if event should be retried."""
        return self.retry_count < self.max_retries and not self.is_expired()
    
    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1
    
    def matches_target(self, user_id: Optional[str] = None, user_role: Optional[str] = None, lot_id: Optional[str] = None) -> bool:
        """Check if event matches the given target criteria."""
        # If no specific targets, it's a broadcast
        if not self.target_users and not self.target_roles and not self.target_lots:
            return True
        
        # Check user targeting
        if self.target_users and user_id:
            if user_id in self.target_users:
                return True
        
        # Check role targeting
        if self.target_roles and user_role:
            if user_role in self.target_roles:
                return True
        
        # Check lot targeting
        if self.target_lots and lot_id:
            if lot_id in self.target_lots:
                return True
        
        # If we have targets but none matched
        return False


class WebSocketEventBuilder:
    """Builder pattern for creating WebSocket events."""
    
    def __init__(self):
        self.event = WebSocketEvent()
    
    def event_type(self, event_type: WebSocketEventType) -> "WebSocketEventBuilder":
        """Set event type."""
        self.event.event_type = event_type
        return self
    
    def priority(self, priority: WebSocketEventPriority) -> "WebSocketEventBuilder":
        """Set event priority."""
        self.event.priority = priority
        return self
    
    def source(self, source: str) -> "WebSocketEventBuilder":
        """Set event source."""
        self.event.source = source
        return self
    
    def target_users(self, user_ids: List[str]) -> "WebSocketEventBuilder":
        """Set target users."""
        self.event.target_users = user_ids
        return self
    
    def target_user(self, user_id: str) -> "WebSocketEventBuilder":
        """Set single target user."""
        self.event.target_users = [user_id]
        return self
    
    def target_roles(self, roles: List[str]) -> "WebSocketEventBuilder":
        """Set target roles."""
        self.event.target_roles = roles
        return self
    
    def target_lots(self, lot_ids: List[str]) -> "WebSocketEventBuilder":
        """Set target lots."""
        self.event.target_lots = lot_ids
        return self
    
    def target_lot(self, lot_id: str) -> "WebSocketEventBuilder":
        """Set single target lot."""
        self.event.target_lots = [lot_id]
        return self
    
    def data(self, data: Dict[str, Any]) -> "WebSocketEventBuilder":
        """Set event data."""
        self.event.data = data
        return self
    
    def add_data(self, key: str, value: Any) -> "WebSocketEventBuilder":
        """Add single data field."""
        self.event.data[key] = value
        return self
    
    def message(self, message: str) -> "WebSocketEventBuilder":
        """Set event message."""
        self.event.message = message
        return self
    
    def expires_in_minutes(self, minutes: int) -> "WebSocketEventBuilder":
        """Set expiration time in minutes."""
        self.event.expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        return self
    
    def build(self) -> WebSocketEvent:
        """Build the event."""
        return self.event


class WebSocketEventFactory:
    """Factory for creating common WebSocket events."""
    
    @staticmethod
    def availability_update(lot_id: str, available_slots: int, total_slots: int, vehicle_type: Optional[str] = None) -> WebSocketEvent:
        """Create availability update event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.AVAILABILITY_UPDATE)
                .priority(WebSocketEventPriority.NORMAL)
                .source("availability_service")
                .target_lot(lot_id)
                .data({
                    "lot_id": lot_id,
                    "available_slots": available_slots,
                    "total_slots": total_slots,
                    "vehicle_type": vehicle_type,
                    "occupancy_rate": round((total_slots - available_slots) / total_slots * 100, 2) if total_slots > 0 else 0
                })
                .message(f"Parking availability updated: {available_slots}/{total_slots} slots available")
                .build())
    
    @staticmethod
    def slot_status_changed(slot_id: str, old_status: str, new_status: str, lot_id: str) -> WebSocketEvent:
        """Create slot status change event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.SLOT_STATUS_CHANGED)
                .priority(WebSocketEventPriority.NORMAL)
                .source("slot_service")
                .target_lot(lot_id)
                .data({
                    "slot_id": slot_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "lot_id": lot_id
                })
                .message(f"Slot {slot_id} changed from {old_status} to {new_status}")
                .build())
    
    @staticmethod
    def booking_created(booking_id: str, user_id: str, lot_id: str, slot_id: str) -> WebSocketEvent:
        """Create booking created event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.BOOKING_CREATED)
                .priority(WebSocketEventPriority.HIGH)
                .source("booking_service")
                .target_user(user_id)
                .target_lot(lot_id)
                .data({
                    "booking_id": booking_id,
                    "user_id": user_id,
                    "lot_id": lot_id,
                    "slot_id": slot_id
                })
                .message(f"New booking created: {booking_id}")
                .build())
    
    @staticmethod
    def booking_cancelled(booking_id: str, user_id: str, lot_id: str, slot_id: str, reason: str = "user_cancelled") -> WebSocketEvent:
        """Create booking cancelled event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.BOOKING_CANCELLED)
                .priority(WebSocketEventPriority.HIGH)
                .source("booking_service")
                .target_user(user_id)
                .target_lot(lot_id)
                .data({
                    "booking_id": booking_id,
                    "user_id": user_id,
                    "lot_id": lot_id,
                    "slot_id": slot_id,
                    "reason": reason
                })
                .message(f"Booking {booking_id} has been cancelled")
                .build())
    
    @staticmethod
    def user_notification(user_id: str, title: str, message: str, notification_type: str = "info") -> WebSocketEvent:
        """Create user notification event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.USER_NOTIFICATION)
                .priority(WebSocketEventPriority.NORMAL)
                .source("notification_service")
                .target_user(user_id)
                .data({
                    "title": title,
                    "notification_type": notification_type,  # info, warning, error, success
                    "action_required": False
                })
                .message(message)
                .expires_in_minutes(60)  # Notifications expire in 1 hour
                .build())
    
    @staticmethod
    def system_announcement(message: str, priority: WebSocketEventPriority = WebSocketEventPriority.NORMAL) -> WebSocketEvent:
        """Create system announcement event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.SYSTEM_ANNOUNCEMENT)
                .priority(priority)
                .source("system")
                .data({
                    "announcement_type": "general",
                    "action_required": False
                })
                .message(message)
                .build())
    
    @staticmethod
    def admin_alert(message: str, alert_type: str = "info", data: Optional[Dict[str, Any]] = None) -> WebSocketEvent:
        """Create admin alert event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.ADMIN_ALERT)
                .priority(WebSocketEventPriority.HIGH)
                .source("admin_service")
                .target_roles(["admin", "super_admin"])
                .data({
                    "alert_type": alert_type,  # info, warning, error, critical
                    "requires_action": alert_type in ["error", "critical"],
                    **(data or {})
                })
                .message(message)
                .build())
    
    @staticmethod
    def maintenance_alert(lot_id: str, slot_id: str, message: str, maintenance_type: str = "scheduled") -> WebSocketEvent:
        """Create maintenance alert event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.MAINTENANCE_ALERT)
                .priority(WebSocketEventPriority.HIGH)
                .source("maintenance_service")
                .target_roles(["admin", "maintenance"])
                .target_lot(lot_id)
                .data({
                    "lot_id": lot_id,
                    "slot_id": slot_id,
                    "maintenance_type": maintenance_type,  # scheduled, emergency, completed
                    "requires_action": maintenance_type == "emergency"
                })
                .message(message)
                .build())
    
    @staticmethod
    def heartbeat() -> WebSocketEvent:
        """Create heartbeat event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.HEARTBEAT)
                .priority(WebSocketEventPriority.LOW)
                .source("websocket_manager")
                .data({
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "status": "alive"
                })
                .message("Server heartbeat")
                .expires_in_minutes(1)
                .build())
    
    @staticmethod
    def create_user_notification(user_id: str, notification_data: Dict[str, Any]) -> WebSocketEvent:
        """Create user notification event."""
        return (WebSocketEventBuilder()
                .event_type(WebSocketEventType.USER_NOTIFICATION)
                .priority(WebSocketEventPriority.NORMAL)
                .source("notification_service")
                .target_user(user_id)
                .data({
                    "notification_id": notification_data.get("id"),
                    "notification_type": notification_data.get("type"),
                    "title": notification_data.get("title"),
                    "message": notification_data.get("message"),
                    "priority": notification_data.get("priority", "normal"),
                    "booking_id": notification_data.get("booking_id"),
                    "lot_id": notification_data.get("lot_id"),
                    "metadata": notification_data.get("metadata"),
                    "created_at": notification_data.get("created_at")
                })
                .message(notification_data.get("message", "New notification"))
                .build())


# Pydantic models for API serialization
class WebSocketEventResponse(BaseModel):
    """Response model for WebSocket events."""
    
    event_id: str
    event_type: str
    priority: str
    timestamp: str
    source: str
    target_users: Optional[List[str]] = None
    target_roles: Optional[List[str]] = None
    target_lots: Optional[List[str]] = None
    data: Dict[str, Any]
    message: Optional[str] = None
    
    @classmethod
    def from_websocket_event(cls, event: WebSocketEvent) -> "WebSocketEventResponse":
        """Create response from WebSocket event."""
        return cls(
            event_id=event.event_id,
            event_type=event.event_type.value,
            priority=event.priority.value,
            timestamp=event.timestamp.isoformat(),
            source=event.source,
            target_users=event.target_users,
            target_roles=event.target_roles,
            target_lots=event.target_lots,
            data=event.data,
            message=event.message
        )
