"""Async SQLAlchemy session factory and FastAPI dependency for GAIA-OS.

Configuration is driven entirely by the DATABASE_URL environment variable.
Example values:
    postgresql+asyncpg://user:pass@localhost:5432/gaia
    sqlite+aiosqlite:///./gaia_dev.db

Usage in a FastAPI route::

    from gaia.db.session import get_db
    from sqlalchemy.ext.asyncio import AsyncSession
    from fastapi import Depends

    async def my_route(db: AsyncSession = Depends(get_db)):
        ...
"""
from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# Engine — created lazily so that importing this module during test
# collection does not crash when the async driver (aiosqlite / asyncpg)
# is not yet installed.  The engine is built on first access via
# _get_engine(), which is called by AsyncSessionLocal.
# ---------------------------------------------------------------------------

_DATABASE_URL: str | None = None
_ECHO: bool = False
_engine = None
_session_factory = None


def _get_engine():
    global _engine, _DATABASE_URL, _ECHO
    if _engine is None:
        _DATABASE_URL = os.environ.get(
            "DATABASE_URL",
            # Sensible local default so the app boots without env config.
            "sqlite+aiosqlite:///./gaia_dev.db",
        )
        _ECHO = os.environ.get("DATABASE_ECHO", "0") == "1"
        _engine = create_async_engine(
            _DATABASE_URL,
            echo=_ECHO,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


# ---------------------------------------------------------------------------
# Public alias kept for backwards-compatibility with code that does:
#   from gaia.db.session import AsyncSessionLocal
# Access triggers lazy engine creation, which is fine at runtime.
# ---------------------------------------------------------------------------

class _LazySessionLocal:
    """Proxy that forwards __call__ / async-context-manager use to the
    real async_sessionmaker, created on first use."""

    def __call__(self, *args, **kwargs):
        return _get_session_factory()(*args, **kwargs)

    def __aenter__(self, *args, **kwargs):  # pragma: no cover
        return _get_session_factory().__aenter__(*args, **kwargs)


AsyncSessionLocal = _LazySessionLocal()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for the duration of one request.

    Commits on clean exit; rolls back on any exception.
    Always closes the session when the request is done.
    """
    async with _get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
