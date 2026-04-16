"""
Alembic migration environment.

Reads database URL from app settings and imports all SQLModel models
so that `alembic revision --autogenerate` can detect schema changes.

For offline generation, set ALEMBIC_DATABASE_URL to a SQLite path.
For production migrations, it auto-detects from .env settings.
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# If ALEMBIC_DATABASE_URL is set, use that (supports offline generation)
# Otherwise fall back to app settings
database_url = os.environ.get("ALEMBIC_DATABASE_URL")

if database_url is None:
    from src.adapters.config.settings import settings

    database_url = settings.effective_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", database_url)

# Import all SQLModel models so Alembic can detect them
from sqlmodel import SQLModel

from src.adapters.db.chat import ChatSession  # noqa: F401
from src.adapters.db.file_models import FileSection, FileUpload  # noqa: F401
from src.adapters.db.message import ChatMessage  # noqa: F401
from src.adapters.db.metrics_models import (  # noqa: F401
    AgentMetrics,
    DailyMetricsSummary,
    ErrorLog,
)
from src.domain.models.user import User  # noqa: F401

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL scripts)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to the database)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
