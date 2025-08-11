
from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    severity: str = "low"
    event_time: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"
    people_required: int = 5
    casualties_count: int = 0
    description: Optional[str] = None
    reporter: Optional[str] = None
    lat: float = 31.0461
    lng: float = 34.8516
    created_at: datetime = Field(default_factory=datetime.utcnow)

    participants: List['Participant'] = Relationship(back_populates="event")

class Participant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    event_id: int = Field(foreign_key="event.id")
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    event: Optional[Event] = Relationship(back_populates="participants")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: EmailStr
    hashed_password: str
    role: str = "responder"
    created_at: datetime = Field(default_factory=datetime.utcnow)
