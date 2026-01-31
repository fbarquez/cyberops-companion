"""WebSocket endpoints for real-time updates."""
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from datetime import datetime
import json
import asyncio

from src.core.security import verify_token


websocket_router = APIRouter()


# =============================================================================
# Notification Connection Manager (User-specific connections)
# =============================================================================

class NotificationConnectionManager:
    """Manages WebSocket connections for user notifications."""

    def __init__(self):
        # user_id -> set of connections (user may have multiple tabs/devices)
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> bool:
        """Accept and register a connection for a user."""
        try:
            await websocket.accept()
            async with self._lock:
                if user_id not in self.active_connections:
                    self.active_connections[user_id] = set()
                self.active_connections[user_id].add(websocket)
            return True
        except Exception:
            return False

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a connection."""
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections for a specific user."""
        if user_id not in self.active_connections:
            return

        message_str = json.dumps(message)
        dead_connections = set()

        for connection in self.active_connections[user_id].copy():
            try:
                await connection.send_text(message_str)
            except Exception:
                dead_connections.add(connection)

        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                for conn in dead_connections:
                    self.active_connections[user_id].discard(conn)
                if not self.active_connections.get(user_id):
                    self.active_connections.pop(user_id, None)

    async def broadcast_to_users(self, user_ids: list[str], message: dict):
        """Broadcast message to multiple users."""
        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)

    def get_connected_users(self) -> list[str]:
        """Get list of connected user IDs."""
        return list(self.active_connections.keys())

    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user has active connections."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Global notification manager instance
notification_manager = NotificationConnectionManager()


@websocket_router.websocket("/notifications")
async def notification_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time user notifications.

    Connect with: ws://host/api/v1/ws/notifications?token=<jwt_token>

    Events sent to client:
    - notification:new - New notification created
    - notification:read - Notification marked as read
    - notification:deleted - Notification deleted
    - stats:updated - Notification stats changed
    - connection:established - Connection confirmed
    - connection:error - Connection error
    """
    # Authenticate via token query parameter
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    payload = verify_token(token, token_type="access")
    if not payload:
        await websocket.close(code=4002, reason="Invalid or expired token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4003, reason="Invalid token payload")
        return

    # Connect user
    connected = await notification_manager.connect(websocket, user_id)
    if not connected:
        return

    # Send connection confirmation
    await websocket.send_text(json.dumps({
        "event": "connection:established",
        "data": {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to notification stream",
        }
    }))

    try:
        while True:
            # Wait for messages (ping/pong, subscription changes)
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle ping/pong for connection keep-alive
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat(),
                }))

    except WebSocketDisconnect:
        await notification_manager.disconnect(websocket, user_id)
    except Exception:
        await notification_manager.disconnect(websocket, user_id)


# =============================================================================
# Utility functions for broadcasting notifications
# =============================================================================

async def broadcast_notification(
    user_id: str,
    notification_data: dict,
    event_type: str = "notification:new"
):
    """Broadcast a notification to a specific user."""
    await notification_manager.send_to_user(user_id, {
        "event": event_type,
        "data": notification_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_notification_to_users(
    user_ids: list[str],
    notification_data: dict,
    event_type: str = "notification:new"
):
    """Broadcast a notification to multiple users."""
    message = {
        "event": event_type,
        "data": notification_data,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await notification_manager.broadcast_to_users(user_ids, message)


async def broadcast_stats_update(user_id: str, stats: dict):
    """Broadcast updated notification stats to a user."""
    await notification_manager.send_to_user(user_id, {
        "event": "stats:updated",
        "data": stats,
        "timestamp": datetime.utcnow().isoformat(),
    })


# =============================================================================
# Incident Connection Manager (Existing functionality)
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        # incident_id -> set of connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, incident_id: str):
        """Accept and register a connection."""
        await websocket.accept()
        if incident_id not in self.active_connections:
            self.active_connections[incident_id] = set()
        self.active_connections[incident_id].add(websocket)

    def disconnect(self, websocket: WebSocket, incident_id: str):
        """Remove a connection."""
        if incident_id in self.active_connections:
            self.active_connections[incident_id].discard(websocket)
            if not self.active_connections[incident_id]:
                del self.active_connections[incident_id]

    async def broadcast(self, incident_id: str, message: dict):
        """Broadcast message to all connections for an incident."""
        if incident_id in self.active_connections:
            message_str = json.dumps(message)
            dead_connections = set()

            for connection in self.active_connections[incident_id]:
                try:
                    await connection.send_text(message_str)
                except Exception:
                    dead_connections.add(connection)

            # Clean up dead connections
            for conn in dead_connections:
                self.active_connections[incident_id].discard(conn)


manager = ConnectionManager()


@websocket_router.websocket("/incidents/{incident_id}")
async def incident_websocket(websocket: WebSocket, incident_id: str):
    """
    WebSocket endpoint for real-time incident updates.

    Events:
    - evidence:new - New evidence entry added
    - phase:changed - Phase changed
    - checklist:updated - Checklist item updated
    - decision:made - Decision recorded
    - user:joined - User connected
    - user:left - User disconnected
    """
    await manager.connect(websocket, incident_id)

    # Notify others of new connection
    await manager.broadcast(incident_id, {
        "event": "user:joined",
        "data": {"message": "A user joined the incident"},
    })

    try:
        while True:
            # Receive and potentially broadcast messages
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            else:
                # Broadcast to other users
                await manager.broadcast(incident_id, message)

    except WebSocketDisconnect:
        manager.disconnect(websocket, incident_id)
        await manager.broadcast(incident_id, {
            "event": "user:left",
            "data": {"message": "A user left the incident"},
        })


# Utility functions for broadcasting from other parts of the API
async def broadcast_evidence_added(incident_id: str, entry_id: str):
    """Broadcast new evidence entry."""
    await manager.broadcast(incident_id, {
        "event": "evidence:new",
        "data": {"entry_id": entry_id},
    })


async def broadcast_phase_changed(incident_id: str, old_phase: str, new_phase: str):
    """Broadcast phase change."""
    await manager.broadcast(incident_id, {
        "event": "phase:changed",
        "data": {"old_phase": old_phase, "new_phase": new_phase},
    })


async def broadcast_checklist_updated(incident_id: str, item_id: str, status: str):
    """Broadcast checklist update."""
    await manager.broadcast(incident_id, {
        "event": "checklist:updated",
        "data": {"item_id": item_id, "status": status},
    })


async def broadcast_decision_made(incident_id: str, node_id: str, option_id: str):
    """Broadcast decision made."""
    await manager.broadcast(incident_id, {
        "event": "decision:made",
        "data": {"node_id": node_id, "option_id": option_id},
    })
