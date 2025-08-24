# backend/routes/auth.py
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, ProgrammingError

from backend.database import get_db
from backend.users.models import User  # Uses column "hashed_password"
from backend.security_simple import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class SignUp(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=256)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=256)

class Login(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=256)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: SignUp, db: Session = Depends(get_db)) -> Token:
    # Normalize email to lower
    email = payload.email.lower().strip()
    # Unique email enforced by DB (users.models.User has UniqueConstraint on email)
    user = User(email=email, full_name=payload.full_name, hashed_password=hash_password(payload.password))
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    except ProgrammingError as e:
        db.rollback()
        # Likely table/column mismatch – surface a pragmatic message
        raise HTTPException(status_code=500, detail=f"Database schema mismatch: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")
    token = create_access_token(str(user.id))
    return Token(access_token=token)

@router.post("/login", response_model=Token)
def login(payload: Login, db: Session = Depends(get_db)) -> Token:
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(str(user.id))
    return Token(access_token=token)
