import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..core.db import get_db
from ..core.security import get_current_user
from ..models.event import Event, Participant
from ..schemas.event import EventCreate, EventOut, ConfirmRequest, EventPatch
from ..services.geocode import geocode_il

logger = logging.getLogger('events')

router = APIRouter(prefix="/events", tags=["events"])

@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    rows = db.execute(select(Event).order_by(Event.start_time.desc())).scalars().all()
    return rows

@router.get("/historical", response_model=list[EventOut])
def historical_events(db: Session = Depends(get_db)):
    now = datetime.now(tz=timezone.utc)
    rows = db.execute(select(Event).where(Event.end_time < now).order_by(Event.start_time.desc())).scalars().all()
    return rows

@router.post("", response_model=EventOut)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    # Geocode IL address
    lat, lng = geocode_il(payload.address)
    ev = Event(
        title=payload.title, description=payload.description,
        address=payload.address, lat=lat, lng=lng, country_code="IL",
        start_time=payload.start_time, end_time=payload.end_time,
        required_attendees=payload.required_attendees
    )
    db.add(ev); db.commit(); db.refresh(ev)
    return ev

@router.post("/{event_id}/confirm")
def confirm_attendance(event_id: int, req: ConfirmRequest, db: Session = Depends(get_db)):
    ev = db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    p = Participant(event_id=ev.id, display_name=req.display_name, lat=req.lat, lng=req.lng)
    db.add(p); db.commit(); db.refresh(p)
        logger.info("attendance.confirmed event_id=%s display_name=%s", ev.id, p.display_name)

    # Lock event for edit if threshold reached
    cnt = db.execute(select(Participant).where(Participant.event_id == ev.id)).scalars().all()
    if len(cnt) >= ev.required_attendees:
        ev.is_locked_for_edit = True
        db.add(ev); db.commit()

    # Broadcast via websocket (in-memory registry in app.state)
    try:
        from ..ws import broadcast_event
        broadcast_event({"type":"attendance_confirmed", "event_id": ev.id, "display_name": p.display_name})
    except Exception:
        pass
    return {"ok": True, "locked": ev.is_locked_for_edit}

@router.patch("/{event_id}", response_model=EventOut)
def patch_event(event_id: int, payload: EventPatch, db: Session = Depends(get_db)):
    ev = db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    if ev.is_locked_for_edit:
        raise HTTPException(status_code=409, detail="Event is locked for edit due to attendee threshold reached")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(ev, k, v)
    db.add(ev); db.commit(); db.refresh(ev)
    return ev

@router.get("/{event_id}/participants")
def list_participants(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    items = []
    for p in ev.participants:
        items.append({
            "id": p.id,
            "display_name": p.display_name,
            "lat": p.lat, "lng": p.lng,
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None
        })
    logger.info("participants.list event_id=%s count=%s", event_id, len(items))
    return items
