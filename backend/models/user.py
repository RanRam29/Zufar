# backend/models/user.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # מה שהראוטר והסכימות מצפים לו:
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)

    # אופציונלי, לשמירה על תיעוד זמנים
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
