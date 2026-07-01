"""
core/storage/sqlite_backend.py
==============================
SQLiteBackend — StorageBackend implementation backed by SQLite.

This is the default backend for GAIA-OS.  It preserves all existing
behaviour and requires no additional dependencies beyond Python's stdlib.

Thread safety
-------------
SQLite connections are NOT thread-safe.  This backend creates one
connection per-thread via threading.local(), so it is safe to call from
multiple asyncio tasks (which run in a thread pool via run_in_executor).

All async methods delegate blocking I/O to asyncio's default thread-pool
executor so the event loop is never blocked during database operations.

Performance
-----------
- WAL mode enabled (Write-Ahead Logging) for concurrent read performance
- Prepared statement cache via the connection object
- Single table `kv_store(key TEXT PRIMARY KEY, value BLOB, expires_at REAL)`
  Expired rows are pruned on every `query()` call (lazy expiry).

Phase 2 / 3 note:
    This backend will remain the default for single-node and development
    deployments.  Planetary-scale backends (CockroachDB, ScyllaDB, IPFS)
    are loaded via the factory in factory.py when configured.

Issue: #281
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path

from .backend import StorageWriteError

logger = logging.getLogger("gaia.storage.sqlite")

_DDL = """
CREATE TABLE IF NOT EXISTS kv_store (
    key         TEXT    PRIMARY KEY,
    value       BLOB    NOT NULL,
    expires_at  REAL    DEFAULT NULL  -- UNIX timestamp, NULL = no expiry
);
CREATE INDEX IF NOT EXISTS idx_kv_key_prefix ON kv_store (key);
"""


class SQLiteBackend:
    """
    SQLite-backed StorageBackend.

    Args:
        db_path:   Path to the SQLite file.  Expanded with os.path.expanduser.
                   Defaults to ~/.gaia/storage.db
        loop:      Event loop to use for run_in_executor.  Defaults to the
                   running loop at time of first call.
    """

    def __init__(
        self,
        db_path: str = "~/.gaia/storage.db",
    ) -> None:
        self._db_path = os.path.expanduser(db_path)
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()  # per-thread connection
        self._closed = False
        # Ensure schema exists on the calling thread at init time
        conn = self._connect()
        conn.executescript(_DDL)
        conn.commit()
        logger.debug(f"[SQLiteBackend] Initialised: {self._db_path}")

    # ── Connection management ────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        """Return the per-thread SQLite connection, creating it if needed."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
                timeout=30.0,
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-4096")  # 4 MB page cache
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    # ── Sync internals (run inside executor) ─────────────────────────────

    def _sync_put(self, key: str, value: bytes, ttl: int | None) -> None:
        expires_at = (time.time() + ttl) if ttl is not None else None
        try:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO kv_store (key, value, expires_at) "
                "VALUES (?, ?, ?)",
                (key, value, expires_at),
            )
            conn.commit()
        except sqlite3.Error as exc:
            raise StorageWriteError(f"SQLite put failed for {key!r}: {exc}") from exc

    def _sync_get(self, key: str) -> bytes | None:
        conn = self._connect()
        row = conn.execute(
            "SELECT value, expires_at FROM kv_store WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        if row["expires_at"] is not None and time.time() > row["expires_at"]:
            conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
            conn.commit()
            return None
        return bytes(row["value"])

    def _sync_query(self, prefix: str, limit: int) -> list[tuple[str, bytes]]:
        conn = self._connect()
        now = time.time()
        # Prune expired rows lazily during every query scan
        conn.execute(
            "DELETE FROM kv_store WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now,),
        )
        rows = conn.execute(
            "SELECT key, value FROM kv_store "
            "WHERE key LIKE ? "
            "ORDER BY key ASC LIMIT ?",
            (prefix + "%", limit),
        ).fetchall()
        conn.commit()  # commit the lazy prune
        return [(row["key"], bytes(row["value"])) for row in rows]

    def _sync_delete(self, key: str) -> None:
        try:
            conn = self._connect()
            conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
            conn.commit()
        except sqlite3.Error as exc:
            raise StorageWriteError(f"SQLite delete failed for {key!r}: {exc}") from exc

    def _sync_ping(self) -> bool:
        try:
            conn = self._connect()
            conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False

    # ── Async public API ───────────────────────────────────────────────────

    async def _run(self, fn, *args):
        """Run a sync function in the default thread-pool executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fn, *args)

    async def put(
        self, key: str, value: bytes, ttl: int | None = None
    ) -> None:
        await self._run(self._sync_put, key, value, ttl)

    async def get(self, key: str) -> bytes | None:
        return await self._run(self._sync_get, key)

    async def query(
        self, prefix: str, limit: int = 100
    ) -> list[tuple[str, bytes]]:
        return await self._run(self._sync_query, prefix, limit)

    async def delete(self, key: str) -> None:
        await self._run(self._sync_delete, key)

    async def close(self) -> None:
        """Close the per-thread connection if open."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
        self._closed = True
        logger.debug(f"[SQLiteBackend] Closed: {self._db_path}")

    async def ping(self) -> bool:
        return await self._run(self._sync_ping)

    # ── Repr ──────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"SQLiteBackend(path={self._db_path!r}, closed={self._closed})"
