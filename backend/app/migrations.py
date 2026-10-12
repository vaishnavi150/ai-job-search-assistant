"""Idempotent schema setup, run at startup.

`create_all` creates missing tables but never alters existing ones, so
columns added after the first deploy are added here. Each step checks the
live schema first, so it's safe to run on every boot against both SQLite
and Postgres.
"""
import logging

from sqlalchemy import inspect, text

from app.database import Base, engine
import app.models  # noqa: F401 - registers models on Base

logger = logging.getLogger(__name__)

# (table, column, DDL type + default) for columns added after v0.1.0
_ADDED_COLUMNS = [
    ("users", "token_version", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "password_changed_at", "TIMESTAMP"),
    ("applications", "job_url", "VARCHAR"),
]


def run_migrations() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table, column, ddl in _ADDED_COLUMNS:
            existing = {c["name"] for c in inspector.get_columns(table)}
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                logger.info("Added column %s.%s", table, column)
