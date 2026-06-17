"""
core.memory.store
=================
Persistent, searchable memory store backed by SQLite + sqlite-vec.

Architecture
------------
Two tables live in a single SQLite file (WAL mode):

  memory_items      -- canonical row with all metadata (text, kind, tier ...)
  vec_memory_items  -- sqlite-vec ``vec0`` virtual table storing embeddings,
                       keyed by the same rowid as memory_items.

A ``remember()`` call inserts into both tables atomically.
A ``retrieve()`` call embeds the query, runs a k-NN search on the vec0
table, joins back to memory_items for metadata, and applies a hybrid
scoring formula (semantic similarity + importance + recency).

Dependencies
 ------------
    pip install sqlite-vec httpx

The sqlite-vec extension is loaded at connection time via:
    import sqlite_vec; conn.load_extension(sqlite_vec.find())
If sqlite_vec is not installed, the store falls back to a pure-text
(no vector search) mode that still persists memories but cannot do
semantic retrieval -- a warning is emitted at startup.

FIX (2026-06-17): MemoryStore.__init__ now accepts `dbpath` (no underscore)
as a keyword alias for `db_path` so that test fixtures calling
  MemoryStore(dbpath=..., embedder=FallbackEmbedder(dim=64))
work without TypeError.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .embedder import EmbeddingProvider, FallbackEmbedder
from .taxonomy import MemoryItem, MemoryKind, MemoryTier

log = logging.getLogger(__name__)

# Default path -- resolves to  <repo-root>/data/gaia_memory.db
_DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "gaia_memory.db"

# Capacity before the pruner is auto-triggered
_DEFAULT_CAPACITY = 100_000


@dataclass
class RetrievedMemory:
    """A memory item returned by ``MemoryStore.retrieve()``."""

    item:  MemoryItem
    score: float   # higher is more relevant (0.0 - 1.0 scale after normalisation)


class MemoryStore:
    """
    SQLite-backed semantic memory store.

    Parameters
    ----------
    db_path   : Path to the SQLite file.  Created on first use.
    dbpath    : Alias for db_path (for test-fixture compatibility).
    embedder  : EmbeddingProvider instance.  Defaults to FallbackEmbedder
                (hash-based, no semantic meaning -- swap in OllamaEmbedder
                or OpenAIEmbedder for real deployments).
    capacity  : Soft upper-bound on total rows per user before the pruner
                is triggered automatically.  Default 100 000.
    """

    def __init__(
        self,
        db_path:  Path | str               = _DEFAULT_DB_PATH,
        embedder: EmbeddingProvider | None  = None,
        capacity: int                       = _DEFAULT_CAPACITY,
        *,
        # Test-fixture alias: MemoryStore(dbpath=..., embedder=...)
        dbpath:   Path | str | None         = None,
        **kwargs,
    ) -> None:
        # dbpath keyword takes precedence over the positional db_path default
        effective_path = dbpath if dbpath is not None else db_path
        self._db_path  = Path(effective_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._embedder = embedder or FallbackEmbedder()
        self._capacity = capacity
        self._vec_ok   = False   # set True if sqlite-vec loads successfully
        self._conn     = self._open_connection()
        self._apply_migrations()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _open_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # WAL mode for concurrent readers + one writer
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        # Try to load sqlite-vec extension
        try:
            import sqlite_vec  # type: ignore
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
            self._vec_ok = True
            log.info("sqlite-vec loaded successfully -- semantic search enabled.")
        except Exception as exc:
            log.warning(
                "sqlite-vec not available (%s). "
                "Vector search disabled; text-only fallback active.",
                exc,
            )
        return conn

    # ------------------------------------------------------------------
    # Schema migrations
    # ------------------------------------------------------------------

    def _apply_migrations(self) -> None:
        c = self._conn
        # Main items table
        c.execute("""
            CREATE TABLE IF NOT EXISTS memory_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT    NOT NULL,
                kind        TEXT    NOT NULL DEFAULT 'message',
                tier        TEXT    NOT NULL DEFAULT 'short_term',
                role        TEXT    NOT NULL DEFAULT 'user',
                text        TEXT    NOT NULL,
                importance  REAL    NOT NULL DEFAULT 0.5,
                created_at  INTEGER NOT NULL,
                session_id  TEXT,
                topic_tag   TEXT,
                ttl_seconds INTEGER,
                metadata    TEXT,
                deleted     INTEGER NOT NULL DEFAULT 0
            )
        """)
        # Add metadata column to existing databases that predate this migration
        try:
            c.execute("ALTER TABLE memory_items ADD COLUMN metadata TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_mem_user_deleted "
            "ON memory_items (user_id, deleted)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_mem_kind "
            "ON memory_items (user_id, kind, deleted)"
        )
        # Vector table (requires sqlite-vec)
        if self._vec_ok:
            dim = self._embedder.dim
            c.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_memory_items
                USING vec0(
                    embedding FLOAT[{dim}]
                )
            """)
        c.commit()

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    async def remember(
        self,
        user_id:     str,
        text:        str,
        role:        str        = "user",
        kind:        MemoryKind = MemoryKind.MESSAGE,
        tier:        MemoryTier = MemoryTier.SHORT_TERM,
        importance:  float      = 0.5,
        session_id:  str | None = None,
        topic_tag:   str | None = None,
        ttl_seconds: int | None = None,
        metadata:    dict | None = None,
    ) -> int:
        """
        Persist a memory item and its embedding.

        Returns the newly-assigned row ``id``.
        """
        now = int(time.time())
        metadata_json = json.dumps(metadata) if metadata else None
        safe_role = role if role is not None else "user"
        cur = self._conn.execute(
            """
            INSERT INTO memory_items
                (user_id, kind, tier, role, text, importance,
                 created_at, session_id, topic_tag, ttl_seconds, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                kind.value if isinstance(kind, MemoryKind) else kind,
                tier.value if isinstance(tier, MemoryTier) else tier,
                safe_role,
                text, importance, now,
                session_id, topic_tag, ttl_seconds,
                metadata_json,
            ),
        )
        item_id = cur.lastrowid
        assert item_id is not None

        if self._vec_ok:
            try:
                vec = await self._embedder.embed(text)
                import struct
                blob = struct.pack(f"{len(vec)}f", *vec)
                self._conn.execute(
                    "INSERT INTO vec_memory_items (rowid, embedding) VALUES (?, ?)",
                    (item_id, blob),
                )
            except Exception as exc:
                log.warning("Failed to store embedding for item %d: %s", item_id, exc)

        self._conn.commit()
        return item_id

    def remember_sync(
        self,
        user_id:     str,
        text:        str,
        role:        str        = "user",
        kind:        MemoryKind = MemoryKind.MESSAGE,
        tier:        MemoryTier = MemoryTier.SHORT_TERM,
        importance:  float      = 0.5,
        session_id:  str | None = None,
        topic_tag:   str | None = None,
        ttl_seconds: int | None = None,
        metadata:    dict | None = None,
    ) -> int:
        """
        Synchronous wrapper around ``remember()``.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(
                        asyncio.run,
                        self.remember(
                            user_id=user_id, text=text, role=role,
                            kind=kind, tier=tier, importance=importance,
                            session_id=session_id, topic_tag=topic_tag,
                            ttl_seconds=ttl_seconds, metadata=metadata,
                        ),
                    )
                    return fut.result()
            else:
                return loop.run_until_complete(
                    self.remember(
                        user_id=user_id, text=text, role=role,
                        kind=kind, tier=tier, importance=importance,
                        session_id=session_id, topic_tag=topic_tag,
                        ttl_seconds=ttl_seconds, metadata=metadata,
                    )
                )
        except RuntimeError:
            return asyncio.run(
                self.remember(
                    user_id=user_id, text=text, role=role,
                    kind=kind, tier=tier, importance=importance,
                    session_id=session_id, topic_tag=topic_tag,
                    ttl_seconds=ttl_seconds, metadata=metadata,
                )
            )

    async def remember_item(self, item: MemoryItem) -> int:
        """Convenience wrapper -- persist a fully-constructed MemoryItem."""
        return await self.remember(
            user_id=item.user_id,
            text=item.text,
            role=item.role,
            kind=item.kind,
            tier=item.tier,
            importance=item.importance,
            session_id=item.session_id,
            topic_tag=item.topic_tag,
            ttl_seconds=item.ttl_seconds,
            metadata=item.metadata if isinstance(item.metadata, dict) else None,
        )

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    async def retrieve(
        self,
        user_id:          str,
        query:            str,
        top_k:            int                          = 20,
        kinds:            list[MemoryKind] | None      = None,
        tiers:            list[MemoryTier] | None      = None,
        topic_tag:        str | None                  = None,
        since_ts:         int | None                  = None,
        importance_floor: float                       = 0.0,
        importance_weight: float                      = 0.2,
        recency_weight:   float                       = 0.1,
    ) -> list[RetrievedMemory]:
        """
        Retrieve the top-k most relevant memories for *query*.
        """
        filters = ["m.user_id = ?", "m.deleted = 0"]
        params: list = [user_id]

        if kinds:
            placeholders = ",".join("?" * len(kinds))
            filters.append(f"m.kind IN ({placeholders})")
            params.extend(k.value for k in kinds)
        if tiers:
            placeholders = ",".join("?" * len(tiers))
            filters.append(f"m.tier IN ({placeholders})")
            params.extend(t.value for t in tiers)
        if topic_tag:
            filters.append("m.topic_tag = ?")
            params.append(topic_tag)
        if since_ts:
            filters.append("m.created_at >= ?")
            params.append(since_ts)
        if importance_floor > 0:
            filters.append("m.importance >= ?")
            params.append(importance_floor)

        where = " AND ".join(filters)

        if self._vec_ok:
            return await self._retrieve_vec(
                query, top_k, where, params,
                importance_weight, recency_weight,
            )
        else:
            return self._retrieve_fallback(top_k, where, params)

    def retrieve_sync(
        self,
        user_id:         str,
        query:           str,
        top_k:           int = 20,
        **kwargs,
    ) -> list[MemoryItem]:
        """Synchronous wrapper around ``retrieve()``."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(
                        asyncio.run,
                        self.retrieve(user_id=user_id, query=query, top_k=top_k, **kwargs),
                    )
                    results: list[RetrievedMemory] = fut.result()
            else:
                results = loop.run_until_complete(
                    self.retrieve(user_id=user_id, query=query, top_k=top_k, **kwargs)
                )
        except RuntimeError:
            results = asyncio.run(
                self.retrieve(user_id=user_id, query=query, top_k=top_k, **kwargs)
            )
        return [r.item for r in results]

    async def _retrieve_vec(
        self,
        query:             str,
        top_k:             int,
        where:             str,
        params:            list,
        importance_weight: float,
        recency_weight:    float,
    ) -> list[RetrievedMemory]:
        import struct
        vec = await self._embedder.embed(query)
        blob = struct.pack(f"{len(vec)}f", *vec)
        candidates = top_k * 3
        sql = f"""
            SELECT
                m.id, m.user_id, m.kind, m.tier, m.role, m.text,
                m.importance, m.created_at, m.session_id,
                m.topic_tag, m.ttl_seconds, m.deleted,
                v.distance
            FROM vec_memory_items v
            JOIN memory_items m ON m.id = v.rowid
            WHERE v.embedding MATCH ?
              AND k = ?
              AND {where}
            ORDER BY v.distance ASC
        """
        rows = self._conn.execute(sql, [blob, candidates, *params]).fetchall()
        now = int(time.time())
        results = []
        for row in rows:
            age_days    = max((now - row["created_at"]) / 86_400, 0.001)
            recency     = 1.0 / (1.0 + age_days / 30)
            similarity  = max(0.0, 1.0 - float(row["distance"]))
            score = (
                similarity
                + importance_weight * float(row["importance"])
                + recency_weight    * recency
            )
            item = MemoryItem(
                id          = row["id"],
                user_id     = row["user_id"],
                kind        = MemoryKind(row["kind"]),
                tier        = MemoryTier(row["tier"]),
                role        = row["role"],
                text        = row["text"],
                importance  = row["importance"],
                created_at  = row["created_at"],
                session_id  = row["session_id"],
                topic_tag   = row["topic_tag"],
                ttl_seconds = row["ttl_seconds"],
                deleted     = bool(row["deleted"]),
            )
            results.append(RetrievedMemory(item=item, score=score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def _retrieve_fallback(
        self,
        top_k:  int,
        where:  str,
        params: list,
    ) -> list[RetrievedMemory]:
        """No-vector fallback: rank by importance x recency."""
        sql = f"""
            SELECT *,
                   (importance * 0.7 + (created_at / CAST(strftime('%s','now') AS REAL)) * 0.3)
                   AS score
            FROM memory_items m
            WHERE {where}
            ORDER BY score DESC
            LIMIT ?
        """
        rows = self._conn.execute(sql, [*params, top_k]).fetchall()
        results = []
        for row in rows:
            item = MemoryItem(
                id          = row["id"],
                user_id     = row["user_id"],
                kind        = MemoryKind(row["kind"]),
                tier        = MemoryTier(row["tier"]),
                role        = row["role"],
                text        = row["text"],
                importance  = float(row["importance"]),
                created_at  = row["created_at"],
                session_id  = row["session_id"],
                topic_tag   = row["topic_tag"],
                ttl_seconds = row["ttl_seconds"],
                deleted     = bool(row["deleted"]),
            )
            results.append(RetrievedMemory(item=item, score=float(row["score"])))
        return results

    # ------------------------------------------------------------------
    # Soft-delete / hard-delete
    # ------------------------------------------------------------------

    def forget(self, item_id: int) -> None:
        """Soft-delete a single memory item."""
        self._conn.execute(
            "UPDATE memory_items SET deleted = 1 WHERE id = ?", (item_id,)
        )
        self._conn.commit()

    def forget_user(self, user_id: str) -> int:
        """Soft-delete ALL memories for a user.  Returns count deleted."""
        cur = self._conn.execute(
            "UPDATE memory_items SET deleted = 1 WHERE user_id = ? AND deleted = 0",
            (user_id,),
        )
        self._conn.commit()
        return cur.rowcount

    def hard_delete_soft_deleted(self) -> int:
        """Permanently erase rows flagged as deleted.  Returns count erased."""
        ids = [
            row[0]
            for row in self._conn.execute(
                "SELECT id FROM memory_items WHERE deleted = 1"
            ).fetchall()
        ]
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        self._conn.execute(
            f"DELETE FROM memory_items WHERE id IN ({placeholders})", ids
        )
        if self._vec_ok:
            self._conn.execute(
                f"DELETE FROM vec_memory_items WHERE rowid IN ({placeholders})", ids
            )
        self._conn.commit()
        return len(ids)

    # ------------------------------------------------------------------
    # Stats / counts
    # ------------------------------------------------------------------

    def count(self, user_id: str | None = None) -> int:
        """Return the number of non-deleted memory items."""
        if user_id:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM memory_items WHERE user_id = ? AND deleted = 0",
                (user_id,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM memory_items WHERE deleted = 0"
            ).fetchone()
        return int(row[0])

    def stats(self, user_id: str | None = None) -> dict:
        """Return a dict with row counts, broken down by kind."""
        if user_id:
            rows = self._conn.execute(
                """
                SELECT kind, COUNT(*) AS cnt
                FROM memory_items
                WHERE user_id = ? AND deleted = 0
                GROUP BY kind
                """,
                (user_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT kind, COUNT(*) AS cnt
                FROM memory_items
                WHERE deleted = 0
                GROUP BY kind
                """
            ).fetchall()
        total = self.count(user_id=user_id)
        return {
            "total": total,
            "by_kind": {row["kind"]: row["cnt"] for row in rows},
            "vec_enabled": self._vec_ok,
            "db_path": str(self._db_path),
        }

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()
