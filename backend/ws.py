from __future__ import annotations
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

class WSManager:
    def __init__(self) -> None:
        self._clients: List[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.append(ws)
        # Immediate "connected" message to confirm channel
        await ws.send_json({"type": "connected", "data": {"clients": len(self._clients)}})

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._clients:
            self._clients.remove(ws)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        for ws in self._clients.copy():
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)

manager = WSManager()
