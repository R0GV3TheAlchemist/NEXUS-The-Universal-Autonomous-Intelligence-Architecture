"""
core/memory/tiers/short_term.py

ShortTermMemoryStore — SQLite-backed, 48 h default TTL.
Supports in-memory mode via db_path=':memory:'
Issue: #213
"""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Optional

from core.memory.hierarchy import MemoryQuery, MemoryStore

_DEFAULT_TTL_HOURS = 48.0


class ShortTermMemoryStore(MemoryStore):
    def __init__(self, db_path: str = ":memory:", default_ttl_hours: float = _DEFAULT_TTL_HOURS) -> None:
        self._default_ttl = default_ttl_hours * 3600
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS short_term (
                key        TEXT NOT NULL,
                gaian_id   TEXT,
                value      TEXT NOT NULL,
                expires_at REAL NOT NULL,
                PRIMARY KEY (key, gaian_id)
            )
            """
        )
        self._conn.commit()

    async def write(
        self, key: str, value: Any,
        gaian_id: Optional[str] = None,
        ttl_hours: Optional[float] = None,
        **kwargs,
    ) -> None:
        ttl = (ttl_hours * 3600) if ttl_hours is not None else self._default_ttl
        expires_at = time.time() + ttl
        self._conn.execute(
            "INSERT OR REPLACE INTO short_term (key, gaian_id, value, expires_at) VALUES (?, ?, ?, ?)",
            (key, gaian_id, json.dumps(value), expires_at),
        )
        self._conn.commit()

    async def read(self, key: str, gaian_id: Optional[str] = None) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT value, expires_at FROM short_term WHERE key = ? AND (gaian_id = ? OR gaian_id IS NULL)",
            (key, gaian_id),
        ).fetchone()
        if row is None:
            return None
        value, expires_at = row
        if time.time() > expires_at:
            return None
        return json.loads(value)

    async def search(self, query: MemoryQuery) -> list[dict]:
        now = time.time()
        text = query.text.lower()
        rows = self._conn.execute(
            "SELECT key, value FROM short_term WHERE expires_at > ?", (now,)
        ).fetchall()
        results = []
        for key, value in rows:
            if text in key.lower() or text in value.lower():
                results.append({"key": key, "value": json.loads(value), "_relevance": 0.5, "_recency": 0.7})
        return results

    async def evict_expired(self) -> int:
        cur = self._conn.execute("DELETE FROM short_term WHERE expires_at <= ?", (time.time(),))
        self._conn.commit()
        return cur.rowcount
