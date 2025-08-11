
import os, logging
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from .db import get_session
from .models import User
from .schemas import UserCreate

log = logging.getLogger("zufar.auth")
JWT_SECRET = os.getenv("JWT_SECRET", "INSECURE-CHANGE-ME")
ALG = "HS256"
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(p: str) -> str: return pwd.hash(p)
def verify_password(p: str, h: str) -> bool: return pwd.verify(p, h)

def create_access_token(sub: str, minutes: int = 60) -> str:
    payload = {"sub": sub, "exp": datetime.utcnow() + timedelta(minutes=minutes)}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALG)

def register_user(session: Session, payload: UserCreate) -> User:
    exists = session.exec(select(User).where(User.username == payload.username)).first()
    if exists: raise HTTPException(400, "username already exists")
    user = User(username=payload.username, email=payload.email, hashed_password=hash_password(payload.password))
    session.add(user); session.commit(); session.refresh(user)
    return user

def authenticate_user(session: Session, username: str, password: str) -> Optional[User]:
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password): return None
    return user

def get_current_user(token: str = Depends(oauth2), session: Session = Depends(get_session)) -> User:
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[ALG])
        uid = int(data.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(401, "Invalid token")
    user = session.get(User, uid)
    if not user: raise HTTPException(401, "User not found")
    return user
