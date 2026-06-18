"""
core/memory/tiers/short_term.py

SHORT-TERM tier — SQLite-backed, default 48-hour TTL.
Supports ':memory:' for fully in-process test runs.

Canon: C34 (Memory Sovereignty)  Issue: #213
"""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore, MemoryTier

_DEFAULT_TTL_HOURS = MemoryTier.SHORT_TERM.default_ttl_hours  # 48.0


class ShortTermMemoryStore(MemoryStore):
    """
    SQLite-backed short-term store with TTL support.

    Pass ``db_path=':memory:'`` for fully in-process test usage.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS short_term (
                gaian_id  TEXT    NOT NULL DEFAULT '__global__',
                key       TEXT    NOT NULL,
                value     TEXT    NOT NULL,
                expires_at REAL,
                PRIMARY KEY (gaian_id, key)
            )
            """
        )
        self._conn.commit()

    # ------------------------------------------------------------------ #
    # MemoryStore ABC
    # ------------------------------------------------------------------ #

    async def write(
        self, key: str, value: Any,
        gaian_id: Optional[str] = None,
        ttl_hours: Optional[float] = None,
        **kwargs
    ) -> None:
        gid = gaian_id or "__global__"
        ttl = ttl_hours if ttl_hours is not None else _DEFAULT_TTL_HOURS
        expires_at = (time.time() + ttl * 3600) if ttl > 0 else None
        encoded = json.dumps(value)
        self._conn.execute(
            """
            INSERT INTO short_term (gaian_id, key, value, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(gaian_id, key) DO UPDATE SET
                value=excluded.value,
                expires_at=excluded.expires_at
            """,
            (gid, key, encoded, expires_at),
        )
        self._conn.commit()

    async def read(
        self, key: str, gaian_id: Optional[str] = None
    ) -> Optional[Any]:
        gid = gaian_id or "__global__"
        now = time.time()
        row = self._conn.execute(
            "SELECT value, expires_at FROM short_term WHERE gaian_id=? AND key=?",
            (gid, key),
        ).fetchone()
        if row is None:
            return None
        value_str, expires_at = row
        if expires_at is not None and now > expires_at:
            return None
        return json.loads(value_str)

    async def search(self, query: MemoryQuery) -> list[dict]:
        gid = query.gaian_id or "__global__"
        now = time.time()
        rows = self._conn.execute(
            """
            SELECT key, value, expires_at FROM short_term
            WHERE gaian_id=?
            AND (expires_at IS NULL OR expires_at > ?)
            """,
            (gid, now),
        ).fetchall()
        text = query.text.lower()
        results = []
        for k, v_str, expires_at in rows:
            v = json.loads(v_str)
            haystack = f"{k} {v}".lower()
            relevance = 0.8 if text in haystack else 0.2
            age_frac = max(0.0, 1.0 - (now - (expires_at or now + 1)) / (_DEFAULT_TTL_HOURS * 3600)) if expires_at else 0.5
            results.append({
                "key": k, "value": v,
                "_relevance": relevance, "_recency": age_frac,
                "_tier": "short_term",
            })
        return results

    async def evict_expired(self) -> int:
        now = time.time()
        cur = self._conn.execute(
            "DELETE FROM short_term WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (now,),
        )
        self._conn.commit()
        return cur.rowcount
