# backend/routers/events.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.event import Event, Participant
from backend.security_simple import get_current_user_id

router = APIRouter(prefix="/events", tags=["events"])

# ---------- Schemas (kept local to avoid external broken imports) ----------

class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    address: str = Field(..., min_length=1, max_length=300)
    start_time: datetime
    end_time: datetime
    lat: float
    lng: float

class EventPatch(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    address: Optional[str] = Field(None, min_length=1, max_length=300)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class ParticipantOut(BaseModel):
    id: int
    display_name: str
    user_id: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    confirmed_at: datetime

    class Config:
        from_attributes = True

class EventOut(BaseModel):
    id: int
    title: str
    description: str
    address: str
    country_code: str
    lat: float
    lng: float
    start_time: datetime
    end_time: datetime
    min_confirmations_for_edit: int
    is_locked_for_edit: bool
    created_by_user_id: Optional[int] = None
    participants: List[ParticipantOut] = []

    class Config:
        from_attributes = True

class ConfirmBody(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=64)
    lat: Optional[float] = None
    lng: Optional[float] = None

# ---------- Routes ----------

@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> EventOut:
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")
    ev = Event(
        title=payload.title,
        description=payload.description,
        address=payload.address,
        country_code="IL",
        lat=payload.lat,
        lng=payload.lng,
        start_time=payload.start_time,
        end_time=payload.end_time,
        min_confirmations_for_edit=3,
        is_locked_for_edit=False,
        created_by_user_id=user_id,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return EventOut.model_validate(ev)

@router.get("", response_model=List[EventOut])
def list_events(db: Session = Depends(get_db)) -> List[EventOut]:
    now = datetime.now(timezone.utc)
    rows = db.query(Event).filter(Event.end_time >= now).order_by(Event.start_time.asc()).all()
    return [EventOut.model_validate(r) for r in rows]

@router.get("/historical", response_model=List[EventOut])
def list_historical(db: Session = Depends(get_db)) -> List[EventOut]:
    now = datetime.now(timezone.utc)
    rows = db.query(Event).filter(Event.end_time < now).order_by(Event.start_time.desc()).all()
    return [EventOut.model_validate(r) for r in rows]

@router.post("/{event_id}/confirm", response_model=EventOut)
def confirm_attendance(event_id: int, body: ConfirmBody, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> EventOut:
    ev = db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    part = Participant(event_id=event_id, user_id=user_id, display_name=body.display_name, lat=body.lat, lng=body.lng)
    db.add(part)
    db.flush()
    # lock logic: once we have enough confirmations, allow edits (or lock? per original requirement: allow edit after enough users confirm)
    cnt = db.query(Participant).filter(Participant.event_id == event_id).count()
    ev.is_locked_for_edit = False if cnt >= ev.min_confirmations_for_edit else True
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return EventOut.model_validate(ev)

@router.patch("/{event_id}", response_model=EventOut)
def edit_event(event_id: int, body: EventPatch, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> EventOut:
    ev = db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    # only allow edit once enough people confirmed (is_locked_for_edit == False)
    if ev.is_locked_for_edit:
        raise HTTPException(status_code=400, detail="Editing is locked until enough confirmations are received")
    # author can edit; optionally enforce creator check
    if ev.created_by_user_id and ev.created_by_user_id != user_id:
        raise HTTPException(status_code=403, detail="Only the creator can edit the event")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ev, field, value)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return EventOut.model_validate(ev)
