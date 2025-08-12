from fastapi import FastAPI
from backend.database import on_startup_db_check
from backend.routes import auth as auth_routes
# השאר זמני בלבד, להסרה בפרוד
from backend.routes import debug as debug_routes  # remove in production if not needed

app = FastAPI()

# Startup: בדיקת DB/קונקטיביות
@app.on_event("startup")
def _startup():
    on_startup_db_check()

# Health/Liveness (Render קורא לזה בדיפולט)
@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}

# Root 200 (מונע 404 מה-HEAD / של Render)
@app.get("/", include_in_schema=False)
def root():
    return {"status": "up"}

# Routers
app.include_router(auth_routes.router)
app.include_router(debug_routes.router)  # הסר בפרוד
