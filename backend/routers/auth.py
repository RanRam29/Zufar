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
    # אימייל ייחודי
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
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
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    logger.info("user.login id=%s email=%s", user.id, user.email)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}
