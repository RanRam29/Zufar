from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, String, Boolean

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(
        sa_column=Column(String(255), unique=True, index=True, nullable=False)
    )
    full_name: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    hashed_password: str = Field(sa_column=Column(String(255), nullable=False))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
