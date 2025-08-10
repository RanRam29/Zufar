"""
Casualty Management Application Prototype
----------------------------------------

This module implements a simplified version of the ZufaRav application as
described in the provided specification. The goal is to provide a working
prototype that demonstrates how the existing repository’s backend patterns
can be extended to meet the operational requirements for managing fatality
events. This implementation is self‑contained and does not require a
database; instead, it stores data in memory for demonstration purposes.

Key features implemented:

* Create an event with details such as description, location, number of
  casualties and the number of required responders (rabbis).
* Join an event: responders can accept the call to join an event. When
  the number of responders reaches the required count, the event is
  automatically closed.
* Update the required number of responders, with automatic reopening of
  closed events when the requirement increases.
* Confirm an event (e.g. by an admin or operations centre).
* Real‑time notifications to connected clients via WebSockets when a new
  event is created or its status changes.
* Basic reporting endpoints to list events and show summary statistics.

This file can be run directly with `uvicorn` for local testing:

    uvicorn casualty_management_app:app --reload

Note: This prototype omits certain advanced requirements (2FA, push
notifications on silent, screenshot prevention, etc.) due to
environmental constraints. These can be added by integrating with
appropriate mobile or web technologies.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Dict, List
from datetime import datetime
import uuid

app = FastAPI(title="ZufaRav Casualty Management Prototype")

# ----------------------------------------------------------------------------
# In‑memory data stores. In a production system these would be backed by a
# relational database such as PostgreSQL, as in the existing repository.
# ----------------------------------------------------------------------------
class EventRecord(BaseModel):
    """Internal model for storing event state.

    In addition to the basic event details, this model keeps track of
    participants and their individual statuses. The participants field
    maps a username to a status string (e.g. "dispatched", "enroute",
    "onscene", "completed"). This richer structure makes it possible
    to support the requirement for tracking responder progress through
    the dispatch, travel and on‑scene phases of an event. See
    ParticipantStatusUpdate for updating these values.
    """
    id: str
    title: str
    description: str
    reporter: str
    severity: str
    datetime: datetime
    lat: float
    lng: float
    people_required: int
    casualties_count: int
    created_at: datetime
    confirmed: bool = False
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    status: str = "active"  # active, closed
    # participants now maps username -> status
    participants: Dict[str, str] = {}

events: Dict[str, EventRecord] = {}
user_locations: Dict[str, Dict[str, float | str]] = {}

connected_websockets: List[WebSocket] = []

# ----------------------------------------------------------------------------
# API Models exposed to clients
# ----------------------------------------------------------------------------
class CreateEventRequest(BaseModel):
    title: str = Field(..., description="Short title for the event")
    description: str = Field(..., description="Brief description of the event")
    reporter: str = Field(..., description="Who reported the event (e.g. police, MDA)")
    severity: str = Field(..., description="Severity level of the event")
    datetime: datetime = Field(..., description="Scheduled or occurred time of the event")
    lat: float = Field(..., description="Latitude coordinate of the event location")
    lng: float = Field(..., description="Longitude coordinate of the event location")
    people_required: int = Field(1, description="Number of responders required for the event")
    casualties_count: int = Field(0, description="Number of casualties involved")

class JoinEventRequest(BaseModel):
    event_id: str = Field(..., description="ID of the event to join")
    username: str = Field(..., description="Identifier of the responder")

class UpdateRequiredRequest(BaseModel):
    event_id: str
    new_required: int

class ConfirmEventRequest(BaseModel):
    event_id: str
    username: str

class LocationUpdate(BaseModel):
    username: str
    lat: float
    lng: float
    timestamp: datetime | None = None

class EventSummary(BaseModel):
    id: str
    title: str
    severity: str
    datetime: datetime
    status: str
    people_required: int
    people_count: int
    casualties_count: int

def broadcast(message: dict) -> None:
    """
    Broadcast a JSON serialisable message to all connected WebSocket clients.

    Exceptions are caught and silenced; dead connections are removed.
    """
    for ws in connected_websockets.copy():
        try:
            app.loop.create_task(ws.send_json(message))
        except Exception:
            connected_websockets.remove(ws)

@app.post("/events/create", response_model=EventSummary)
def create_event(request: CreateEventRequest) -> EventSummary:
    """Create a new event and notify subscribers via WebSocket."""
    event_id = str(uuid.uuid4())
    record = EventRecord(
        id=event_id,
        title=request.title,
        description=request.description,
        reporter=request.reporter,
        severity=request.severity,
        datetime=request.datetime,
        lat=request.lat,
        lng=request.lng,
        people_required=request.people_required,
        casualties_count=request.casualties_count,
        created_at=datetime.utcnow(),
    )
    events[event_id] = record
    summary = EventSummary(
        id=record.id,
        title=record.title,
        severity=record.severity,
        datetime=record.datetime,
        status=record.status,
        people_required=record.people_required,
        people_count=len(record.participants),
        casualties_count=record.casualties_count,
    )
    # Notify clients
    broadcast({"type": "new_event", "data": summary.dict()})
    return summary

@app.get("/events/list", response_model=List[EventSummary])
def list_events() -> List[EventSummary]:
    """Return summaries of all events."""
    return [
        EventSummary(
            id=e.id,
            title=e.title,
            severity=e.severity,
            datetime=e.datetime,
            status=e.status,
            people_required=e.people_required,
            people_count=len(e.participants),
            casualties_count=e.casualties_count,
        )
        for e in events.values()
    ]

@app.post("/events/join")
def join_event(request: JoinEventRequest) -> dict:
    """
    Allow a responder to join an event. When a user joins, they are
    entered into the participants dictionary with an initial status
    of ``dispatched``. The event automatically closes once the
    required number of responders have joined. If the user has
    already joined, an error is raised.
    """
    event = events.get(request.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status == "closed":
        raise HTTPException(status_code=400, detail="Event is closed")
    if request.username in event.participants:
        raise HTTPException(status_code=400, detail="User already joined this event")
    # Register the participant with initial status
    event.participants[request.username] = "dispatched"
    # Close event if threshold met
    if len(event.participants) >= event.people_required:
        event.status = "closed"
    # Notify via broadcast
    broadcast({"type": "event_update", "data": {
        "id": event.id,
        "status": event.status,
        "people_count": len(event.participants),
        "people_required": event.people_required,
    }})
    return {"msg": f"{request.username} joined event {event.title}",
            "status": event.participants[request.username]}

@app.patch("/events/update_required")
def update_required(request: UpdateRequiredRequest) -> dict:
    """
    Update the number of required responders for an event. If the new
    requirement exceeds the number of already joined participants, the
    event will be reopened (status set to active).
    """
    event = events.get(request.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if request.new_required <= 0:
        raise HTTPException(status_code=400, detail="Required count must be positive")
    event.people_required = request.new_required
    if len(event.participants) < event.people_required:
        event.status = "active"
    else:
        event.status = "closed"
    broadcast({"type": "event_update", "data": {
        "id": event.id,
        "status": event.status,
        "people_required": event.people_required,
        "people_count": len(event.participants),
    }})
    return {"msg": f"Updated required responders to {event.people_required}"}

@app.post("/events/confirm")
def confirm_event(request: ConfirmEventRequest) -> dict:
    """Mark an event as confirmed by a specific user."""
    event = events.get(request.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.confirmed = True
    event.confirmed_by = request.username
    event.confirmed_at = datetime.utcnow()
    broadcast({"type": "event_confirmed", "data": {
        "id": event.id,
        "confirmed_by": event.confirmed_by,
        "confirmed_at": event.confirmed_at.isoformat(),
    }})
    return {"msg": f"Event '{event.title}' confirmed by {request.username}"}

@app.post("/tracking/update")
def update_location(loc: LocationUpdate) -> dict:
    """Update a responder’s location."""
    timestamp = loc.timestamp.isoformat() if loc.timestamp else datetime.utcnow().isoformat()
    user_locations[loc.username] = {
        "lat": loc.lat,
        "lng": loc.lng,
        "timestamp": timestamp,
    }
    broadcast({"type": "location_update", "data": {
        "username": loc.username,
        "lat": loc.lat,
        "lng": loc.lng,
        "timestamp": timestamp,
    }})
    return {"msg": f"Location updated for {loc.username}"}

@app.get("/reports/summary")
def report_summary() -> dict:
    """
    Generate basic statistics about events. Returns the count of events by
    severity and the total number of participations (joins) recorded.
    """
    severity_counts: Dict[str, int] = {}
    total_participations = 0
    for event in events.values():
        severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
        total_participations += len(event.participants)
    return {
        "severity_summary": [
            {"severity": sev, "count": cnt} for sev, cnt in severity_counts.items()
        ],
        "total_confirmations": total_participations,
    }

# --------------------------------------------------------------------------
# User and participant status management
# --------------------------------------------------------------------------
class User(BaseModel):
    """
    Simple user record storing a username and role. Roles can include
    ``responder`` (field staff such as rabbis), ``admin`` (authority to
    confirm events and change configuration) and ``dispatcher``
    (operations centre personnel). In a future production system this
    would be integrated with a proper authentication provider and
    multi‑factor authentication. For now it is purely in memory.
    """
    username: str
    role: str

class ParticipantStatusUpdate(BaseModel):
    """
    Request model for updating the status of a participant in an event.
    ``new_status`` should reflect the responder’s progress, e.g.
    ``enroute``, ``onscene``, ``completed``. The status value is not
    restricted here but could be validated against an allowed set in
    production.
    """
    event_id: str
    username: str
    new_status: str

class CasualtiesUpdate(BaseModel):
    """
    Request model for updating the casualty count and required
    responder count of an event. This enables dynamic scaling of
    responders based on the evolving situation, as required by the
    specification. The new required count must be positive.
    """
    event_id: str
    casualties_count: int
    people_required: int

# In-memory registry of users
users: Dict[str, User] = {}

@app.post("/users/register")
def register_user(user: User) -> dict:
    """Register a user with a role."""
    if user.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[user.username] = user
    return {"msg": f"User {user.username} registered as {user.role}"}

@app.get("/users/list", response_model=List[User])
def list_users() -> List[User]:
    """List all registered users."""
    return list(users.values())

@app.post("/events/update_status")
def update_participant_status(req: ParticipantStatusUpdate) -> dict:
    """
    Update the status of a participant in a given event. This is used to
    reflect the responder’s progress from dispatch through arrival and
    completion. If the participant is not part of the event, an error
    is returned.
    """
    event = events.get(req.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if req.username not in event.participants:
        raise HTTPException(status_code=404, detail="User not part of event")
    event.participants[req.username] = req.new_status
    broadcast({"type": "participant_status", "data": {
        "event_id": event.id,
        "username": req.username,
        "status": req.new_status,
    }})
    return {"msg": f"Status for {req.username} set to {req.new_status}"}

@app.post("/events/update_casualties")
def update_casualties(req: CasualtiesUpdate) -> dict:
    """
    Update the casualty count and required responder count for an event.
    If the new required count is greater than the number of current
    participants, the event is reopened; otherwise it remains closed.
    """
    event = events.get(req.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if req.people_required <= 0:
        raise HTTPException(status_code=400, detail="people_required must be positive")
    event.casualties_count = req.casualties_count
    event.people_required = req.people_required
    # Reevaluate status
    if len(event.participants) < event.people_required:
        event.status = "active"
    else:
        event.status = "closed"
    broadcast({"type": "event_update", "data": {
        "id": event.id,
        "status": event.status,
        "people_required": event.people_required,
        "people_count": len(event.participants),
        "casualties_count": event.casualties_count,
    }})
    return {"msg": "Event updated",
            "status": event.status,
            "casualties_count": event.casualties_count,
            "people_required": event.people_required}

@app.websocket("/ws/events")
async def websocket_endpoint(ws: WebSocket) -> None:
    """
    Accept WebSocket connections for real‑time event updates. Clients
    receive broadcast messages whenever events are created, updated or
    confirmed. A client must send messages periodically to keep the
    connection alive, but these messages are ignored.
    """
    await ws.accept()
    connected_websockets.append(ws)
    try:
        while True:
            await ws.receive_text()  # Keep the connection alive
    except WebSocketDisconnect:
        if ws in connected_websockets:
            connected_websockets.remove(ws)
