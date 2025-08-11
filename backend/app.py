import os, logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .core.db import engine
from .models.base import Base
from .routers import auth, events, health
from . import ws

# Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("app")

# DB init
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(events.router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")

@app.head("/", include_in_schema=False)
def root_head():
    return RedirectResponse(url="/static/index.html")

@app.exception_handler(Exception)
async def on_error(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)

@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    await ws.register(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive / ignore content
    except WebSocketDisconnect:
        await ws.unregister(websocket)