from __future__ import annotations

from typing import List, Dict
from pathlib import Path
from datetime import datetime
import json
import logging
import time

from fastapi import FastAPI, HTTPException, Depends, WebSocket, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlmodel import select, Session

from .db import init_db, get_session, engine
from .models import Event, Participant
from .schemas import EventCreate, EventSummary, EventDetail, JoinEvent, UpdateRequired
from .ws import manager

# --------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("zufar.app")

# --------------------------------------------------------------------
# App & Static Files
# --------------------------------------------------------------------
app = FastAPI(title="Casualty Management", version="1.0.0")

FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend").resolve()
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
    log.info("Static UI mounted at /static from %s", FRONTEND_DIR)
else:
    log.warning("Frontend directory not found: %s (UI disabled; APIs still available)", FRONTEND_DIR)

# --------------------------------------------------------------------
# CORS (relax for MVP; tighten for production)
# --------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------
# Minimal request logging middleware (duration + status)
# --------------------------------------------------------------------
@app.middleware("http")
async def access_log(request: Request, call_next):
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
        return response
    finally:
        dt_ms = int((time.perf_counter() - t0) * 1000)
        # avoid logging /healthz every second too noisily
        if request.url.path != "/healthz":
            log.info("%s %s -> %s (%d ms)",
                     request.method, request.url.path, getattr(response, "status_code", "?"), dt_ms)

# --------------------------------------------------------------------
# Global exception handler (don’t leak internals)
# --------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# --------------------------------------------------------------------
# Startup
# --------------------------------------------------------------------
@app.on_event("startup")
def on_startup() -> None:
    try:
        init_db()
        log.info("Startup: DB initialized")
    except Exception:
        # Keep process up; /healthz will expose DB state.
        log.exception("Startup failed during init_db()")

# --------------------------------------------------------------------
# Healthz (Render health check)
# --------------------------------------------------------------------
@app.get("/healthz", status_code=status.HTTP_200_OK)
def healthz():
    """
    Liveness/readiness probe.
    Always 200 to avoid flapping; payload indicates DB state.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "up"}
    except Exception:
        log.exception("Healthz DB check failed")
        return {"status": "degraded", "db": "down"}

# --------------------------------------------------------------------
# Root -> redirect to static UI (if present)
# --------------------------------------------------------------------
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

# --------------------------------------------------------------------
# Event APIs
# --------------------------------------------------------------------
@app.get("/events", response_model=List[EventSummary])
def list_events(session: Session = Depends(get_session)) -> List[EventSummary]:
    try:
        rows = session.exec(select(Event)).all()
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
            for e in rows
        ]
        log.info("GET /events -> %d items", len(out))
        return out
    except Exception:
        log.exception("GET /events failed")
        raise HTTPException(500, "Failed to list events")

@app.get("/events/{event_id}", response_model=EventDetail)
def get_event(event_id: int, session: Session = Depends(get_session)) -> EventDetail:
    try:
        e = session.get(Event, event_id)
        if not e:
            log.info("GET /events/%s -> 404", event_id)
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
        return detail
    except HTTPException:
        raise
    except Exception:
        log.exception("GET /events/%s failed", event_id)
        raise HTTPException(500, "Failed to retrieve event")

@app.post("/events", response_model=EventDetail)
async def create_event(payload: EventCreate, session: Session = Depends(get_session)) -> EventDetail:
    try:
        e = Event(**payload.model_dump())
        session.add(e)
        session.commit()
        session.refresh(e)
        log.info("POST /events created id=%s title=%s", e.id, e.title)
    except Exception:
        session.rollback()
        log.exception("POST /events insert failed")
        raise HTTPException(500, "Failed to create event")

    # Broadcast outside transaction; don’t fail API if WS has issues
    try:
        await manager.broadcast({"type": "new_event", "data": {"id": e.id, "title": e.title}})
    except Exception:
        log.exception("Broadcast new_event failed id=%s", e.id)

    # Return canonical detail
    return EventDetail(
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

@app.post("/events/join")
async def join_event(payload: JoinEvent, session: Session = Depends(get_session)) -> Dict[str, str]:
    try:
        e = session.get(Event, payload.event_id)
        if not e:
            log.info("POST /events/join -> 404 event_id=%s", payload.event_id)
            raise HTTPException(404, "Event not found")
        if e.status == "closed":
            raise HTTPException(400, "Event is closed")
        if any(p.username == payload.username for p in e.participants):
            raise HTTPException(400, "User already joined")

        p = Participant(username=payload.username, event_id=e.id)
        session.add(p)
        session.commit()
        session.refresh(e)

        if len(e.participants) >= e.people_required and e.status != "closed":
            e.status = "closed"
            session.add(e)
            session.commit()

        log.info(
            "JOIN event=%s by user=%s -> %d/%d status=%s",
            e.id, payload.username, len(e.participants), e.people_required, e.status
        )
    except HTTPException:
        raise
    except Exception:
        session.rollback()
        log.exception("POST /events/join failed event_id=%s", payload.event_id)
        raise HTTPException(500, "Failed to join event")

    try:
        await manager.broadcast({
            "type": "event_update",
            "data": {
                "id": e.id,
                "status": e.status,
                "people_count": len(e.participants),
                "people_required": e.people_required,
            },
        })
    except Exception:
        log.exception("Broadcast event_update failed event_id=%s", e.id)

    return {"msg": f"{payload.username} joined event {e.id}"}

@app.patch("/events/required")
async def update_required(payload: UpdateRequired, session: Session = Depends(get_session)) -> Dict[str, str]:
    try:
        e = session.get(Event, payload.event_id)
        if not e:
            raise HTTPException(404, "Event not found")
        e.people_required = payload.new_required
        if len(e.participants) < e.people_required:
            e.status = "active"
        session.add(e)
        session.commit()
        log.info("PATCH /events/required -> event=%s required=%d status=%s",
                 e.id, e.people_required, e.status)
    except HTTPException:
        raise
    except Exception:
        session.rollback()
        log.exception("PATCH /events/required failed event_id=%s", payload.event_id)
        raise HTTPException(500, "Failed to update requirement")

    try:
        await manager.broadcast({
            "type": "event_update",
            "data": {
                "id": e.id,
                "status": e.status,
                "people_required": e.people_required,
                "people_count": len(e.participants),
            },
        })
    except Exception:
        log.exception("Broadcast event_update failed event_id=%s", e.id)

    return {"msg": "required updated"}

@app.get("/reports/summary")
def report_summary(session: Session = Depends(get_session)) -> dict:
    try:
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
        log.info("GET /reports/summary -> %s", payload)
        return payload
    except Exception:
        log.exception("GET /reports/summary failed")
        raise HTTPException(500, "Failed to build report")

# --------------------------------------------------------------------
# WebSocket: /ws/events
# --------------------------------------------------------------------
@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await manager.connect(ws)
    log.info("WS connected (%d clients)", len(manager._clients))
    try:
        while True:
            # Read a message; treat any non-JSON as ping and echo back
            try:
                raw = await ws.receive_text()
            except Exception:
                break

            try:
                msg = json.loads(raw)
                # Future: handle typed messages here (e.g., position updates)
                await ws.send_json({"type": "ack", "data": msg.get("type", "unknown")})
            except Exception:
                try:
                    await ws.send_json({"type": "echo", "data": raw})
                except Exception:
                    log.warning("WS echo failed")
    except Exception:
        log.exception("WS loop crashed")
    finally:
        manager.disconnect(ws)
        log.info("WS disconnected (%d clients)", len(manager._clients))
