from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.database import get_db
from backend.users.models import User

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/users_count")
def users_count(db: Session = Depends(get_db)):
    return {"count": db.scalar(select(func.count()).select_from(User))}
