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
from backend.db.base import Base
from backend.users import models as _users  # noqa: F401 ensure models are imported
target_metadata = Base.metadata

# --- Alembic config ---
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if "sslmode=" not in url and url.startswith("postgresql+psycopg://"):
        url = f"{url}{'&' if '?' in url else '?'}sslmode=require"
    return url

db_url = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
db_url = _normalize_url(db_url)
config.set_main_option("sqlalchemy.url", db_url)

def run_migrations_offline():
    context.configure(url=db_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section),
                                     prefix="sqlalchemy.",
                                     poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
