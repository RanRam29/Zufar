import os

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Event Console")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-prod")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    ALGORITHM: str = "HS256"
    ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    NOMINATIM_URL: str = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")

settings = Settings()