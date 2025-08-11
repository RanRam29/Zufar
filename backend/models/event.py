from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, DateTime, Float, Boolean
from datetime import datetime, timezone
from .base import Base

class Event(Base):
    __tablename__ = "event"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(2000))
    address: Mapped[str] = mapped_column(String(300))
    country_code: Mapped[str] = mapped_column(String(2), default="IL")
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    required_attendees: Mapped[int] = mapped_column(Integer, default=1)
    is_locked_for_edit: Mapped[bool] = mapped_column(Boolean, default=False)

    participants: Mapped[List["Participant"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

class Participant(Base):
    __tablename__ = "participant"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), index=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(200))
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))

    event: Mapped["Event"] = relationship(back_populates="participants")