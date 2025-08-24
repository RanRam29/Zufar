from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from ..db import get_session
from ..schemas import UserCreate, LoginJSON, Token
from ..auth import register_user, authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    user = register_user(session, payload)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(body: LoginJSON, session: Session = Depends(get_session)):
    user = authenticate_user(session, body.identifier, body.password)
    if not user:
        raise HTTPException(status_code=400, detail="invalid credentials")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
