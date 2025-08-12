from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.users.schemas import UserCreate, UserOut
from backend.users.service import create_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, email=payload.email, full_name=payload.full_name, password=payload.password)
