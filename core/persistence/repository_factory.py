"""RepositoryFactory — builds concrete repository instances from configuration.

The factory reads ``GAIA_DB_DSN`` from the environment (or accepts an explicit
DSN) and returns a :class:`Repositories` named-tuple that holds fully
initialised :class:`PostgresMemoryRepository` and
:class:`PostgresSearchRepository` instances backed by a shared
:class:`PostgresPool`.

When no DSN is configured the factory returns ``None``; callers should fall
back to the existing file-based stores in that case.  This keeps the
Postgres dependency strictly optional — the system runs without a database
in development and test environments.

Typical usage::

    from core.persistence.repository_factory import RepositoryFactory

    repos = RepositoryFactory.from_env()          # returns None if no DSN
    manager = PersistenceManager(root=data_dir, repos=repos)

Or for tests::

    repos = RepositoryFactory.from_dsn("postgresql://localhost/gaia_test")
    manager = PersistenceManager(root=tmp_path, repos=repos)

    # Teardown:
    RepositoryFactory.close(repos)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from .postgres_repositories import (
    PostgresMemoryRepository,
    PostgresPool,
    PostgresSearchRepository,
)

logger = logging.getLogger("gaia.persistence.factory")

# Environment variable the factory reads by default.
GAIA_DB_DSN_ENV = "GAIA_DB_DSN"


@dataclass(frozen=True)
class Repositories:
    """Container for all active repository instances.

    Attributes:
        memory: Postgres-backed memory CRUD repository.
        search: Postgres-backed search-history repository.
        pool:   Shared connection pool (hold a reference to allow
                graceful shutdown via :func:`RepositoryFactory.close`).
    """

    memory: PostgresMemoryRepository
    search: PostgresSearchRepository
    pool: PostgresPool


class RepositoryFactory:
    """Factory that wires together the Postgres pool and repository objects."""

    @classmethod
    def from_env(
        cls,
        *,
        minconn: int = 1,
        maxconn: int = 10,
    ) -> Optional[Repositories]:
        """Build repositories from the ``GAIA_DB_DSN`` environment variable.

        Returns ``None`` when the variable is absent or empty, signalling
        that the caller should use the file-based stores instead.

        Args:
            minconn: Minimum connections to keep open in the pool.
            maxconn: Maximum connections the pool may open.

        Returns:
            A :class:`Repositories` instance, or ``None``.
        """
        dsn = os.environ.get(GAIA_DB_DSN_ENV, "").strip()
        if not dsn:
            logger.debug(
                "RepositoryFactory: %s not set — using file-based stores.",
                GAIA_DB_DSN_ENV,
            )
            return None
        return cls.from_dsn(dsn, minconn=minconn, maxconn=maxconn)

    @classmethod
    def from_dsn(
        cls,
        dsn: str,
        *,
        minconn: int = 1,
        maxconn: int = 10,
    ) -> Repositories:
        """Build repositories from an explicit DSN string.

        Args:
            dsn:     A psycopg2-compatible connection string, e.g.
                     ``"postgresql://user:pass@host:5432/gaia"``.
            minconn: Minimum connections kept open in the pool.
            maxconn: Maximum connections the pool may open.

        Returns:
            A :class:`Repositories` instance.

        Raises:
            psycopg2.OperationalError: When the DSN is invalid or the
                database cannot be reached.
        """
        logger.info(
            "RepositoryFactory: connecting to Postgres (minconn=%d, maxconn=%d).",
            minconn,
            maxconn,
        )
        pool = PostgresPool(dsn=dsn, minconn=minconn, maxconn=maxconn)
        return Repositories(
            memory=PostgresMemoryRepository(pool),
            search=PostgresSearchRepository(pool),
            pool=pool,
        )

    @staticmethod
    def close(repos: Optional[Repositories]) -> None:
        """Gracefully close the connection pool held by *repos*.

        Safe to call with ``None`` (no-op) so callers do not need to
        check whether Postgres was configured before shutting down::

            RepositoryFactory.close(manager.repos)

        Args:
            repos: The :class:`Repositories` to close, or ``None``.
        """
        if repos is not None:
            repos.pool.close()
            logger.info("RepositoryFactory: connection pool closed.")
