
import logging
from typing import Set
from fastapi import WebSocket
log = logging.getLogger("zufar.ws")
class WSManager:
    def __init__(self): self._clients: Set[WebSocket] = set()
    async def connect(self, ws: WebSocket):
        await ws.accept(); self._clients.add(ws)
    def disconnect(self, ws: WebSocket):
        if ws in self._clients: self._clients.remove(ws)
    async def broadcast(self, message):
        for ws in list(self._clients):
            try: await ws.send_json(message)
            except Exception: log.warning("drop WS client"); self.disconnect(ws)
manager = WSManager()
