
from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import logging, time, json, httpx
from fastapi import FastAPI, HTTPException, Depends, WebSocket, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlmodel import select, Session
from .db import init_db, get_session, engine
from .models import Event, Participant, User
from .schemas import (UserCreate, UserRead, Token, EventCreate, EventSummary, EventDetail, JoinEvent, UpdateRequired, EventUpdate)
from .auth import (register_user, authenticate_user, create_access_token, get_current_user)
from .ws import manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")
log = logging.getLogger("zufar.app")

app = FastAPI(title="Casualty Management", version="1.2.0")

FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend").resolve()
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
    log.info("Static UI mounted at /static from %s", FRONTEND_DIR)
else:
    log.warning("Frontend directory not found: %s (UI disabled)", FRONTEND_DIR)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def access_log(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    if request.url.path != "/healthz":
        log.info("%s %s -> %s (%d ms)", request.method, request.url.path, getattr(resp, "status_code", "?"), int((time.perf_counter()-t0)*1000))
    return resp

@app.exception_handler(Exception)
async def on_error(request: Request, exc: Exception):
    log.exception("Unhandled %s %s", request.method, request.url.path)
    return JSONResponse(500, {"detail":"Internal server error"})

@app.on_event("startup")
def on_startup():
    init_db(); log.info("Startup: DB initialized")

@app.get("/healthz", status_code=status.HTTP_200_OK)
def healthz():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status":"ok","db":"up"}
    except Exception:
        log.exception("Healthz failure"); return {"status":"degraded","db":"down"}

@app.get("/", response_class=HTMLResponse)
def root_page():
    return '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=/static/">'

@app.post("/auth/register", response_model=UserRead, tags=["auth"])
def register(payload: UserCreate, session: Session = Depends(get_session)) -> UserRead:
    u = register_user(session, payload); log.info("register %s", u.username); return UserRead.model_validate(u)

@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)) -> Token:
    u = authenticate_user(session, form.username, form.password)
    if not u: raise HTTPException(401, "Invalid credentials")
    return Token(access_token=create_access_token(str(u.id)))

@app.get("/auth/me", response_model=UserRead, tags=["auth"])
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)

@app.get("/events", response_model=List[EventSummary])
def list_events(session: Session = Depends(get_session)) -> List[EventSummary]:
    rows = session.exec(select(Event)).all()
    return [EventSummary(id=e.id,title=e.title,severity=e.severity,event_time=e.event_time,status=e.status,
            people_required=e.people_required,people_count=len(e.participants),casualties_count=e.casualties_count,lat=e.lat,lng=e.lng) for e in rows]

@app.get("/events/history", response_model=List[EventSummary])
def list_history(limit: int = Query(100, ge=1, le=1000), session: Session = Depends(get_session)) -> List[EventSummary]:
    rows = session.exec(select(Event).where(Event.status=="closed").order_by(Event.event_time.desc())).all()[:limit]
    return [EventSummary(id=e.id,title=e.title,severity=e.severity,event_time=e.event_time,status=e.status,
            people_required=e.people_required,people_count=len(e.participants),casualties_count=e.casualties_count,lat=e.lat,lng=e.lng) for e in rows]

@app.get("/events/{event_id}", response_model=EventDetail)
def get_event(event_id: int, session: Session = Depends(get_session)) -> EventDetail:
    e = session.get(Event, event_id)
    if not e: raise HTTPException(404, "Event not found")
    return EventDetail(id=e.id,title=e.title,severity=e.severity,event_time=e.event_time,status=e.status,
        people_required=e.people_required,people_count=len(e.participants),casualties_count=e.casualties_count,
        description=e.description,reporter=e.reporter,lat=e.lat,lng=e.lng,created_at=e.created_at)

@app.post("/events", response_model=EventDetail)
async def create_event(payload: EventCreate, session: Session = Depends(get_session)) -> EventDetail:
    e = Event(**payload.model_dump()); session.add(e); session.commit(); session.refresh(e)
    try: await manager.broadcast({"type":"new_event","data":{"id":e.id,"title":e.title}})
    except Exception: pass
    return get_event(e.id, session)

@app.post("/events/join")
async def join_event(payload: JoinEvent, session: Session = Depends(get_session)) -> Dict[str, str]:
    e = session.get(Event, payload.event_id)
    if not e: raise HTTPException(404, "Event not found")
    if e.status == "closed": raise HTTPException(400, "Event is closed")
    if any(p.username==payload.username for p in e.participants): raise HTTPException(400, "User already joined")
    session.add(Participant(username=payload.username, event_id=e.id)); session.commit(); session.refresh(e)
    if len(e.participants) >= e.people_required and e.status != "closed": e.status="closed"; session.add(e); session.commit()
    try: await manager.broadcast({"type":"arrival","data":{"event_id":e.id,"username":payload.username,"people_count":len(e.participants),"people_required":e.people_required,"status":e.status}})
    except Exception: pass
    return {"msg": f"{payload.username} joined event {e.id}"}

@app.patch("/events/required")
async def update_required(payload: UpdateRequired, session: Session = Depends(get_session)) -> Dict[str, str]:
    e = session.get(Event, payload.event_id)
    if not e: raise HTTPException(404, "Event not found")
    e.people_required = payload.new_required
    if len(e.participants) < e.people_required: e.status="active"
    session.add(e); session.commit()
    try: await manager.broadcast({"type":"event_update","data":{"id":e.id,"status":e.status,"people_required":e.people_required,"people_count":len(e.participants)}})
    except Exception: pass
    return {"msg": "required updated"}

@app.patch("/events/{event_id}/edit", response_model=EventDetail)
def edit_event(event_id: int, payload: EventUpdate, session: Session = Depends(get_session)) -> EventDetail:
    e = session.get(Event, event_id)
    if not e: raise HTTPException(404, "Event not found")
    data = payload.model_dump(exclude_unset=True)
    for k,v in data.items(): setattr(e, k, v)
    session.add(e); session.commit(); session.refresh(e)
    return get_event(e.id, session)

@app.get("/events/geocode")
def geocode(address: str = Query(..., min_length=3)) -> Dict[str, float]:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": f"{address}, Israel", "format":"json", "limit":1}
    with httpx.Client(timeout=10, headers={"User-Agent":"ZufarApp/1.0"}) as client:
        r = client.get(url, params=params); r.raise_for_status()
        arr = r.json()
        if not arr: raise HTTPException(404, "Address not found")
        return {"lat": float(arr[0]["lat"]), "lng": float(arr[0]["lon"])}

@app.get("/reports/summary")
def report_summary(session: Session = Depends(get_session)) -> dict:
    rows = session.exec(select(Event)).all()
    sev, total = {}, 0
    for e in rows:
        sev[e.severity] = sev.get(e.severity, 0) + 1
        total += len(e.participants)
    return {"severity_summary":[{"severity":k,"count":v} for k,v in sev.items()],"total_participations":total}

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            try:
                raw = await ws.receive_text()
                await ws.send_json({"type":"echo","data":raw})
            except Exception:
                break
    finally:
        manager.disconnect(ws)
