from __future__ import annotations
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

class EventCreate(BaseModel):
    title: str
    description: str
    reporter: str
    severity: str
    event_time: datetime
    lat: float
    lng: float
    people_required: int = Field(1, ge=1)
    casualties_count: int = Field(0, ge=0)

class EventSummary(BaseModel):
    id: int
    title: str
    severity: str
    event_time: datetime
    status: str
    people_required: int
    people_count: int
    casualties_count: int

class EventDetail(EventSummary):
    description: str
    reporter: str
    lat: float
    lng: float
    created_at: datetime

class JoinEvent(BaseModel):
    event_id: int
    username: str

class UpdateRequired(BaseModel):
    event_id: int
    new_required: int = Field(..., ge=1)
