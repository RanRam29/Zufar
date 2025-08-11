import os

def _normalize_db_url(raw: str) -> str:
    if not raw:
        return raw
    url = raw.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.endswith("/"):
        url = url[:-1]
    return url

from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

config = context.config
env_url = _normalize_db_url(os.getenv("DATABASE_URL", ""))
if env_url:
    config.set_main_option("sqlalchemy.url", env_url)
