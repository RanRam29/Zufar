"""WebSocket manager for broadcasting notifications and position updates.

The ``ConnectionManager`` class maintains a mapping of active
WebSocket connections and associated user IDs. It exposes methods
for connecting clients, disconnecting them, and broadcasting messages
to all or specific subsets of clients.

Messages are encoded as JSON objects with a ``type`` field to
indicate their purpose. Clients can send JSON objects with
``type`` set to ``position`` to update their location. All
messages received from clients are echoed back for debugging.

The manager is intentionally simple; for production consider
features such as per-event rooms, message throttling and better
error handling.
"""

from __future__ import annotations

import json
from typing import Dict, Optional

from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections keyed by user ID."""

    def __init__(self) -> None:
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """Accept a WebSocket connection and register it under the user ID."""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        """Remove a connection from the active registry."""
        self.active_connections.pop(user_id, None)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON serialisable message to all connected clients."""
        data = json.dumps(message)
        for ws in list(self.active_connections.values()):
            try:
                await ws.send_text(data)
            except Exception:
                # If sending fails drop the connection
                user_id = None
                for uid, conn in self.active_connections.items():
                    if conn is ws:
                        user_id = uid
                        break
                if user_id is not None:
                    self.disconnect(user_id)


manager = ConnectionManager()