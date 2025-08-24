import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

# add repo root to path so "backend" can be imported when Alembic runs from /alembic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import models so their tables are registered on SQLModel.metadata
try:
    from backend import models as _models  # noqa: F401
    # If your models are split across modules, import them here to ensure they're discovered:
    # from backend.models import user, event  # noqa: F401
except Exception:
    # Don't crash if imports fail during non-autogenerate runs
    pass

config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prefer DATABASE_URL from env; fallback to alembic.ini
db_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Use SQLModel's metadata (covers both SQLModel and Declarative mixins)
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("No database URL provided. Set DATABASE_URL env var or sqlalchemy.url in alembic.ini")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    if not configuration.get("sqlalchemy.url"):
        raise RuntimeError("No database URL provided. Set DATABASE_URL env var or sqlalchemy.url in alembic.ini")
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
