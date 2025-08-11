import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import get_password_hash, verify_password, create_access_token
from ..models.user import User
from ..schemas.auth import SignUp, Login, Token

logger = logging.getLogger("app.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
def signup(payload: SignUp, db: Session = Depends(get_db)) -> Token:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("user.created id=%s email=%s", user.id, user.email)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(payload: Login, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    logger.info("user.login id=%s email=%s", user.id, user.email)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}
