"""WebSocket endpoints for real-time updates."""
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from datetime import datetime
import json
import asyncio
import logging

import redis.asyncio as aioredis

from src.core.security import verify_token
from src.config import settings

logger = logging.getLogger(__name__)


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


# =============================================================================
# Scan Progress Connection Manager
# =============================================================================

class ScanProgressConnectionManager:
    """Manages WebSocket connections for scan progress updates."""

    def __init__(self):
        # scan_id -> set of connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, scan_id: str) -> bool:
        """Accept and register a connection for a scan."""
        try:
            await websocket.accept()
            async with self._lock:
                if scan_id not in self.active_connections:
                    self.active_connections[scan_id] = set()
                self.active_connections[scan_id].add(websocket)
            return True
        except Exception:
            return False

    async def disconnect(self, websocket: WebSocket, scan_id: str):
        """Remove a connection."""
        async with self._lock:
            if scan_id in self.active_connections:
                self.active_connections[scan_id].discard(websocket)
                if not self.active_connections[scan_id]:
                    del self.active_connections[scan_id]

    async def broadcast_progress(self, scan_id: str, progress_data: dict):
        """Broadcast progress update to all connections for a scan."""
        if scan_id not in self.active_connections:
            return

        message = {
            "event": "scan:progress",
            "data": progress_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        message_str = json.dumps(message)
        dead_connections = set()

        for connection in self.active_connections.get(scan_id, set()).copy():
            try:
                await connection.send_text(message_str)
            except Exception:
                dead_connections.add(connection)

        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                for conn in dead_connections:
                    if scan_id in self.active_connections:
                        self.active_connections[scan_id].discard(conn)
                if scan_id in self.active_connections and not self.active_connections[scan_id]:
                    del self.active_connections[scan_id]

    def has_subscribers(self, scan_id: str) -> bool:
        """Check if a scan has active subscribers."""
        return scan_id in self.active_connections and len(self.active_connections[scan_id]) > 0


# Global scan progress manager instance
scan_progress_manager = ScanProgressConnectionManager()


@websocket_router.websocket("/scans/{scan_id}/progress")
async def scan_progress_websocket(
    websocket: WebSocket,
    scan_id: str,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time scan progress updates.

    Connect with: ws://host/api/v1/ws/scans/{scan_id}/progress?token=<jwt_token>

    Events sent to client:
    - scan:progress - Progress update (percent, hosts, status)
    - scan:started - Scan started
    - scan:completed - Scan completed with results
    - scan:failed - Scan failed with error
    - scan:cancelled - Scan was cancelled
    - connection:established - Connection confirmed
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

    # Connect to scan progress stream
    connected = await scan_progress_manager.connect(websocket, scan_id)
    if not connected:
        return

    # Send connection confirmation
    await websocket.send_text(json.dumps({
        "event": "connection:established",
        "data": {
            "scan_id": scan_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to scan progress stream",
        }
    }))

    # Send latest progress if available (for mid-scan connections)
    try:
        from src.core.scan_progress import get_latest_scan_progress
        latest = get_latest_scan_progress(scan_id)
        if latest:
            await websocket.send_text(json.dumps(latest))
    except Exception as e:
        logger.warning(f"Failed to get latest scan progress: {e}")

    # Create Redis subscriber for this scan
    redis_client = None
    pubsub = None
    redis_task = None

    async def listen_to_redis():
        """Listen to Redis pub/sub for scan progress updates."""
        nonlocal redis_client, pubsub
        try:
            redis_client = await aioredis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
            pubsub = redis_client.pubsub()
            channel = f"scan:progress:{scan_id}"
            await pubsub.subscribe(channel)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        await websocket.send_text(message["data"])
                    except Exception:
                        break  # WebSocket closed, exit loop
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
        finally:
            if pubsub:
                await pubsub.unsubscribe()
                await pubsub.close()
            if redis_client:
                await redis_client.close()

    async def handle_websocket_messages():
        """Handle incoming WebSocket messages (ping/pong)."""
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    try:
        # Run Redis listener and WebSocket handler concurrently
        redis_task = asyncio.create_task(listen_to_redis())
        ws_task = asyncio.create_task(handle_websocket_messages())

        # Wait for either task to complete (usually WebSocket disconnect)
        done, pending = await asyncio.wait(
            [redis_task, ws_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"Scan progress WebSocket error: {e}")
    finally:
        await scan_progress_manager.disconnect(websocket, scan_id)
        if redis_task and not redis_task.done():
            redis_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass


# =============================================================================
# Utility functions for broadcasting scan progress
# =============================================================================

async def broadcast_scan_progress(
    scan_id: str,
    progress_percent: int,
    state: str,
    hosts_total: int = 0,
    hosts_completed: int = 0,
    current_host: Optional[str] = None,
    message: Optional[str] = None,
):
    """Broadcast scan progress update."""
    await scan_progress_manager.broadcast_progress(scan_id, {
        "scan_id": scan_id,
        "progress_percent": progress_percent,
        "state": state,
        "hosts_total": hosts_total,
        "hosts_completed": hosts_completed,
        "current_host": current_host,
        "message": message,
    })


async def broadcast_scan_started(scan_id: str, scan_name: str, targets: list):
    """Broadcast scan started event."""
    if not scan_progress_manager.has_subscribers(scan_id):
        return

    message = {
        "event": "scan:started",
        "data": {
            "scan_id": scan_id,
            "scan_name": scan_name,
            "targets": targets,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    message_str = json.dumps(message)

    for connection in scan_progress_manager.active_connections.get(scan_id, set()).copy():
        try:
            await connection.send_text(message_str)
        except Exception:
            pass


async def broadcast_scan_completed(
    scan_id: str,
    total_findings: int,
    critical_count: int,
    high_count: int,
    medium_count: int,
    low_count: int,
    info_count: int,
):
    """Broadcast scan completed event."""
    if not scan_progress_manager.has_subscribers(scan_id):
        return

    message = {
        "event": "scan:completed",
        "data": {
            "scan_id": scan_id,
            "total_findings": total_findings,
            "severity_counts": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count,
                "info": info_count,
            },
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    message_str = json.dumps(message)

    for connection in scan_progress_manager.active_connections.get(scan_id, set()).copy():
        try:
            await connection.send_text(message_str)
        except Exception:
            pass


async def broadcast_scan_failed(scan_id: str, error_message: str):
    """Broadcast scan failed event."""
    if not scan_progress_manager.has_subscribers(scan_id):
        return

    message = {
        "event": "scan:failed",
        "data": {
            "scan_id": scan_id,
            "error": error_message,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    message_str = json.dumps(message)

    for connection in scan_progress_manager.active_connections.get(scan_id, set()).copy():
        try:
            await connection.send_text(message_str)
        except Exception:
            pass


async def broadcast_scan_cancelled(scan_id: str):
    """Broadcast scan cancelled event."""
    if not scan_progress_manager.has_subscribers(scan_id):
        return

    message = {
        "event": "scan:cancelled",
        "data": {
            "scan_id": scan_id,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    message_str = json.dumps(message)

    for connection in scan_progress_manager.active_connections.get(scan_id, set()).copy():
        try:
            await connection.send_text(message_str)
        except Exception:
            pass
