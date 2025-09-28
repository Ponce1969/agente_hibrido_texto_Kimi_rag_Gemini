"""
PostgreSQL engine and pgvector initialization (optional, hybrid DB).

This module will only create an engine if `settings.database_url_pg` is set.
It does not affect the current SQLite-backed chat history.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.adapters.config.settings import settings


_pg_engine: Optional[Engine] = None


def get_pg_engine() -> Optional[Engine]:
    """
    Return a singleton SQLAlchemy Engine for PostgreSQL when configured.
    If `settings.database_url_pg` is not set, returns None.
    """
    global _pg_engine
    if _pg_engine is not None:
        return _pg_engine

    url = settings.database_url_pg
    if not url:
        return None

    # Example URL: postgresql+psycopg2://user:password@postgres:5432/dbname
    _pg_engine = create_engine(url, echo=False, future=True)

    # Ensure pgvector extension exists
    try:
        with _pg_engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception:
        # In some hosted PG setups, enabling extensions requires superuser.
        # We'll ignore errors here and let table creation fail noisily later if needed.
        pass

    return _pg_engine
