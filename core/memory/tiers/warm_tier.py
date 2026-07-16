"""
core/memory/tiers/warm_tier.py

WARM TIER — SQLite-backed mid-term memory storage.

Design:
- Stores entries in a local SQLite database (WAL mode, thread-safe).
- Each entry has a composite score = relevance * recency_decay.
- Supports full-text search via FTS5 virtual table.
- Entries are promoted to HotTier on hot read, demoted to ColdTier
  when score falls below a configurable threshold (handled by router).
- Max retention: configurable (default 7 days).
"""

from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class WarmEntry:
    key: str
    value: Any                       # serialised as JSON
    tags: List[str] = field(default_factory=list)
    relevance: float = 1.0           # caller-supplied importance [0, 1]
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def score(self, half_life: float = 86_400.0) -> float:
        """Recency-weighted relevance score."""
        age = time.time() - self.accessed_at
        decay = math.exp(-math.log(2) * age / half_life)
        return self.relevance * decay


# ---------------------------------------------------------------------------
# WarmTier
# ---------------------------------------------------------------------------

class WarmTier:
    """
    SQLite-backed warm memory store.

    Parameters
    ----------
    db_path : str | Path
        File path for the SQLite database.  Use ":memory:" for tests.
    max_age_seconds : float
        Entries not accessed within this window are eligible for cold demotion.
    half_life : float
        Half-life in seconds for the recency decay in score().
    """

    _DDL = """
    CREATE TABLE IF NOT EXISTS warm_entries (
        key           TEXT PRIMARY KEY,
        value_json    TEXT NOT NULL,
        tags_json     TEXT NOT NULL DEFAULT '[]',
        relevance     REAL NOT NULL DEFAULT 1.0,
        created_at    REAL NOT NULL,
        accessed_at   REAL NOT NULL,
        access_count  INTEGER NOT NULL DEFAULT 0,
        metadata_json TEXT NOT NULL DEFAULT '{}'
    );
    CREATE INDEX IF NOT EXISTS idx_accessed ON warm_entries(accessed_at);
    CREATE VIRTUAL TABLE IF NOT EXISTS warm_fts
        USING fts5(key, value_json, content='warm_entries', content_rowid='rowid');
    CREATE TRIGGER IF NOT EXISTS warm_ai AFTER INSERT ON warm_entries BEGIN
        INSERT INTO warm_fts(rowid, key, value_json)
        VALUES (new.rowid, new.key, new.value_json);
    END;
    CREATE TRIGGER IF NOT EXISTS warm_au AFTER UPDATE ON warm_entries BEGIN
        INSERT INTO warm_fts(warm_fts, rowid, key, value_json)
        VALUES ('delete', old.rowid, old.key, old.value_json);
        INSERT INTO warm_fts(rowid, key, value_json)
        VALUES (new.rowid, new.key, new.value_json);
    END;
    CREATE TRIGGER IF NOT EXISTS warm_ad AFTER DELETE ON warm_entries BEGIN
        INSERT INTO warm_fts(warm_fts, rowid, key, value_json)
        VALUES ('delete', old.rowid, old.key, old.value_json);
    END;
    """

    def __init__(
        self,
        db_path: str | Path = "gaia_warm.db",
        max_age_seconds: float = 7 * 86_400,
        half_life: float = 86_400.0,
    ) -> None:
        self.db_path = str(db_path)
        self.max_age_seconds = max_age_seconds
        self.half_life = half_life
        self._local = threading.local()
        self._init_db()

    # ------------------------------------------------------------------
    # Connection helper (thread-local)
    # ------------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_db(self) -> None:
        conn = self._conn()
        conn.executescript(self._DDL)
        conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def put(
        self,
        key: str,
        value: Any,
        *,
        tags: Optional[List[str]] = None,
        relevance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WarmEntry:
        now = time.time()
        entry = WarmEntry(
            key=key,
            value=value,
            tags=tags or [],
            relevance=max(0.0, min(1.0, relevance)),
            created_at=now,
            accessed_at=now,
            metadata=metadata or {},
        )
        conn = self._conn()
        conn.execute(
            """
            INSERT INTO warm_entries
                (key, value_json, tags_json, relevance, created_at,
                 accessed_at, access_count, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            ON CONFLICT(key) DO UPDATE SET
                value_json   = excluded.value_json,
                tags_json    = excluded.tags_json,
                relevance    = excluded.relevance,
                accessed_at  = excluded.accessed_at,
                metadata_json= excluded.metadata_json
            """,
            (
                key,
                json.dumps(value),
                json.dumps(entry.tags),
                entry.relevance,
                entry.created_at,
                entry.accessed_at,
                json.dumps(entry.metadata),
            ),
        )
        conn.commit()
        return entry

    def get(self, key: str) -> Optional[Any]:
        entry = self.get_entry(key)
        return entry.value if entry else None

    def get_entry(self, key: str) -> Optional[WarmEntry]:
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM warm_entries WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        entry = self._row_to_entry(row)
        # Update access stats
        now = time.time()
        conn.execute(
            "UPDATE warm_entries SET accessed_at = ?, access_count = access_count + 1 WHERE key = ?",
            (now, key),
        )
        conn.commit()
        entry.accessed_at = now
        entry.access_count += 1
        return entry

    def delete(self, key: str) -> bool:
        conn = self._conn()
        cur = conn.execute("DELETE FROM warm_entries WHERE key = ?", (key,))
        conn.commit()
        return cur.rowcount > 0

    def search(
        self,
        query: str,
        limit: int = 20,
        min_score: float = 0.0,
    ) -> List[WarmEntry]:
        """Full-text search over keys and values."""
        conn = self._conn()
        rows = conn.execute(
            """
            SELECT w.* FROM warm_entries w
            JOIN warm_fts f ON w.rowid = f.rowid
            WHERE warm_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        entries = [self._row_to_entry(r) for r in rows]
        return [
            e for e in entries
            if e.score(self.half_life) >= min_score
        ]

    def top_entries(
        self, n: int = 50, min_score: float = 0.0
    ) -> List[WarmEntry]:
        """Return top-n entries by composite score."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM warm_entries ORDER BY accessed_at DESC LIMIT ?",
            (n * 4,),  # over-fetch then re-sort by computed score
        ).fetchall()
        entries = [self._row_to_entry(r) for r in rows]
        scored = [
            (e.score(self.half_life), e) for e in entries
            if e.score(self.half_life) >= min_score
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:n]]

    def stale_entries(self) -> List[WarmEntry]:
        """Return entries not accessed within max_age_seconds."""
        cutoff = time.time() - self.max_age_seconds
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM warm_entries WHERE accessed_at < ?", (cutoff,)
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def purge_stale(self) -> int:
        """Delete stale entries.  Returns count removed."""
        stale = self.stale_entries()
        if not stale:
            return 0
        conn = self._conn()
        keys = [e.key for e in stale]
        conn.executemany(
            "DELETE FROM warm_entries WHERE key = ?", [(k,) for k in keys]
        )
        conn.commit()
        return len(keys)

    def clear(self) -> None:
        conn = self._conn()
        conn.execute("DELETE FROM warm_entries")
        conn.commit()

    def count(self) -> int:
        conn = self._conn()
        return conn.execute("SELECT COUNT(*) FROM warm_entries").fetchone()[0]

    def __len__(self) -> int:
        return self.count()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> WarmEntry:
        return WarmEntry(
            key=row["key"],
            value=json.loads(row["value_json"]),
            tags=json.loads(row["tags_json"]),
            relevance=row["relevance"],
            created_at=row["created_at"],
            accessed_at=row["accessed_at"],
            access_count=row["access_count"],
            metadata=json.loads(row["metadata_json"]),
        )
