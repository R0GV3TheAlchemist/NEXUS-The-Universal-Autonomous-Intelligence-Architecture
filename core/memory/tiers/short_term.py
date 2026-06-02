"""
core/memory/tiers/short_term.py
Short-Term Memory Tier — Sprint G-8

SQLite-backed store with TTL expiry. Default TTL: 48 hours.
Falls back to an in-memory dict when SQLite is unavailable
(e.g., in-process unit tests or sandboxed environments).

Table schema (created on first use):
  CREATE TABLE short_term_memory (
      gaian_id  TEXT,
      key       TEXT,
      value     TEXT,   -- JSON-serialised
      written_at REAL,  -- Unix epoch float
      expires_at REAL,  -- Unix epoch float; NULL = no expiry
      PRIMARY KEY (gaian_id, key)
  );

Canon Refs: C34, C01
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

from core.memory.hierarchy import MemoryQuery, MemoryTier

log = logging.getLogger(__name__)

_DEFAULT_TTL_HOURS = MemoryTier.SHORT_TERM.default_ttl_hours  # 48.0
_DB_PATH = Path("core/memory/audit/short_term.db")


class ShortTermMemoryStore:
    """SQLite-backed store with TTL expiry for short-term memory.

    In tests, pass ``db_path=':memory:'`` for a fully in-process store.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = str(db_path or _DB_PATH)
        self._conn: sqlite3.Connection | None = None
        self._fallback: dict[tuple[str | None, str], tuple[Any, float, float | None]] = {}
        self._use_fallback = False
        self._init_db()

    def _init_db(self) -> None:
        try:
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True) if self._db_path != ":memory:" else None
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS short_term_memory (
                    gaian_id   TEXT,
                    key        TEXT,
                    value      TEXT,
                    written_at REAL NOT NULL,
                    expires_at REAL,
                    PRIMARY KEY (gaian_id, key)
                )
                """
            )
            self._conn.commit()
        except Exception as exc:  # noqa: BLE001
            log.warning("ShortTermMemoryStore: SQLite unavailable (%r), using fallback dict.", exc)
            self._use_fallback = True

    async def write(
        self,
        key: str,
        value: Any,
        gaian_id: str | None = None,
        ttl_hours: float | None = None,
    ) -> None:
        now = time.time()
        ttl = (ttl_hours if ttl_hours is not None else _DEFAULT_TTL_HOURS) or 0
        expires_at = (now + ttl * 3600) if ttl > 0 else None
        gid = gaian_id or ""

        if self._use_fallback:
            self._fallback[(gid, key)] = (value, now, expires_at)
            return

        self._conn.execute(  # type: ignore[union-attr]
            """
            INSERT OR REPLACE INTO short_term_memory
                (gaian_id, key, value, written_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (gid, key, json.dumps(value), now, expires_at),
        )
        self._conn.commit()  # type: ignore[union-attr]

    async def read(self, key: str, gaian_id: str | None = None) -> Any | None:
        now = time.time()
        gid = gaian_id or ""

        if self._use_fallback:
            entry = self._fallback.get((gid, key))
            if entry is None:
                return None
            _, _, expires_at = entry
            if expires_at and now > expires_at:
                del self._fallback[(gid, key)]
                return None
            return entry[0]

        row = self._conn.execute(  # type: ignore[union-attr]
            "SELECT value, expires_at FROM short_term_memory WHERE gaian_id=? AND key=?",
            (gid, key),
        ).fetchone()
        if row is None:
            return None
        val_json, expires_at = row
        if expires_at and now > expires_at:
            self._conn.execute(  # type: ignore[union-attr]
                "DELETE FROM short_term_memory WHERE gaian_id=? AND key=?", (gid, key)
            )
            self._conn.commit()  # type: ignore[union-attr]
            return None
        return json.loads(val_json)

    async def search(self, query: MemoryQuery) -> list[dict]:
        now = time.time()
        gid = query.gaian_id or ""
        needle = query.query_text.lower()

        if self._use_fallback:
            rows = [
                (k, v, written_at, expires_at)
                for (g, k), (v, written_at, expires_at) in self._fallback.items()
                if (not query.gaian_id or g == gid)
                and (not expires_at or now <= expires_at)
            ]
        else:
            sql = "SELECT key, value, written_at FROM short_term_memory WHERE (expires_at IS NULL OR expires_at > ?)"
            params: list[Any] = [now]
            if query.gaian_id:
                sql += " AND gaian_id = ?"
                params.append(gid)
            rows_raw = self._conn.execute(sql, params).fetchall()  # type: ignore[union-attr]
            rows = [(r[0], json.loads(r[1]), r[2], None) for r in rows_raw]

        results = []
        for k, v, written_at, _ in rows:
            text = str(v).lower()
            relevance = 1.0 if needle and needle in text else 0.2
            age_hours = (now - written_at) / 3600
            recency = 1.0 / (1.0 + age_hours / 24.0)  # decays over days
            results.append({
                "key":        k,
                "value":      v,
                "_relevance": relevance,
                "_recency":   recency,
            })
        return results

    async def evict_expired(self) -> int:
        now = time.time()
        if self._use_fallback:
            expired = [(g, k) for (g, k), (_, _, exp) in self._fallback.items() if exp and now > exp]
            for key in expired:
                del self._fallback[key]
            return len(expired)

        cur = self._conn.execute(  # type: ignore[union-attr]
            "DELETE FROM short_term_memory WHERE expires_at IS NOT NULL AND expires_at <= ?", (now,)
        )
        self._conn.commit()  # type: ignore[union-attr]
        return cur.rowcount
