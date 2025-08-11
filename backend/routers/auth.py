from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from ..core.db import get_db
from ..core.security import create_access_token, get_password_hash, verify_password
from ..core.config import settings
from ..models.user import User
from ..schemas.auth import SignUp, Login, Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
def signup(payload: SignUp, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    u = User(email=payload.email, full_name=payload.full_name, password_hash=get_password_hash(payload.password))
    db.add(u)
    db.commit()
    db.refresh(u)
    token = create_access_token(str(u.id))
    return Token(access_token=token)

@router.post("/login", response_model=Token)
def login(payload: Login, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == payload.email).first()
    if not u or not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(u.id))
    return Token(access_token=token)