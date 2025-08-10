from __future__ import annotations
from typing import List, Dict
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import select, Session
from datetime import datetime
import logging

from .db import init_db, get_session
from .models import Event, Participant
from .schemas import EventCreate, EventSummary, EventDetail, JoinEvent, UpdateRequired
from .ws import manager

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("zufar")

# --------------------------------------------------
# App & Static Files Mount
# --------------------------------------------------
app = FastAPI(title="Casualty Management MVP")

FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend").resolve()
if not FRONTEND_DIR.exists():
    raise RuntimeError(f"Frontend directory not found: {FRONTEND_DIR}")

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

# --------------------------------------------------
# CORS for local dev
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Startup event
# --------------------------------------------------
@app.on_event("startup")
def on_startup() -> None:
    init_db()
    log.info("DB initialized. Serving frontend from %s", FRONTEND_DIR)

# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def root_page() -> str:
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Casualty Management</title>
        <meta http-equiv="refresh" content="0; url=/static/">
      </head>
      <body>Loading UI…</body>
    </html>
    """

@app.get("/events", response_model=List[EventSummary])
def list_events(session: Session = Depends(get_session)) -> List[EventSummary]:
    events = session.exec(select(Event)).all()
    out = [
        EventSummary(
            id=e.id,
            title=e.title,
            severity=e.severity,
            event_time=e.event_time,
            status=e.status,
            people_required=e.people_required,
            people_count=len(e.participants),
            casualties_count=e.casualties_count,
        )
        for e in events
    ]
    log.info("List events -> %d items", len(out))
    return out

@app.get("/events/{event_id}", response_model=EventDetail)
def get_event(event_id: int, session: Session = Depends(get_session)) -> EventDetail:
    e = session.get(Event, event_id)
    if not e:
        raise HTTPException(404, "Event not found")
    detail = EventDetail(
        id=e.id,
        title=e.title,
        severity=e.severity,
        event_time=e.event_time,
        status=e.status,
        people_required=e.people_required,
        people_count=len(e.participants),
        casualties_count=e.casualties_count,
        description=e.description,
        reporter=e.reporter,
        lat=e.lat,
        lng=e.lng,
        created_at=e.created_at,
    )
    log.info("Get event %s", event_id)
    return detail

@app.post("/events", response_model=EventDetail)
async def create_event(payload: EventCreate, session: Session = Depends(get_session)) -> EventDetail:
    e = Event(**payload.model_dump())
    session.add(e)
    session.commit()
    session.refresh(e)
    await manager.broadcast({"type": "new_event", "data": {"id": e.id, "title": e.title}})
    log.info("Created event id=%s title=%s", e.id, e.title)
    return get_event(e.id, session)

@app.post("/events/join")
async def join_event(payload: JoinEvent, session: Session = Depends(get_session)) -> Dict[str, str]:
    e = session.get(Event, payload.event_id)
    if not e:
        raise HTTPException(404, "Event not found")
    if e.status == "closed":
        raise HTTPException(400, "Event is closed")
    if any(p.username == payload.username for p in e.participants):
        raise HTTPException(400, "User already joined")

    p = Participant(username=payload.username, event_id=e.id)
    session.add(p)
    session.commit()
    session.refresh(e)

    if len(e.participants) >= e.people_required:
        e.status = "closed"
        session.add(e)
        session.commit()

    await manager.broadcast({
        "type": "event_update",
        "data": {"id": e.id, "status": e.status, "people_count": len(e.participants), "people_required": e.people_required}
    })
    log.info("User %s joined event %s -> %d/%d", payload.username, e.id, len(e.participants), e.people_required)
    return {"msg": f"{payload.username} joined event {e.id}"}

@app.patch("/events/required")
async def update_required(payload: UpdateRequired, session: Session = Depends(get_session)) -> Dict[str, str]:
    e = session.get(Event, payload.event_id)
    if not e:
        raise HTTPException(404, "Event not found")
    e.people_required = payload.new_required
    if len(e.participants) < e.people_required:
        e.status = "active"
    session.add(e)
    session.commit()

    await manager.broadcast({
        "type": "event_update",
        "data": {"id": e.id, "status": e.status, "people_required": e.people_required, "people_count": len(e.participants)}
    })
    log.info("Updated required for event %s -> %d", e.id, e.people_required)
    return {"msg": "required updated"}

@app.get("/reports/summary")
def report_summary(session: Session = Depends(get_session)) -> dict:
    events = session.exec(select(Event)).all()
    severity_counts: dict[str, int] = {}
    total_participations = 0
    for e in events:
        severity_counts[e.severity] = severity_counts.get(e.severity, 0) + 1
        total_participations += len(e.participants)
    payload = {
        "severity_summary": [{"severity": k, "count": v} for k, v in severity_counts.items()],
        "total_participations": total_participations,
    }
    log.info("Report summary -> %s", payload)
    return payload

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await manager.connect(ws)
    log.info("WS connected (%d clients)", len(manager._clients))
    try:
        while True:
            # Echo any text to keep connection alive and for debugging
            msg = await ws.receive_text()
            await ws.send_json({"type": "echo", "data": msg})
    except Exception:
        manager.disconnect(ws)
        log.info("WS disconnected (%d clients)", len(manager._clients))
