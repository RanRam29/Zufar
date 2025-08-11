"""
Authentication endpoints.

This router implements user registration and login using JWT tokens.
Passwords are hashed with ``passlib`` and stored securely.  Registration
and login return a short‑lived bearer token that can be used to call
protected endpoints.  A minimal ``/ping`` endpoint is also provided for
health checking.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from ..models.user import User
from ..schemas.auth import SignUp, Login, Token

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/ping")
def ping() -> dict[str, str]:
    """Simple liveness check for the auth router."""
    return {"msg": "pong"}


@router.post("/signup", response_model=Token)
def signup(payload: SignUp, db: Session = Depends(get_db)) -> Token:
    """Register a new user.

    If the e‑mail address is already registered, a 400 error is raised.
    Upon successful registration, a JWT is returned so the user can
    continue interacting with the system without an additional login.
    """
    # Check for existing account
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("user.created id=%s email=%s", user.id, user.email)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(payload: Login, db: Session = Depends(get_db)) -> Token:
    """Authenticate an existing user.

    The provided e‑mail and password are validated against stored
    credentials.  A 400 error is returned for invalid credentials.  On
    success, a new JWT is issued.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    logger.info("user.login id=%s email=%s", user.id, user.email)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}