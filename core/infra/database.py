"""GAIA SQLite Database — canonical engine, Base, and schema init.

Canon References: C17 (Persistent Memory and Identity Architecture)
Issue: #440 (Session Bootstrap), #462 (GAIARuntime persistence)

This module is the single source of truth for:
  - The SQLAlchemy engine (SQLite, local dev; swap URL for prod)
  - DeclarativeBase (all ORM models must inherit from Base here)
  - init_db()  — creates all tables; idempotent, call on every boot
  - get_session() — returns a new SQLAlchemy 2.x Session

SQLAlchemy 2.x conventions used throughout:
  - engine.begin() for DDL / write transactions
  - Session(bind=engine) for ORM sessions
  - select() + session.scalars() for ORM queries
  - text() for raw SQL
Never use engine.execute(), session.query(), or 1.x-style implicit transactions.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_DB_URL = os.environ.get("GAIA_DB_URL", "sqlite:///./gaia.db")

engine = create_engine(
    _DB_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + threading
    echo=False,
)

# Enable WAL mode for SQLite — prevents read/write lock contention in tests
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
    if _DB_URL.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """All GAIA ORM models must inherit from this Base.

    Example::

        from core.infra.database import Base

        class ArchitectRecord(Base):
            __tablename__ = "architects"
            id: Mapped[str] = mapped_column(String, primary_key=True)
            name: Mapped[str] = mapped_column(String, nullable=False)
    """
    pass


# ---------------------------------------------------------------------------
# Schema init
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables registered on Base.metadata.

    Idempotent — safe to call on every boot.  Tables that already exist
    are not recreated or altered.  Call this before any repository or
    session code runs.

    Execution order during boot::

        1. init_db()               ← this function
        2. GAIANRegistry.list_all  ← Fix 4
        3. bootstrap_primordial_session()  ← Fix 5
    """
    # Import all ORM models here so their Table definitions are registered
    # on Base.metadata before create_all fires.  Add new model imports as
    # they are created.
    _import_all_models()
    Base.metadata.create_all(bind=engine)


def _import_all_models() -> None:
    """Side-effect import: registers ORM model Table objects on Base.metadata."""
    # pylint: disable=import-outside-toplevel,unused-import
    try:
        from core.session import architect as _architect_models  # noqa: F401
    except ImportError:
        pass
    try:
        from core.infra import sqlite_lifecycle_repository as _lc  # noqa: F401
    except ImportError:
        pass
    try:
        from core.infra import sqlite_stewardship_repository as _st  # noqa: F401
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context-manager yielding a SQLAlchemy 2.x Session.

    Usage::

        from core.infra.database import get_session

        with get_session() as session:
            stmt = select(MyModel).where(MyModel.id == target_id)
            result = session.scalars(stmt).first()
    """
    session = Session(bind=engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
