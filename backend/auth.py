import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Union

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from .db import get_session
from .models import User
from .schemas import UserCreate

log = logging.getLogger("zufar.auth")

SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET") or "INSECURE-CHANGE-ME"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def _exp_delta(minutes: Optional[int] = None) -> timedelta:
    return timedelta(minutes=minutes or ACCESS_TOKEN_EXPIRE_MINUTES)

def create_access_token(subject: Union[int, str], minutes: Optional[int] = None) -> str:
    to_encode = {"sub": str(subject), "exp": datetime.utcnow() + _exp_delta(minutes)}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def _select_user_by_username(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username)).first()

def _select_user_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()

def register_user(session: Session, payload: UserCreate) -> User:
    email = (payload.email or "").strip().lower()
    username_from_payload = getattr(payload, "username", None)
    username = (username_from_payload or (email.split("@")[0] if email else None))

    if hasattr(User, "username") and username:
        if _select_user_by_username(session, username):
            raise HTTPException(status_code=400, detail="username already exists")

    if hasattr(User, "email") and email:
        if _select_user_by_email(session, email):
            raise HTTPException(status_code=400, detail="email already exists")

    user_kwargs = {}
    if hasattr(User, "username") and username:
        user_kwargs["username"] = username
    if hasattr(User, "email") and email:
        user_kwargs["email"] = email
    if hasattr(User, "full_name") and hasattr(payload, "full_name"):
        user_kwargs["full_name"] = getattr(payload, "full_name")

    user_kwargs["hashed_password"] = hash_password(payload.password)

    try:
        user = User(**user_kwargs)  # type: ignore[arg-type]
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception:
        session.rollback()
        log.exception("register_user failed")
        raise HTTPException(status_code=500, detail="Registration failed")

def authenticate_user(session: Session, identifier: str, password: str) -> Optional[User]:
    candidate: Optional[User] = None
    if hasattr(User, "username"):
        candidate = _select_user_by_username(session, identifier)
    if not candidate and hasattr(User, "email"):
        candidate = _select_user_by_email(session, identifier.lower())

    if not candidate:
        return None
    if not verify_password(password, candidate.hashed_password):
        return None
    return candidate

def get_current_user(
    token: str = Depends(oauth2),
    session: Session = Depends(get_session),
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        uid = int(sub)
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
