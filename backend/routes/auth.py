from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..db import get_session
from ..auth import register_user, authenticate_user, create_access_token
from ..schemas import UserCreate, LoginJSON, Token, UserRead

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    user = register_user(session, payload)
    return UserRead(id=user.id, email=user.email, full_name=user.full_name)  # type: ignore[arg-type]

@router.post("/login", response_model=Token)
def login(payload: LoginJSON, session: Session = Depends(get_session)):
    user = authenticate_user(session, payload.identifier, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)  # type: ignore[arg-type]
    return Token(access_token=token)
