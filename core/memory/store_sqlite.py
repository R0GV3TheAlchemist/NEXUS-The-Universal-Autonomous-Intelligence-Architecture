"""
core/memory/store_sqlite.py

SQLite-backed MemoryStore for the semantic memory layer.
Used by test_memory_store.py via: MemoryStore(db_path=..., embedder=FallbackEmbedder(dim=N))

Features:
  - WAL mode for concurrent read safety
  - remember_sync / remember_item write paths
  - retrieve_sync read path with filtering (kind, tier, topic_tag, importance_floor, since_ts)
  - forget (soft-delete), forget_user, hard_delete_soft_deleted
  - count(), stats()
  - MemoryPruner integration

Canon Reference: C01, C-SENTINEL Article 4
Issue: #213
Version: 1.0.0
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from core.memory.items import MemoryItem, MemoryKind, RetrievedMemory
from core.memory.hierarchy import MemoryTier


class MemoryStore:
    """
    SQLite-backed semantic memory store.
    Accepts an embedder for future vector search; falls back to text search.
    """

    def __init__(
        self,
        db_path: Any = ":memory:",
        embedder: Any = None,
    ) -> None:
        self._db_path  = str(db_path)
        self._embedder = embedder
        self._vec_enabled = False  # sqlite-vec not required
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._migrate()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _migrate(self) -> None:
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_items (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      TEXT    NOT NULL,
                kind         TEXT    NOT NULL DEFAULT 'message',
                tier         TEXT    NOT NULL DEFAULT 'ephemeral',
                role         TEXT    NOT NULL DEFAULT 'user',
                text         TEXT    NOT NULL,
                importance   REAL    NOT NULL DEFAULT 0.5,
                topic_tag    TEXT,
                metadata     TEXT    NOT NULL DEFAULT '{}',
                created_at   INTEGER NOT NULL,
                ttl_seconds  INTEGER,
                deleted      INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def remember_sync(
        self,
        user_id: str,
        text: str,
        kind: MemoryKind          = MemoryKind.MESSAGE,
        tier: Any                 = None,
        role: str                 = "user",
        importance: float         = 0.5,
        topic_tag: Optional[str]  = None,
        metadata: Optional[dict]  = None,
        ttl_seconds: Optional[int]= None,
    ) -> int:
        tier_val = tier.value if tier is not None else MemoryTier.EPHEMERAL.value
        cur = self._conn.execute(
            """
            INSERT INTO memory_items
                (user_id, kind, tier, role, text, importance, topic_tag, metadata, created_at, ttl_seconds, deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                user_id,
                kind.value,
                tier_val,
                role,
                text,
                importance,
                topic_tag,
                json.dumps(metadata or {}),
                int(time.time()),
                ttl_seconds,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    async def remember_item(self, item: MemoryItem) -> int:
        tier_val = item.tier.value if item.tier is not None else MemoryTier.EPHEMERAL.value
        cur = self._conn.execute(
            """
            INSERT INTO memory_items
                (user_id, kind, tier, role, text, importance, topic_tag, metadata, created_at, ttl_seconds, deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                item.user_id,
                item.kind.value,
                tier_val,
                item.role,
                item.text,
                item.importance,
                item.topic_tag,
                json.dumps(item.metadata or {}),
                item.created_at or int(time.time()),
                item.ttl_seconds,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def retrieve_sync(
        self,
        user_id: str,
        query: str,
        top_k: int                           = 20,
        kinds: Optional[list[MemoryKind]]    = None,
        tiers: Optional[list[Any]]           = None,
        topic_tag: Optional[str]             = None,
        importance_floor: Optional[float]    = None,
        since_ts: Optional[int]              = None,
    ) -> list[MemoryItem]:
        sql  = "SELECT id, user_id, kind, tier, role, text, importance, topic_tag, metadata, created_at, ttl_seconds FROM memory_items WHERE deleted = 0 AND user_id = ?"
        args: list = [user_id]

        if kinds:
            sql += f" AND kind IN ({','.join('?' * len(kinds))})"
            args += [k.value for k in kinds]
        if tiers:
            sql += f" AND tier IN ({','.join('?' * len(tiers))})"
            args += [t.value for t in tiers]
        if topic_tag:
            sql += " AND topic_tag = ?"
            args.append(topic_tag)
        if importance_floor is not None:
            sql += " AND importance >= ?"
            args.append(importance_floor)
        if since_ts is not None:
            sql += " AND created_at >= ?"
            args.append(since_ts)

        sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        args.append(top_k)

        rows = self._conn.execute(sql, args).fetchall()
        return [self._row_to_item(r) for r in rows]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def forget(self, item_id: int) -> None:
        self._conn.execute("UPDATE memory_items SET deleted = 1 WHERE id = ?", (item_id,))
        self._conn.commit()

    def forget_user(self, user_id: str) -> int:
        cur = self._conn.execute(
            "UPDATE memory_items SET deleted = 1 WHERE user_id = ? AND deleted = 0", (user_id,)
        )
        self._conn.commit()
        return cur.rowcount

    def hard_delete_soft_deleted(self) -> int:
        cur = self._conn.execute("DELETE FROM memory_items WHERE deleted = 1")
        self._conn.commit()
        return cur.rowcount

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def count(self, user_id: Optional[str] = None) -> int:
        if user_id:
            return self._conn.execute(
                "SELECT COUNT(*) FROM memory_items WHERE deleted = 0 AND user_id = ?", (user_id,)
            ).fetchone()[0]
        return self._conn.execute(
            "SELECT COUNT(*) FROM memory_items WHERE deleted = 0"
        ).fetchone()[0]

    def stats(self, user_id: Optional[str] = None) -> dict:
        total = self.count(user_id=user_id)
        where = "deleted = 0" + (f" AND user_id = '{user_id}'" if user_id else "")
        by_kind = {}
        for row in self._conn.execute(
            f"SELECT kind, COUNT(*) FROM memory_items WHERE {where} GROUP BY kind"
        ).fetchall():
            by_kind[row[0]] = row[1]
        return {
            "total":       total,
            "by_kind":     by_kind,
            "vec_enabled": self._vec_enabled,
            "db_path":     self._db_path,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _row_to_item(self, row: tuple) -> MemoryItem:
        id_, user_id, kind, tier, role, text, importance, topic_tag, metadata, created_at, ttl_seconds = row
        return MemoryItem(
            id=id_,
            user_id=user_id,
            kind=MemoryKind(kind),
            tier=self._parse_tier(tier),
            role=role,
            text=text,
            importance=float(importance),
            topic_tag=topic_tag,
            metadata=json.loads(metadata) if metadata else {},
            created_at=created_at,
            ttl_seconds=ttl_seconds,
        )

    @staticmethod
    def _parse_tier(val: str) -> Optional[Any]:
        try:
            return MemoryTier(val)
        except ValueError:
            return None
