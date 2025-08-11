import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routers import health, events

app = FastAPI(title="Backend Service (Fixed)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOW_ORIGINS", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(health.router)
app.include_router(events.router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")

@app.exception_handler(Exception)
async def on_error(request: Request, exc: Exception):
    return JSONResponse({"detail": "Internal server error"}, status_code=500)

@app.get("/api/version")
def version():
    return {"name": "Backend Service (Fixed)", "version": os.getenv("APP_VERSION", "0.1.0")}
