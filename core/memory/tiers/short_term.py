"""
core/memory/tiers/short_term.py
ShortTermMemoryStore — async SQLite-backed, TTL-aware (24–72 hr default).

Uses aiosqlite when available; falls back to a thread-safe synchronous
sqlite3 wrapper so the store still works in pure-stdlib environments
(e.g., the test runner with `db_path=':memory:'`).

Canon refs: C34, C01
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from typing import Any


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS short_term (
    gaian_id  TEXT,
    key       TEXT,
    value     TEXT NOT NULL,
    expires_at REAL,           -- Unix timestamp; NULL = no expiry
    created_at REAL NOT NULL,
    PRIMARY KEY (gaian_id, key)
);
"""


class ShortTermMemoryStore:
    """SQLite-backed short-term memory with per-record TTL expiry."""

    DEFAULT_TTL_HOURS = 48.0

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()

    # ── Internal ──────────────────────────────────────────────────── #

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute(_CREATE_TABLE)
            self._conn.commit()
        return self._conn

    def _now(self) -> float:
        return time.time()

    # ── MemoryStore Protocol ───────────────────────────────────────── #

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,
    ) -> None:
        async with self._lock:
            ttl = ttl_hours if ttl_hours is not None else self.DEFAULT_TTL_HOURS
            now = self._now()
            expires = now + ttl * 3600 if ttl > 0 else None
            serialised = json.dumps(value)
            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO short_term (gaian_id, key, value, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(gaian_id, key) DO UPDATE SET
                    value=excluded.value,
                    expires_at=excluded.expires_at,
                    created_at=excluded.created_at
                """,
                (gaian_id, key, serialised, expires, now),
            )
            conn.commit()

    async def read(
        self,
        key: str,
        gaian_id: str | None = None,
    ) -> Any | None:
        async with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT value, expires_at FROM short_term WHERE gaian_id=? AND key=?",
                (gaian_id, key),
            ).fetchone()
            if row is None:
                return None
            if row["expires_at"] is not None and row["expires_at"] < self._now():
                return None
            return json.loads(row["value"])

    async def search(
        self,
        query: Any,
    ) -> list[dict]:
        async with self._lock:
            gid  = getattr(query, "gaian_id", None)
            text = getattr(query, "query_text", "").lower()
            now  = self._now()
            conn = self._get_conn()
            if gid is not None:
                rows = conn.execute(
                    "SELECT * FROM short_term WHERE gaian_id=? AND (expires_at IS NULL OR expires_at > ?)",
                    (gid, now),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM short_term WHERE (expires_at IS NULL OR expires_at > ?)",
                    (now,),
                ).fetchall()
            results = []
            for row in rows:
                haystack = (row["key"] + " " + row["value"]).lower()
                rel = 0.8 if text and text in haystack else 0.3
                age_score = max(0.0, 1.0 - (now - row["created_at"]) / (48 * 3600))
                results.append({
                    "key": row["key"],
                    "value": json.loads(row["value"]),
                    "_relevance": rel,
                    "_recency":   age_score,
                })
            return results

    async def evict_expired(self) -> int:
        async with self._lock:
            conn = self._get_conn()
            cur = conn.execute(
                "DELETE FROM short_term WHERE expires_at IS NOT NULL AND expires_at < ?",
                (self._now(),),
            )
            conn.commit()
            return cur.rowcount
