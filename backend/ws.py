from typing import Set
from fastapi import WebSocket
from asyncio import Lock

connections: Set[WebSocket] = set()
_lock = Lock()

async def register(ws: WebSocket):
    await ws.accept()
    async with _lock:
        connections.add(ws)

async def unregister(ws: WebSocket):
    async with _lock:
        if ws in connections:
            connections.remove(ws)

async def broadcast(payload: dict):
    dead = []
    for ws in list(connections):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        await unregister(ws)

# helper for sync contexts (routers) - schedule send later
def broadcast_event(payload: dict):
    # Lazy import to avoid circular
    import anyio
    anyio.from_thread.run(broadcast, payload)