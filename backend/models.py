# C:\Zufar\backend\models.py

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    reporter: str
    severity: str
    event_time: datetime
    lat: float
    lng: float
    people_required: int = 1
    casualties_count: int = 0
    status: str = "active"  # active, closed
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # IMPORTANT: use typing.List[...] here (not built-in list[...] and no __future__ annotations)
    participants: List["Participant"] = Relationship(back_populates="event")


class Participant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    event_id: int = Field(foreign_key="event.id")
    event: Optional["Event"] = Relationship(back_populates="participants")
