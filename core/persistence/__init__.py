"""
GAIA OS Persistence Layer.

This package gives every in-memory OS structure a disk-backed
counterpart. Nothing in core/ is modified — persistence is
additive: a thin write-through / read-on-boot wrapper around
existing structures.

Modules
-------
store.py               — PersistenceStore: atomic JSON file I/O
memory.py              — MemoryPersistence: saves/loads MemoryStore fragments
identity.py            — IdentityPersistence: saves/loads GAIAN identity + genesis
registry.py            — RegistryPersistence: saves/loads GAIANRegistry
session.py             — SessionPersistence: saves/loads boot manifests
manager.py             — PersistenceManager: orchestrates all sub-stores,
                         called by PrimordialSession at boot and shutdown
postgres_repositories  — PostgresMemoryRepository, PostgresSearchRepository,
                         PostgresPool: Postgres-backed CRUD over the memories
                         and search_results tables.
repository_factory.py  — RepositoryFactory + Repositories: reads GAIA_DB_DSN
                         from the environment and builds the Postgres repos;
                         returns None when the env var is absent so callers
                         gracefully fall back to file-based stores.

Design
------
1. ATOMIC WRITES: Every write goes to a .tmp file first,
   then os.replace() renames it atomically. A crash mid-write
   never corrupts the existing state.
2. WRITE-THROUGH: Fragments are written to disk immediately
   on creation (not just at shutdown).
3. BOOT RESTORE: PersistenceManager.restore() is called
   during PrimordialSession Phase 3 (registry_restore) to
   reload all GAIANs, their identities, and their memories
   from disk before any session begins.
4. ZERO DEPENDENCIES (file-based path): Only Python stdlib
   (json, pathlib, os, uuid, datetime). No SQLite, no Redis,
   no ORM.
5. HUMAN-READABLE: All persisted data is UTF-8 JSON.
   A developer can inspect, back up, or migrate state
   with any text editor or `jq`.
6. OPTIONAL POSTGRES: Set GAIA_DB_DSN to a psycopg2-compatible
   connection string to activate Postgres-backed repositories.
   When the variable is absent the system runs unchanged using
   the file stores above.

Quick-start with Postgres
-------------------------
::

    import os
    from pathlib import Path
    from core.persistence import PersistenceManager, RepositoryFactory

    # Configure once at process start:
    os.environ["GAIA_DB_DSN"] = "postgresql://gaia:secret@localhost/gaia"
    repos   = RepositoryFactory.from_env()          # None if no DSN
    manager = PersistenceManager(root=Path("/data/gaia"), repos=repos)

    # During normal operation:
    if manager.postgres_enabled:
        memory = manager.memory_repo.get_memory(some_id)

    # At process exit:
    RepositoryFactory.close(manager.repos)          # safe no-op if None
"""

from .manager import PersistenceManager
from .store import PersistenceStore
from .memory import MemoryPersistence
from .identity import IdentityPersistence
from .registry import RegistryPersistence
from .session import SessionPersistence

# ---------------------------------------------------------------------------
# Optional Postgres layer — only imported when psycopg2 is available.
# This keeps the file-based path completely stdlib-clean and prevents
# collection-time ImportError when psycopg2 is not installed.
# ---------------------------------------------------------------------------
try:
    from .repository_factory import Repositories, RepositoryFactory
    from .postgres_repositories import (
        PostgresMemoryRepository,
        PostgresPool,
        PostgresSearchRepository,
    )
    _POSTGRES_AVAILABLE = True
except ImportError:
    RepositoryFactory = None  # type: ignore[assignment,misc]
    Repositories = None  # type: ignore[assignment,misc]
    PostgresPool = None  # type: ignore[assignment,misc]
    PostgresMemoryRepository = None  # type: ignore[assignment,misc]
    PostgresSearchRepository = None  # type: ignore[assignment,misc]
    _POSTGRES_AVAILABLE = False

__all__ = [
    # Core orchestrator
    "PersistenceManager",
    # Postgres factory & container (None when psycopg2 not installed)
    "RepositoryFactory",
    "Repositories",
    # Postgres repos (importable directly for type hints)
    "PostgresPool",
    "PostgresMemoryRepository",
    "PostgresSearchRepository",
    # File-based sub-stores
    "PersistenceStore",
    "MemoryPersistence",
    "IdentityPersistence",
    "RegistryPersistence",
    "SessionPersistence",
    # Availability flag
    "_POSTGRES_AVAILABLE",
]
