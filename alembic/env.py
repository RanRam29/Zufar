
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os, sys

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from backend.core.db import normalize_url
from backend.core.config import settings
from backend.models.base import Base
from backend.models import user, event  # noqa

target_metadata = Base.metadata

def run_migrations_offline():
    url = normalize_url(settings.DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    url = normalize_url(settings.DATABASE_URL)
    configuration["sqlalchemy.url"] = url
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
