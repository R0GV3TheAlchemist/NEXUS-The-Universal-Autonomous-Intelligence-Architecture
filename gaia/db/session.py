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
# Engine
# ---------------------------------------------------------------------------

_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    # Sensible local default so the app boots without env config.
    "sqlite+aiosqlite:///./gaia_dev.db",
)

# echo=False in production; set DATABASE_ECHO=1 for SQL logging during dev.
_ECHO = os.environ.get("DATABASE_ECHO", "0") == "1"

engine = create_async_engine(
    _DATABASE_URL,
    echo=_ECHO,
    # NullPool is safest for async; avoids connection reuse across event loops.
    pool_pre_ping=True,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for the duration of one request.

    Commits on clean exit; rolls back on any exception.
    Always closes the session when the request is done.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
