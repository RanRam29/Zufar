# backend/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, StringConstraints
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, ProgrammingError
from backend.database import get_db
from backend.users.models import User
from passlib.hash import bcrypt
import logging

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger(__name__)

Min1Str = Annotated[str, StringConstraints(min_length=1)]
Min6Str = Annotated[str, StringConstraints(min_length=6)]

class RegisterIn(BaseModel):
    email: EmailStr
    full_name: Optional[Min1Str] = None
    password: Min6Str

class RegisterOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]

@router.post("/register", response_model=RegisterOut)
def register_user(payload: RegisterIn, db: Session = Depends(get_db)):
    try:
        exists = db.query(User).filter(User.email == payload.email).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=bcrypt.hash(payload.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return RegisterOut(id=user.id, email=user.email, full_name=user.full_name)

    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        log.exception("IntegrityError on register")
        raise HTTPException(status_code=400, detail="Email already registered")
    except ProgrammingError:
        db.rollback()
        log.exception("ProgrammingError on register (table/column mismatch?)")
        raise HTTPException(
            status_code=500,
            detail="Database schema mismatch. Run migrations and align table names.",
        )
    except Exception:
        db.rollback()
        log.exception("Unexpected error on register")
        raise HTTPException(status_code=500, detail="Registration failed")
