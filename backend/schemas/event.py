from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# --------- Event creation / update ---------

class EventCreate(BaseModel):
    title: str
    description: str
    address: str
    start_time: datetime
    end_time: datetime
    required_attendees: int = Field(1, ge=1)


class EventPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# --------- Event read models ---------

class ParticipantOut(BaseModel):
    """Participant snapshot for attendees list / map."""
    display_name: str
    confirmed_at: Optional[datetime] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

    class Config:
        from_attributes = True


class EventOut(BaseModel):
    id: int
    title: str
    description: str
    address: str
    lat: float
    lng: float
    start_time: datetime
    end_time: datetime
    required_attendees: int
    is_locked_for_edit: bool
    # אופציונלי: רשימת משתתפים שאישרו (אם ה-API מחזיר)
    participants: Optional[List[ParticipantOut]] = None

    class Config:
        from_attributes = True


# --------- Commands / actions ---------

class AttendanceConfirm(BaseModel):
    """Body ל-/events/{id}/confirm"""
    display_name: str = Field(min_length=1, max_length=64)
    # אופציונלי: מיקום מאשר, אם נשלח מהלקוח
    lat: Optional[float] = None
    lng: Optional[float] = None


# --------- Backward-compat (אם הקוד הישן ייבא ConfirmRequest) ---------

class ConfirmRequest(AttendanceConfirm):
    """Alias לשמירת תאימות אם קוד קודם משתמש בשם הישן."""
    pass
