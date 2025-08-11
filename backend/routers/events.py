from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..models.event import Event
from ..deps import get_session

router = APIRouter(prefix="/events", tags=["events"])

@router.get("")
def list_events(session: Session = Depends(get_session)):
    rows = session.query(Event).all()
    return [{"id": r.id, "name": r.name, "participants": len(r.participants)} for r in rows]

@router.get("/geocode")
def geocode(address: str = Query(..., min_length=3)):
    # Example fixed geocode
    return {"address": address, "lat": 32.0853, "lng": 34.7818}
