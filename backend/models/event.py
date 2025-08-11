from __future__ import annotations
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from .base import Base

class Event(Base):
    __tablename__ = "event"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    participants: Mapped[List["Participant"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

class Participant(Base):
    __tablename__ = "participant"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    event: Mapped["Event"] = relationship(back_populates="participants")
