
from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=6)

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    class Config: from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class EventCreate(BaseModel):
    title: str
    severity: str = Field("low", pattern="^(low|medium|high)$")
    description: Optional[str] = None
    address: Optional[str] = None
    lat: float
    lng: float
    people_required: int = Field(ge=1, default=5)
    casualties_count: int = Field(ge=0, default=0)

class EventSummary(BaseModel):
    id: int
    title: str
    severity: str
    event_time: datetime
    status: str
    people_required: int
    people_count: int
    casualties_count: int
    lat: float
    lng: float
    class Config: from_attributes = True

class EventDetail(BaseModel):
    id: int
    title: str
    severity: str
    event_time: datetime
    status: str
    people_required: int
    people_count: int
    casualties_count: int
    description: Optional[str] = None
    reporter: Optional[str] = None
    lat: float
    lng: float
    created_at: datetime
    class Config: from_attributes = True

class JoinEvent(BaseModel):
    event_id: int
    username: str

class UpdateRequired(BaseModel):
    event_id: int
    new_required: int = Field(..., ge=1)

class EventUpdate(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    description: Optional[str] = None
    people_required: Optional[int] = Field(None, ge=1)
    casualties_count: Optional[int] = Field(None, ge=0)
    lat: Optional[float] = None
    lng: Optional[float] = None
