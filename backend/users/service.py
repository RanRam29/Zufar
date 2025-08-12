from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from backend.users.models import User
from backend.security import hash_password

def create_user(db: Session, *, email: str, full_name: str | None, password: str) -> User:
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=email, full_name=full_name, hashed_password=hash_password(password))
    db.add(user)
    db.commit()      # Critical – otherwise the user isn't persisted
    db.refresh(user)
    return user
