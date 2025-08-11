from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from .base import Base

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(256))
    password_hash: Mapped[str] = mapped_column(String(256))