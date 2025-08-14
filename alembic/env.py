# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so `backend` package is importable when Alembic runs
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- models metadata ---
from backend.db.base import Base  # noqa: E402
from backend.users import models as _users  # noqa: F401 (ensure models are imported)
target_metadata = Base.metadata

# --- Alembic config & logging ---
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- environment guards ---
RUNNING_IN_RENDER = bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))
REQUIRE_DATABASE_URL = os.getenv("REQUIRE_DATABASE_URL", "1") == "1"

def _normalize_url(url: str) -> str:
    # Render/SQLAlchemy 2: prefer psycopg3
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if "sslmode=" not in url and url.startswith("postgresql+psycopg://"):
        url = f"{url}{'&' if '?' in url else '?'}sslmode=require"
    return url

db_url = os.getenv("DATABASE_URL", "").strip()

# אל תאפשר נפילה ל-SQLite בפרוד
if not db_url and RUNNING_IN_RENDER and REQUIRE_DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set; refusing to run Alembic against SQLite in production.")

# בלוקאל בלבד מותר פולבאק
if not db_url:
    db_url = "sqlite:///./dev.db"

db_url = _normalize_url(db_url)
config.set_main_option("sqlalchemy.url", db_url)

def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # מאפשר ALTER ידידותי גם ב-SQLite אם צריך
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
