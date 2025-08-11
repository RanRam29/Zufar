from __future__ import annotations
"""
Routes for event management.

This module implements the full lifecycle for events, including creation,
listing, confirmation of attendance and limited editing after enough users
have confirmed. It also exposes a simple geocoding helper for client‑side
use. All database interactions are performed with SQLAlchemy and the
Pydantic schemas defined in ``backend.schemas.event`` are used for request and
response validation.

Key behaviours:

* Anyone may list events and historical events.
* Authenticated users can create events. A geocoding lookup against
  OpenStreetMap is performed and only Israeli addresses are accepted.
* Events start in a locked state – editing is unavailable until the
  required number of participants have confirmed their attendance.
* Participants can confirm attendance without authentication.  Each
  confirmation records a display name and optional GPS coordinates.  When
  the confirmation threshold is reached the event is unlocked for editing.
* Authenticated users may edit unlocked events.  Only mutable fields
  (title, description and start/end times) are exposed; changing an
  event’s location or required attendee count is intentionally omitted
  to keep the workflow simple.
* WebSocket notifications are broadcast for new events and new
  confirmations.  See ``backend/ws.py`` for implementation.
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import get_current_user
from ..models.event import Event, Participant
from ..models.user import User
from ..schemas.event import EventCreate, EventOut, ConfirmRequest, EventPatch
from ..services.geocode import geocode_il
from ..ws import broadcast_event

import logging

router = APIRouter(prefix="/events", tags=["events"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)) -> List[EventOut]:
    """Return all events, regardless of their status.

    The client is responsible for differentiating between upcoming and
    historical events based on the ``start_time`` and ``end_time`` fields.
    """
    events = db.query(Event).all()
    return [EventOut.from_orm(ev) for ev in events]


@router.get("/historical", response_model=list[EventOut])
def historical_events(db: Session = Depends(get_db)) -> List[EventOut]:
    """Return events that ended before now.

    An event is considered historical if its ``end_time`` has passed in UTC.
    """
    now = datetime.now(timezone.utc)
    events = db.query(Event).filter(Event.end_time < now).all()
    return [EventOut.from_orm(ev) for ev in events]


@router.get("/geocode")
def geocode(address: str = Query(..., description="Free form address inside Israel")) -> dict[str, float]:
    """Geocode an Israeli address into latitude and longitude.

    This endpoint is a thin wrapper around the ``geocode_il`` service
    which ensures that only Israeli addresses are resolved.  A 400
    response is returned if the address cannot be resolved.
    """
    try:
        lat, lng = geocode_il(address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"lat": lat, "lng": lng}


@router.get("/{event_id}/participants")
def list_participants(event_id: int, db: Session = Depends(get_db)) -> list[dict[str, object]]:
    """Return all participants for a given event.

    Participants include the display name, optional coordinates and the
    timestamp when they confirmed.  A 404 response is returned if the
    event does not exist.
    """
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return [
        {
            "id": p.id,
            "display_name": p.display_name,
            "lat": p.lat,
            "lng": p.lng,
            "confirmed_at": p.confirmed_at,
        }
        for p in event.participants
    ]


@router.post("", response_model=EventOut)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EventOut:
    """Create a new event.

    The caller must be authenticated via Bearer JWT.  The supplied
    address is geocoded against OpenStreetMap and must reside in Israel.
    Newly created events are locked for editing until the required
    attendee threshold is reached.
    """
    # Validate temporal consistency
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")
    # Geocode and validate IL address
    try:
        lat, lng = geocode_il(payload.address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Build event model; initially locked for editing
    event = Event(
        title=payload.title,
        description=payload.description,
        address=payload.address,
        lat=lat,
        lng=lng,
        start_time=payload.start_time,
        end_time=payload.end_time,
        required_attendees=payload.required_attendees,
        is_locked_for_edit=True,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info(
        "event.created id=%s title=%s user_id=%s",
        event.id,
        event.title,
        user.id,
    )
    # Notify subscribers about the new event
    broadcast_event({"type": "event_created", "event_id": event.id, "title": event.title})
    return EventOut.from_orm(event)


@router.post("/{event_id}/confirm")
def confirm_attendance(
    event_id: int,
    payload: ConfirmRequest,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """Record a participant's confirmation of attendance.

    Any caller can confirm attendance.  The ``display_name`` field is
    mandatory; latitude and longitude are optional.  When the number of
    confirmations reaches the event's ``required_attendees`` and the
    event is still locked for editing, the event is unlocked.
    A push notification is sent for every confirmation.
    """
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not payload.display_name:
        raise HTTPException(status_code=400, detail="display_name is required")
    participant = Participant(
        event_id=event.id,
        user_id=None,
        display_name=payload.display_name,
        lat=payload.lat,
        lng=payload.lng,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    # Count confirmations and unlock event if threshold reached
    count = db.query(Participant).filter(Participant.event_id == event.id).count()
    if event.is_locked_for_edit and count >= event.required_attendees:
        event.is_locked_for_edit = False
        db.add(event)
        db.commit()
        logger.info(
            "event.unlocked id=%s attendees=%s threshold=%s",
            event.id,
            count,
            event.required_attendees,
        )
    logger.info(
        "attendance.confirmed event_id=%s display_name=%s",
        event.id,
        participant.display_name,
    )
    # Broadcast new attendance confirmation
    broadcast_event(
        {
            "type": "attendance_confirmed",
            "event_id": event.id,
            "display_name": participant.display_name,
        }
    )
    return {"ok": True}


@router.patch("/{event_id}", response_model=EventOut)
def edit_event(
    event_id: int,
    payload: EventPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EventOut:
    """Edit an existing event.

    Editing is only allowed after enough attendees have confirmed
    attendance.  The ``is_locked_for_edit`` flag controls this
    behaviour; if it is True, a 400 response is returned.  Only a
    subset of fields (title, description, start_time, end_time) may be
    modified.  Changing the location or required attendee count would
    require more complex business logic and is intentionally left out.
    """
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.is_locked_for_edit:
        raise HTTPException(
            status_code=400,
            detail="Event editing is locked until required attendees confirm",
        )
    updated = False
    if payload.title is not None:
        event.title = payload.title
        updated = True
    if payload.description is not None:
        event.description = payload.description
        updated = True
    if payload.start_time is not None:
        # Prevent start after end
        if event.end_time and payload.start_time >= event.end_time:
            raise HTTPException(status_code=400, detail="start_time must be before end_time")
        event.start_time = payload.start_time
        updated = True
    if payload.end_time is not None:
        if event.start_time and payload.end_time <= event.start_time:
            raise HTTPException(status_code=400, detail="end_time must be after start_time")
        event.end_time = payload.end_time
        updated = True
    if updated:
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info("event.updated id=%s user_id=%s", event.id, user.id)
    return EventOut.from_orm(event)