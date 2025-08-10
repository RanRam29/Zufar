"""Backend package for casualty management application.

This package contains the FastAPI application along with all
database models, schemas, authentication helpers and websocket
utilities required to run the casualty management system. It is
structured to separate concerns clearly across modules:

* ``db.py`` – database engine and session management.
* ``models.py`` – SQLModel table definitions for users, events,
  participants and live positions.
* ``schemas.py`` – Pydantic models for request and response bodies.
* ``auth.py`` – password hashing, JWT creation/validation and
  authentication dependencies.
* ``ws.py`` – a simple websocket manager for broadcasting
  notifications and position updates.
* ``app.py`` – the FastAPI application exposing REST and websocket
  endpoints.

By importing from this package the top level app instance can be
discovered by Uvicorn without having to know the internal module
structure.
"""

from .app import app  # noqa: F401