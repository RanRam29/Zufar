"""Database configuration for the casualty management application.

This module provides a SQLModel engine and helpers for creating
sessions. The database URL is read from the ``DATABASE_URL``
environment variable. For development the default is a SQLite file
named ``casualties.db`` in the current working directory. In
production (for example on Render.com) you should set
``DATABASE_URL`` to a PostgreSQL connection string.

The ``init_db`` function is called at application startup to create
tables if they do not already exist. For complex schema evolution
consider using Alembic migrations instead of automating table
creation.
"""

from __future__ import annotations

import os
from sqlmodel import SQLModel, create_engine, Session

# Determine the database URL. Prefer an environment variable so that
# containerised deployments (e.g. Render) can specify a Postgres
# connection string. Fallback to a local SQLite file for easy
# development.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./casualties.db")

# Create the engine. Pool pre ping ensures stale connections are
# refreshed before use. Additional ``connect_args`` are provided for
# SQLite because it requires special flags when used in multithreaded
# contexts. See SQLAlchemy documentation for details.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):  # SQLite needs check_same_thread
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)


def init_db() -> None:
    """Create all tables defined on the SQLModel metadata.

    In production this should be replaced with an explicit migration
    management tool such as Alembic. Automatic table creation is
    convenient during early prototyping but is not recommended for
    mature systems.
    """
    from . import models  # noqa: F401 – ensure model metadata is imported

    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Provide a new SQLModel session.

    FastAPI's dependency injection system will create a session per
    request when ``get_session`` is used as a dependency. The caller
    is responsible for closing the session when done; however
    FastAPI will manage this automatically when used as a dependency.
    """
    with Session(engine) as session:
        yield session