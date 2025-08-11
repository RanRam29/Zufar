from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/events")
def get_events():
    events = [{"id": 1, "name": "Sample Event"}]
    participants = [{"display_name": "User A"}, {"display_name": "User B"}]

    for p in participants:
        # הקפדה על 4 רווחים בלבד בהזחה
        logger.info("attendance.confirmed event_id=%s display_name=%s", events[0]["id"], p["display_name"])

    return {"events": events, "participants": participants}
