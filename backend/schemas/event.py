from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class EventCreate(BaseModel):
    title: str
    description: str
    address: str
    start_time: datetime
    end_time: datetime
    required_attendees: int = Field(1, ge=1)

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
    class Config:
        from_attributes = True

class ConfirmRequest(BaseModel):
    display_name: str
    lat: Optional[float] = None
    lng: Optional[float] = None

class EventPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None