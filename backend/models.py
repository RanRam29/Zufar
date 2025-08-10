"""Database models for the casualty management application.

This module defines SQLModel tables for all persistent entities in
the system:

* ``User`` – accounts that can log in and perform actions. Users may
  report events, join events and share their location. A simple
  ``role`` attribute can distinguish dispatchers from responders.
* ``Event`` – an incident requiring assistance. Events have
  metadata such as severity, location and required responders.
* ``Participant`` – a join table recording which users have
  volunteered for which events.
* ``UserPosition`` – stores the most recent latitude and longitude
  of a user for use on the live map.

Relationships are defined bidirectionally so that related objects
load lazily when accessed. SQLModel's ``Relationship`` helper
automatically manages foreign key columns and back references.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    """Represents an account able to authenticate and interact with the system."""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str = Field(index=True)
    hashed_password: str
    role: str = Field(default="responder")  # e.g. dispatcher, responder
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    events: List["Event"] = Relationship(back_populates="reporter_user")
    participants: List["Participant"] = Relationship(back_populates="user")
    positions: List["UserPosition"] = Relationship(back_populates="user")


class Event(SQLModel, table=True):
    """Represents an incident requiring assistance."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    reporter: str  # free-form reporter name (for legacy/backwards compatibility)
    severity: str
    event_time: datetime
    lat: float
    lng: float
    people_required: int = Field(default=1)
    casualties_count: int = Field(default=0)
    status: str = Field(default="active")  # active or closed
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Reporter user relationship (nullable for backwards compatibility)
    reporter_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    reporter_user: Optional[User] = Relationship(back_populates="events")

    # Participants
    participants: List["Participant"] = Relationship(back_populates="event")


class Participant(SQLModel, table=True):
    """Associates a user with an event they have joined."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="participants")
    event: Optional[Event] = Relationship(back_populates="participants")


class UserPosition(SQLModel, table=True):
    """Stores the latest known position for a user."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    lat: float
    lng: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="positions")