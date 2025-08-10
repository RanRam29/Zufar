"""Main FastAPI application for the casualty management system.

This module wires together the database, authentication, event
management and websocket broadcasting. It exposes REST endpoints for
user registration, login and event operations as well as a single
WebSocket endpoint for live updates. The frontend can authenticate
users, create and join events, update their location and receive
notifications about system changes.

To run the application locally:

.. code-block:: bash

    uvicorn repo.backend.app:app --reload

Ensure that the ``DATABASE_URL`` environment variable is set if you
intend to use a database other than the default SQLite file. On
Render and similar platforms the Postgres connection string is
provided automatically.
"""

from __future__ import annotations

import logging
import json
from datetime import datetime
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from .db import init_db, get_session
from .models import User, Event, Participant, UserPosition
from .schemas import (
    UserCreate,
    UserRead,
    Token,
    EventCreate,
    EventSummary,
    EventDetail,
    JoinEvent,
    UpdateRequired,
)
from .auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_active_user,
    get_current_active_dispatcher,
)
from .ws import manager
from fastapi.security import OAuth2PasswordRequestForm


log = logging.getLogger("zufar.app")

app = FastAPI(title="Casualty Management System")

# Serve frontend static files from the sibling ``frontend`` directory.
from pathlib import Path

FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend").resolve()
if not FRONTEND_DIR.exists():
    raise RuntimeError(f"Frontend directory not found: {FRONTEND_DIR}")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialise the database tables on startup."""
    init_db()
    log.info("Database initialised at %s", datetime.utcnow())


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    """Redirect root to the static frontend."""
    return """
    <meta http-equiv="refresh" content="0; url=/static/" />
    """


# -----------------------------------------------------------------------------
# Authentication endpoints
# -----------------------------------------------------------------------------


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, session: Session = Depends(get_session)) -> UserRead:
    """Register a new user.

    Passwords are hashed before storage. Duplicate usernames or emails
    result in a 400 error.
    """
    # Check uniqueness
    if session.exec(select(User).where(User.username == user_in.username)).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if session.exec(select(User).where(User.email == user_in.email)).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead.from_orm(user)


@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)) -> Token:
    """Authenticate a user and issue a JWT access token."""
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@app.get("/auth/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_active_user)) -> UserRead:
    """Return the current authenticated user."""
    return UserRead.from_orm(current_user)


# -----------------------------------------------------------------------------
# Event endpoints
# -----------------------------------------------------------------------------


@app.get("/events", response_model=List[EventSummary])
async def list_events(session: Session = Depends(get_session)) -> List[EventSummary]:
    """Return a summary of all events."""
    events = session.exec(select(Event)).all()
    summaries: List[EventSummary] = []
    for e in events:
        summaries.append(
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
        )
    return summaries


@app.get("/events/{event_id}", response_model=EventDetail)
async def get_event_detail(event_id: int, session: Session = Depends(get_session)) -> EventDetail:
    """Return detailed information about a specific event."""
    e = session.get(Event, event_id)
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
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


@app.post("/events", response_model=EventDetail, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_in: EventCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> EventDetail:
    """Create a new event and broadcast it to all connected clients."""
    e = Event(
        title=event_in.title,
        description=event_in.description,
        reporter=current_user.username,
        severity=event_in.severity,
        event_time=event_in.event_time,
        lat=event_in.lat,
        lng=event_in.lng,
        people_required=event_in.people_required,
        casualties_count=event_in.casualties_count,
        reporter_user_id=current_user.id,
    )
    session.add(e)
    session.commit()
    session.refresh(e)
    # Broadcast new event
    await manager.broadcast({"type": "new_event", "data": {"id": e.id, "title": e.title}})
    return await get_event_detail(e.id, session)


@app.post("/events/join", status_code=200)
async def join_event(
    join: JoinEvent,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Join an event if not already joined. Broadcast the update."""
    e = session.get(Event, join.event_id)
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    # Ensure not already joined
    if any(p.user_id == current_user.id for p in e.participants):
        raise HTTPException(status_code=400, detail="User already joined")
    # Ensure event not closed
    if e.status == "closed":
        raise HTTPException(status_code=400, detail="Event is closed")
    p = Participant(user_id=current_user.id, event_id=e.id)
    session.add(p)
    session.commit()
    session.refresh(e)
    # Close event if requirement met
    if len(e.participants) >= e.people_required:
        e.status = "closed"
        session.add(e)
        session.commit()
    await manager.broadcast(
        {
            "type": "event_update",
            "data": {
                "id": e.id,
                "status": e.status,
                "people_count": len(e.participants),
                "people_required": e.people_required,
            },
        }
    )
    return {"msg": f"{current_user.username} joined event {e.id}"}


@app.patch("/events/required", status_code=200)
async def update_required(
    payload: UpdateRequired,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_dispatcher),
) -> Dict[str, str]:
    """Update the required number of responders for an event."""
    e = session.get(Event, payload.event_id)
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    e.people_required = payload.new_required
    # Reopen event if necessary
    if len(e.participants) < e.people_required:
        e.status = "active"
    session.add(e)
    session.commit()
    await manager.broadcast(
        {
            "type": "event_update",
            "data": {
                "id": e.id,
                "status": e.status,
                "people_required": e.people_required,
                "people_count": len(e.participants),
            },
        }
    )
    return {"msg": "required updated"}


@app.get("/reports/summary")
async def report_summary(session: Session = Depends(get_session)) -> Dict[str, object]:
    """Return a summary report of events grouped by severity and total participations."""
    events = session.exec(select(Event)).all()
    severity_counts: Dict[str, int] = {}
    total_participations = 0
    for e in events:
        severity_counts[e.severity] = severity_counts.get(e.severity, 0) + 1
        total_participations += len(e.participants)
    return {
        "severity_summary": [{"severity": k, "count": v} for k, v in severity_counts.items()],
        "total_participations": total_participations,
    }


# -----------------------------------------------------------------------------
# WebSocket endpoint
# -----------------------------------------------------------------------------


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time notifications and positions."""
    # Expect token as query parameter for authentication
    token: Optional[str] = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    # Validate token and get user
    try:
        from .auth import decode_access_token

        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect(websocket, user_id)
    log.info("WebSocket connected: user %s", user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except Exception:
                continue
            # Handle position update messages
            if msg.get("type") == "position":
                lat = msg.get("lat")
                lng = msg.get("lng")
                if lat is None or lng is None:
                    continue
                # Persist or update user position
                # Directly create a new session for updating positions
                from .db import engine
                with Session(engine) as session:
                    pos = session.exec(select(UserPosition).where(UserPosition.user_id == user_id)).first()
                    if pos:
                        pos.lat = lat
                        pos.lng = lng
                        pos.updated_at = datetime.utcnow()
                        session.add(pos)
                    else:
                        new_pos = UserPosition(user_id=user_id, lat=lat, lng=lng)
                        session.add(new_pos)
                    session.commit()
                # Broadcast to all
                await manager.broadcast({"type": "position_update", "data": {"user_id": user_id, "lat": lat, "lng": lng}})
            else:
                # Echo any other messages for debugging
                await websocket.send_text(json.dumps({"type": "echo", "data": msg}))
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        log.info("WebSocket disconnected: user %s", user_id)