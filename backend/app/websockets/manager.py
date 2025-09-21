"""WebSocket connection manager for real-time communication."""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Set, List, Optional, Any, Callable
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
import structlog

from fastapi import WebSocket, WebSocketDisconnect
from app.websockets.events import WebSocketEvent, WebSocketEventType, WebSocketEventPriority, WebSocketEventFactory
from app.core.exceptions import ValidationError

logger = structlog.get_logger(__name__)


class ConnectionState(str, Enum):
    """WebSocket connection states."""
    
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ClientConnection:
    """Represents a WebSocket client connection."""
    
    connection_id: str = field(default_factory=lambda: str(uuid4()))
    websocket: Optional[WebSocket] = None
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    lot_ids: Set[str] = field(default_factory=set)  # Subscribed parking lots
    connection_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state: ConnectionState = ConnectionState.CONNECTING
    
    # Connection metadata
    client_info: Dict[str, Any] = field(default_factory=dict)
    subscription_filters: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if connection is active."""
        return self.state == ConnectionState.CONNECTED and self.websocket is not None
    
    def is_authenticated(self) -> bool:
        """Check if connection is authenticated."""
        return self.user_id is not None
    
    def is_subscribed_to_lot(self, lot_id: str) -> bool:
        """Check if connection is subscribed to a specific lot."""
        return lot_id in self.lot_ids
    
    def update_heartbeat(self) -> None:
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.now(timezone.utc)
    
    def is_stale(self, timeout_minutes: int = 5) -> bool:
        """Check if connection is stale based on heartbeat."""
        threshold = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        return self.last_heartbeat < threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert connection to dictionary."""
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "lot_ids": list(self.lot_ids),
            "connection_time": self.connection_time.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "state": self.state.value,
            "is_active": self.is_active(),
            "is_authenticated": self.is_authenticated(),
            "client_info": self.client_info
        }


class WebSocketManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Provides connection lifecycle management, message routing,
    and real-time event broadcasting capabilities.
    """
    
    def __init__(self):
        # Connection storage
        self.connections: Dict[str, ClientConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.lot_connections: Dict[str, Set[str]] = {}   # lot_id -> connection_ids
        self.role_connections: Dict[str, Set[str]] = {}  # role -> connection_ids
        
        # Manager state
        self.active_connections_count = 0
        self.total_connections_count = 0
        self.start_time = datetime.now(timezone.utc)
        
        # Configuration
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 300  # 5 minutes
        self.max_connections_per_user = 5
        self.max_total_connections = 1000
        
        # Event handlers
        self.event_handlers: Dict[WebSocketEventType, List[Callable]] = {}
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        self.logger = logger.bind(service="WebSocketManager")
    
    async def start(self) -> None:
        """Start the WebSocket manager."""
        self.logger.info("Starting WebSocket manager")
        
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("WebSocket manager started successfully")
    
    async def stop(self) -> None:
        """Stop the WebSocket manager."""
        self.logger.info("Stopping WebSocket manager")
        
        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Disconnect all clients
        await self._disconnect_all_clients()
        
        self.logger.info("WebSocket manager stopped")
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        client_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
            user_id: Authenticated user ID
            user_role: User role (user, admin, etc.)
            client_info: Additional client information
            
        Returns:
            Connection ID
            
        Raises:
            ValidationError: If connection limits are exceeded
        """
        # Check connection limits
        if self.active_connections_count >= self.max_total_connections:
            raise ValidationError("Maximum concurrent connections exceeded")
        
        if user_id and len(self.user_connections.get(user_id, set())) >= self.max_connections_per_user:
            raise ValidationError("Maximum connections per user exceeded")
        
        # Accept WebSocket connection
        await websocket.accept()
        
        # Create connection object
        connection = ClientConnection(
            websocket=websocket,
            user_id=user_id,
            user_role=user_role,
            client_info=client_info or {},
            state=ConnectionState.CONNECTED
        )
        
        # Store connection
        self.connections[connection.connection_id] = connection
        self.active_connections_count += 1
        self.total_connections_count += 1
        
        # Index by user
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection.connection_id)
        
        # Index by role
        if user_role:
            if user_role not in self.role_connections:
                self.role_connections[user_role] = set()
            self.role_connections[user_role].add(connection.connection_id)
        
        self.logger.info(
            "WebSocket connection established",
            connection_id=connection.connection_id,
            user_id=user_id,
            user_role=user_role,
            active_connections=self.active_connections_count
        )
        
        # Send connection confirmation
        await self.send_to_connection(
            connection.connection_id,
            WebSocketEventFactory.user_notification(
                user_id=user_id or "anonymous",
                title="Connection Established",
                message="WebSocket connection established successfully",
                notification_type="success"
            )
        )
        
        return connection.connection_id
    
    async def disconnect(self, connection_id: str, reason: str = "client_disconnected") -> None:
        """
        Disconnect a WebSocket connection.
        
        Args:
            connection_id: Connection ID to disconnect
            reason: Disconnection reason
        """
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        try:
            # Update connection state
            connection.state = ConnectionState.DISCONNECTING
            
            # Close WebSocket if still open
            if connection.websocket and connection.is_active():
                await connection.websocket.close()
            
            # Remove from indexes
            await self._remove_connection_from_indexes(connection)
            
            # Remove from main storage
            del self.connections[connection_id]
            self.active_connections_count -= 1
            
            self.logger.info(
                "WebSocket connection disconnected",
                connection_id=connection_id,
                user_id=connection.user_id,
                reason=reason,
                active_connections=self.active_connections_count
            )
            
        except Exception as e:
            self.logger.error("Error disconnecting WebSocket", connection_id=connection_id, error=str(e))
    
    async def subscribe_to_lot(self, connection_id: str, lot_id: str) -> bool:
        """
        Subscribe a connection to parking lot updates.
        
        Args:
            connection_id: Connection ID
            lot_id: Parking lot ID
            
        Returns:
            True if successful
        """
        connection = self.connections.get(connection_id)
        if not connection or not connection.is_active():
            return False
        
        # Add to connection's lot subscriptions
        connection.lot_ids.add(lot_id)
        
        # Add to lot index
        if lot_id not in self.lot_connections:
            self.lot_connections[lot_id] = set()
        self.lot_connections[lot_id].add(connection_id)
        
        self.logger.debug(
            "Connection subscribed to lot",
            connection_id=connection_id,
            lot_id=lot_id,
            user_id=connection.user_id
        )
        
        return True
    
    async def unsubscribe_from_lot(self, connection_id: str, lot_id: str) -> bool:
        """
        Unsubscribe a connection from parking lot updates.
        
        Args:
            connection_id: Connection ID
            lot_id: Parking lot ID
            
        Returns:
            True if successful
        """
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        # Remove from connection's lot subscriptions
        connection.lot_ids.discard(lot_id)
        
        # Remove from lot index
        if lot_id in self.lot_connections:
            self.lot_connections[lot_id].discard(connection_id)
            if not self.lot_connections[lot_id]:
                del self.lot_connections[lot_id]
        
        self.logger.debug(
            "Connection unsubscribed from lot",
            connection_id=connection_id,
            lot_id=lot_id,
            user_id=connection.user_id
        )
        
        return True
    
    async def send_to_connection(self, connection_id: str, event: WebSocketEvent) -> bool:
        """
        Send event to a specific connection.
        
        Args:
            connection_id: Target connection ID
            event: Event to send
            
        Returns:
            True if sent successfully
        """
        connection = self.connections.get(connection_id)
        if not connection or not connection.is_active():
            return False
        
        try:
            await connection.websocket.send_text(event.to_json())
            connection.update_heartbeat()
            
            self.logger.debug(
                "Event sent to connection",
                connection_id=connection_id,
                event_type=event.event_type.value,
                event_id=event.event_id
            )
            
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id, "websocket_disconnect")
            return False
        except Exception as e:
            self.logger.error(
                "Failed to send event to connection",
                connection_id=connection_id,
                event_type=event.event_type.value,
                error=str(e)
            )
            return False
    
    async def send_to_user(self, user_id: str, event: WebSocketEvent) -> int:
        """
        Send event to all connections of a specific user.
        
        Args:
            user_id: Target user ID
            event: Event to send
            
        Returns:
            Number of connections the event was sent to
        """
        connection_ids = self.user_connections.get(user_id, set())
        sent_count = 0
        
        for connection_id in connection_ids.copy():
            if await self.send_to_connection(connection_id, event):
                sent_count += 1
        
        return sent_count
    
    async def send_user_notification(self, user_id: str, notification_data: Dict[str, Any]) -> int:
        """
        Send a user notification via WebSocket.
        
        Args:
            user_id: Target user ID
            notification_data: Notification data to send
            
        Returns:
            Number of connections the notification was sent to
        """
        try:
            # Create a user notification event
            event = WebSocketEventFactory.create_user_notification(
                user_id=user_id,
                notification_data=notification_data
            )
            
            # Send to all user connections
            sent_count = await self.send_to_user(user_id, event)
            
            logger.info(
                "User notification sent via WebSocket",
                user_id=user_id,
                notification_id=notification_data.get("id"),
                sent_to_connections=sent_count
            )
            
            return sent_count
            
        except Exception as e:
            logger.error(
                "Failed to send user notification via WebSocket",
                user_id=user_id,
                error=str(e)
            )
            return 0
    
    async def send_to_role(self, role: str, event: WebSocketEvent) -> int:
        """
        Send event to all connections with a specific role.
        
        Args:
            role: Target role
            event: Event to send
            
        Returns:
            Number of connections the event was sent to
        """
        connection_ids = self.role_connections.get(role, set())
        sent_count = 0
        
        for connection_id in connection_ids.copy():
            if await self.send_to_connection(connection_id, event):
                sent_count += 1
        
        return sent_count
    
    async def send_to_lot(self, lot_id: str, event: WebSocketEvent) -> int:
        """
        Send event to all connections subscribed to a specific lot.
        
        Args:
            lot_id: Target lot ID
            event: Event to send
            
        Returns:
            Number of connections the event was sent to
        """
        connection_ids = self.lot_connections.get(lot_id, set())
        sent_count = 0
        
        for connection_id in connection_ids.copy():
            if await self.send_to_connection(connection_id, event):
                sent_count += 1
        
        return sent_count
    
    async def broadcast(self, event: WebSocketEvent) -> int:
        """
        Broadcast event to all active connections or targeted subset.
        
        Args:
            event: Event to broadcast
            
        Returns:
            Number of connections the event was sent to
        """
        sent_count = 0
        
        # If event has specific targets, use targeted sending
        if event.target_users:
            for user_id in event.target_users:
                sent_count += await self.send_to_user(user_id, event)
        elif event.target_roles:
            for role in event.target_roles:
                sent_count += await self.send_to_role(role, event)
        elif event.target_lots:
            for lot_id in event.target_lots:
                sent_count += await self.send_to_lot(lot_id, event)
        else:
            # Broadcast to all connections
            for connection_id in list(self.connections.keys()):
                if await self.send_to_connection(connection_id, event):
                    sent_count += 1
        
        self.logger.info(
            "Event broadcasted",
            event_type=event.event_type.value,
            event_id=event.event_id,
            recipients=sent_count
        )
        
        return sent_count
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        uptime = datetime.now(timezone.utc) - self.start_time
        
        return {
            "active_connections": self.active_connections_count,
            "total_connections": self.total_connections_count,
            "authenticated_connections": len([c for c in self.connections.values() if c.is_authenticated()]),
            "lot_subscriptions": len(self.lot_connections),
            "role_distribution": {role: len(conn_ids) for role, conn_ids in self.role_connections.items()},
            "uptime_seconds": uptime.total_seconds(),
            "start_time": self.start_time.isoformat()
        }
    
    async def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection."""
        connection = self.connections.get(connection_id)
        if not connection:
            return None
        
        return connection.to_dict()
    
    async def register_event_handler(self, event_type: WebSocketEventType, handler: Callable) -> None:
        """Register an event handler for a specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _heartbeat_loop(self) -> None:
        """Background task for sending heartbeat messages."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send heartbeat to all connections
                heartbeat_event = WebSocketEventFactory.heartbeat()
                await self.broadcast(heartbeat_event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Heartbeat loop error", error=str(e))
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up stale connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Find stale connections
                stale_connections = [
                    conn_id for conn_id, conn in self.connections.items()
                    if conn.is_stale(self.connection_timeout // 60)
                ]
                
                # Disconnect stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id, "connection_timeout")
                
                if stale_connections:
                    self.logger.info("Cleaned up stale connections", count=len(stale_connections))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Cleanup loop error", error=str(e))
    
    async def _remove_connection_from_indexes(self, connection: ClientConnection) -> None:
        """Remove connection from all indexes."""
        connection_id = connection.connection_id
        
        # Remove from user connections
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Remove from role connections
        if connection.user_role and connection.user_role in self.role_connections:
            self.role_connections[connection.user_role].discard(connection_id)
            if not self.role_connections[connection.user_role]:
                del self.role_connections[connection.user_role]
        
        # Remove from lot connections
        for lot_id in connection.lot_ids:
            if lot_id in self.lot_connections:
                self.lot_connections[lot_id].discard(connection_id)
                if not self.lot_connections[lot_id]:
                    del self.lot_connections[lot_id]
    
    async def _disconnect_all_clients(self) -> None:
        """Disconnect all clients during shutdown."""
        connection_ids = list(self.connections.keys())
        
        for connection_id in connection_ids:
            await self.disconnect(connection_id, "server_shutdown")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


class ConnectionManager:
    """
    Simplified interface to WebSocket manager for backward compatibility.
    """
    
    def __init__(self):
        self.manager = websocket_manager
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connect a WebSocket client."""
        await self.manager.connect(websocket, user_id=client_id)
    
    async def disconnect(self, client_id: str) -> None:
        """Disconnect a WebSocket client."""
        # Find connection by user_id
        for connection in self.manager.connections.values():
            if connection.user_id == client_id:
                await self.manager.disconnect(connection.connection_id)
                break
    
    async def send_personal_message(self, message: str, client_id: str) -> None:
        """Send personal message to a client."""
        event = WebSocketEventFactory.user_notification(
            user_id=client_id,
            title="Personal Message",
            message=message
        )
        await self.manager.send_to_user(client_id, event)
    
    async def broadcast(self, message: str) -> None:
        """Broadcast message to all clients."""
        event = WebSocketEventFactory.system_announcement(message)
        await self.manager.broadcast(event)
