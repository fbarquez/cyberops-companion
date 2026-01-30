"""WebSocket endpoints for real-time updates."""
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json


websocket_router = APIRouter()


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
