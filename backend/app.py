from fastapi import FastAPI
from backend.database import on_startup_db_check
from backend.routes import auth as auth_routes
from backend.routes import debug as debug_routes  # remove in production if not needed

app = FastAPI()

@app.on_event("startup")
def _startup():
    on_startup_db_check()

app.include_router(auth_routes.router)
app.include_router(debug_routes.router)
