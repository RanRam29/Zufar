from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import events

app = FastAPI(title="Backend Service Fixed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)

@app.exception_handler(Exception)
async def on_error(request: Request, exc: Exception):
    return JSONResponse({"detail": "Internal server error"}, status_code=500)

@app.get("/healthz")
def healthz():
    return {"status": "up"}
