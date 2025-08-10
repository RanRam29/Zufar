"""Pydantic schemas for request and response bodies.

These schemas define the structure of data exchanged between the
client and server. They are separate from the SQLModel database
models to avoid accidentally exposing internal fields (such as
password hashes) and to enforce validation rules. The schemas are
versioned in that they can evolve independently of the underlying
database models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, constr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "responder"


class UserCreate(UserBase):
    password: constr(min_length=6)


class UserRead(UserBase):
    id: int
    created_at: datetime


class EventCreate(BaseModel):
    title: str
    description: str
    severity: str
    lat: float
    lng: float
    people_required: int = Field(1, ge=1)
    casualties_count: int = Field(0, ge=0)
    event_time: datetime


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