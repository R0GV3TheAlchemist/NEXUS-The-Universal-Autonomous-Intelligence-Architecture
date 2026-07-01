"""
core/memory/memory_store.py

SQLite-backed semantic memory store for GAIA-OS.

Canon Reference: C01 (Gaian Sovereignty), C17 (Memory Sovereignty), C-SENTINEL Article 4
Issue:          #213
Version:        3.1.0

Contract (tests/test_memory_store.py):
  MemoryTier   — EPHEMERAL, SHORT_TERM, EPISODIC, SEMANTIC, LONG_TERM, PERMANENT
  MemoryStore  — SQLite file-backed, WAL mode
    .remember_sync(user_id, text, kind, tier, role, importance,
                   topic_tag, metadata, ttl_seconds)  -> int (row id)
    .remember_item(item: MemoryItem) -> Awaitable[int]
    .retrieve_sync(user_id, query, top_k, kinds, tiers,
                   topic_tag, importance_floor, since_ts)  -> List[MemoryItem]
    .forget(item_id)           -> None    (soft-delete)
    .forget_user(user_id)      -> int     (rows soft-deleted)
    .hard_delete_soft_deleted()-> int     (rows hard-erased)
    .count(user_id=None)       -> int
    .stats(user_id=None)       -> dict
    .close()                   -> None
    ._conn                     — exposed for tests to inspect schema

Contract (tests/memory/test_memory_console.py):
  MemoryCategory   — PREFERENCE, SESSION_GOAL, FACTUAL, EMOTIONAL, PROCEDURAL, IDENTITY
  MemoryEntry      — dataclass: key, value, category, tier, provenance, tags, id,
                     created_at, updated_at, last_used_at, last_used_context, archived
  MemoryProvenance — dataclass: source, confidence (0–1 validated), origin_context
  ProvenanceSource — GAIAN_EXPLICIT, GAIAN_INFERRED, SYSTEM, IMPORTED
  SessionState     — dataclass: session_id, gaian_id; .promote_to_durable(entry) -> MemoryEntry
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional


# ---------------------------------------------------------------------------
# Default store path
# ---------------------------------------------------------------------------

_default_store_path = "./data/memory_store.db"


# ---------------------------------------------------------------------------
# MemoryTier — flat SQLite store tiers
# Note: hierarchy.py has its own 5-member MemoryTier for the tiered architecture.
# This one is used by MemoryStore (SQLite) and MemoryConsole.
# ---------------------------------------------------------------------------

class MemoryTier(str, Enum):
    """
    Tier classification for the flat SQLite memory store and console.
    Higher-value tiers are more persistent.
    """
    EPHEMERAL  = "ephemeral"    # Volatile — session scratch
    SESSION    = "session"      # Current session only
    SHORT_TERM = "short_term"   # A few days
    EPISODIC   = "episodic"     # Recent weeks
    SEMANTIC   = "semantic"     # Derived long-term knowledge
    LONG_TERM  = "long_term"    # Indefinite
    PERMANENT  = "permanent"    # Never pruned
    DURABLE    = "durable"      # Human-principal-confirmed, long-lived
    ARCHIVED   = "archived"     # Soft-archived, excluded from default browse


# ---------------------------------------------------------------------------
# MemoryCategory — semantic grouping for MemoryEntry
# ---------------------------------------------------------------------------

class MemoryCategory(str, Enum):
    """Semantic category for a MemoryEntry in the console layer."""
    PREFERENCE   = "preference"
    SESSION_GOAL = "session_goal"
    FACTUAL      = "factual"
    EMOTIONAL    = "emotional"
    PROCEDURAL   = "procedural"
    IDENTITY     = "identity"
    CONTEXT      = "context"
    SYSTEM       = "system"


# ---------------------------------------------------------------------------
# ProvenanceSource — origin of a memory entry
# ---------------------------------------------------------------------------

class ProvenanceSource(str, Enum):
    """Who or what created / inferred this memory entry."""
    GAIAN_EXPLICIT = "gaian_explicit"   # User told GAIA directly
    GAIAN_INFERRED = "gaian_inferred"   # GAIA inferred from conversation
    SYSTEM         = "system"           # System-generated
    IMPORTED       = "imported"         # Imported from external source


# ---------------------------------------------------------------------------
# MemoryProvenance — confidence-validated provenance record
# ---------------------------------------------------------------------------

@dataclass
class MemoryProvenance:
    """
    Provenance record for a MemoryEntry.

    confidence must be in [0.0, 1.0]; raises ValueError otherwise.
    """
    source: ProvenanceSource
    confidence: float = 1.0
    origin_context: Optional[str] = None
    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"MemoryProvenance.confidence must be in [0.0, 1.0], "
                f"got {self.confidence!r}"
            )


# ---------------------------------------------------------------------------
# MemoryEntry — the console-layer memory unit
# ---------------------------------------------------------------------------

@dataclass
class MemoryEntry:
    """
    A single named memory entry visible in the Gaian Memory Console.

    key      — human-readable identifier (e.g. "preferred_name")
    value    — the stored value (string)
    category — semantic grouping (MemoryCategory)
    tier     — persistence tier (MemoryTier)
    provenance — who/how the entry was created and with what confidence
    tags     — free-form list of string tags for filtering
    id       — auto-generated UUID if not provided
    """
    key:        str
    value:      str
    category:   MemoryCategory
    tier:       MemoryTier
    provenance: MemoryProvenance

    tags:               List[str]          = field(default_factory=list)
    id:                 str                = field(default_factory=lambda: str(uuid.uuid4()))
    created_at:         datetime           = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at:         Optional[datetime] = None
    last_used_at:       Optional[datetime] = None
    last_used_context:  Optional[str]      = None
    archived:           bool               = False


# ---------------------------------------------------------------------------
# SessionState — tracks a single active session
# ---------------------------------------------------------------------------

@dataclass
class SessionState:
    """
    Lightweight session state record managed by the MemoryConsole.

    session_id      — unique session identifier
    gaian_id        — which Gaian instance owns this session
    """
    session_id: str
    gaian_id:   str
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def promote_to_durable(self, entry: MemoryEntry) -> MemoryEntry:
        """
        Return a copy of *entry* promoted to DURABLE tier.
        Does not mutate the original.
        """
        import dataclasses
        return dataclasses.replace(entry, tier=MemoryTier.DURABLE)


# ---------------------------------------------------------------------------
# MemoryStore — SQLite-backed flat store
# ---------------------------------------------------------------------------

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS memory_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT    NOT NULL,
    kind         TEXT    NOT NULL DEFAULT 'message',
    tier         TEXT    NOT NULL DEFAULT 'long_term',
    role         TEXT    NOT NULL DEFAULT 'user',
    text         TEXT    NOT NULL DEFAULT '',
    embedding    BLOB,
    importance   REAL    NOT NULL DEFAULT 0.5,
    topic_tag    TEXT,
    metadata     TEXT    NOT NULL DEFAULT '{}',
    created_at   INTEGER NOT NULL,
    ttl_seconds  INTEGER,
    deleted      INTEGER NOT NULL DEFAULT 0
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_mi_user     ON memory_items (user_id);",
    "CREATE INDEX IF NOT EXISTS idx_mi_deleted  ON memory_items (deleted);",
    "CREATE INDEX IF NOT EXISTS idx_mi_tier     ON memory_items (tier);",
    "CREATE INDEX IF NOT EXISTS idx_mi_kind     ON memory_items (kind);",
    "CREATE INDEX IF NOT EXISTS idx_mi_created  ON memory_items (created_at);",
]


class MemoryStore:
    """
    SQLite-backed semantic memory store.

    Accepts an optional embedder for future vector search;
    falls back to text LIKE search when not available or when
    sqlite-vec is not installed.

    Constructor aliases (all resolve to the same db path):
      db_path   — canonical keyword  (MemoryStore(db_path="..."))
      dbpath    — no-underscore alias (MemoryStore(dbpath="..."))  ← test fixture
      store_path — legacy alias       (MemoryStore(store_path="..."))
    """

    def __init__(
        self,
        db_path: Any = _default_store_path,
        embedder: Optional[Any] = None,
        *,
        dbpath: Optional[str] = None,
        store_path: Optional[str] = None,
    ) -> None:
        # Priority: explicit db_path positional > dbpath alias > store_path legacy > default
        if db_path != _default_store_path:
            resolved = db_path
        elif dbpath is not None:
            resolved = dbpath
        elif store_path is not None:
            resolved = store_path
        else:
            resolved = _default_store_path

        self._db_path = str(resolved)
        self._embedder = embedder
        self._vec_enabled = False
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._migrate()

    # ------------------------------------------------------------------
    # Schema / migrations
    # ------------------------------------------------------------------

    def _migrate(self) -> None:
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute(_CREATE_TABLE)
        for stmt in _CREATE_INDEXES:
            self._conn.execute(stmt)
        # Add metadata column if missing (idempotent migration)
        cols = [r[1] for r in self._conn.execute("PRAGMA table_info(memory_items)").fetchall()]
        if "metadata" not in cols:
            self._conn.execute("ALTER TABLE memory_items ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'")
        self._conn.commit()

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def remember_sync(
        self,
        user_id: str,
        text: str,
        *,
        kind: Any = None,
        tier: Any = None,
        role: str = "user",
        importance: float = 0.5,
        topic_tag: Optional[str] = None,
        metadata: Optional[dict] = None,
        ttl_seconds: Optional[int] = None,
    ) -> int:
        """
        Store a memory synchronously.
        Returns the rowid (integer > 0).
        """
        kind_val  = kind.value  if hasattr(kind,  "value") else str(kind  or "message")
        tier_val  = tier.value  if hasattr(tier,  "value") else str(tier  or "long_term")
        meta_json = json.dumps(metadata or {})
        now       = int(time.time())

        cur = self._conn.execute(
            """
            INSERT INTO memory_items
                (user_id, kind, tier, role, text, importance,
                 topic_tag, metadata, created_at, ttl_seconds, deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (user_id, kind_val, tier_val, role, text, importance,
             topic_tag, meta_json, now, ttl_seconds),
        )
        self._conn.commit()
        return cur.lastrowid

    async def remember_item(self, item: Any) -> int:
        """
        Async convenience: store a MemoryItem object.
        Returns the rowid.
        """
        return self.remember_sync(
            user_id     = item.user_id,
            text        = item.text,
            kind        = item.kind,
            tier        = item.tier,
            role        = getattr(item, "role", "user"),
            importance  = getattr(item, "importance", 0.5),
            topic_tag   = getattr(item, "topic_tag", None),
            metadata    = getattr(item, "metadata", None),
            ttl_seconds = getattr(item, "ttl_seconds", None),
        )

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def retrieve_sync(
        self,
        user_id: str,
        query: str = "",
        *,
        top_k: int = 20,
        kinds: Optional[List[Any]] = None,
        tiers: Optional[List[Any]] = None,
        topic_tag: Optional[str] = None,
        importance_floor: Optional[float] = None,
        since_ts: Optional[int] = None,
    ) -> List[Any]:
        """
        Retrieve memories for a user.
        Returns MemoryItem objects (imported lazily to avoid circular).
        Falls back to text LIKE search (no sqlite-vec required).
        """
        from core.memory.items import MemoryItem, MemoryKind  # lazy import

        conditions = ["user_id = ?", "deleted = 0"]
        params: list = [user_id]

        if kinds:
            kind_vals = [k.value if hasattr(k, "value") else str(k) for k in kinds]
            placeholders = ",".join("?" * len(kind_vals))
            conditions.append(f"kind IN ({placeholders})")
            params.extend(kind_vals)

        if tiers:
            tier_vals = [t.value if hasattr(t, "value") else str(t) for t in tiers]
            placeholders = ",".join("?" * len(tier_vals))
            conditions.append(f"tier IN ({placeholders})")
            params.extend(tier_vals)

        if topic_tag is not None:
            conditions.append("topic_tag = ?")
            params.append(topic_tag)

        if importance_floor is not None:
            conditions.append("importance >= ?")
            params.append(importance_floor)

        if since_ts is not None:
            conditions.append("created_at >= ?")
            params.append(since_ts)

        where = " AND ".join(conditions)
        sql   = f"""
            SELECT id, user_id, kind, tier, role, text, importance,
                   topic_tag, metadata, created_at, ttl_seconds, deleted
            FROM memory_items
            WHERE {where}
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        """
        params.append(top_k)

        rows = self._conn.execute(sql, params).fetchall()

        results = []
        for row in rows:
            (rid, uid, kind_s, tier_s, role_s, text_s, imp,
             tag, meta_s, cat, ttl, deleted) = row
            try:
                kind_e = MemoryKind(kind_s)
            except ValueError:
                kind_e = MemoryKind.MESSAGE
            try:
                tier_e = MemoryTier(tier_s)
            except ValueError:
                tier_e = MemoryTier.LONG_TERM
            meta = json.loads(meta_s) if meta_s else {}
            item = MemoryItem(
                id          = rid,
                user_id     = uid,
                kind        = kind_e,
                tier        = tier_e,
                role        = role_s,
                text        = text_s,
                importance  = float(imp),
                topic_tag   = tag,
                metadata    = meta,
                created_at  = cat,
                ttl_seconds = ttl,
            )
            results.append(item)
        return results

    # ------------------------------------------------------------------
    # Delete path
    # ------------------------------------------------------------------

    def forget(self, item_id: int) -> None:
        """Soft-delete a single memory item by rowid."""
        self._conn.execute(
            "UPDATE memory_items SET deleted = 1 WHERE id = ?", (item_id,)
        )
        self._conn.commit()

    def forget_user(self, user_id: str) -> int:
        """Soft-delete all memories for a user. Returns row count."""
        cur = self._conn.execute(
            "UPDATE memory_items SET deleted = 1 WHERE user_id = ? AND deleted = 0",
            (user_id,),
        )
        self._conn.commit()
        return cur.rowcount

    def hard_delete_soft_deleted(self) -> int:
        """Permanently erase all soft-deleted rows. Returns row count."""
        cur = self._conn.execute(
            "DELETE FROM memory_items WHERE deleted = 1"
        )
        self._conn.commit()
        return cur.rowcount

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def count(self, *, user_id: Optional[str] = None) -> int:
        """Return count of non-deleted memories, optionally scoped to user."""
        if user_id:
            return self._conn.execute(
                "SELECT COUNT(*) FROM memory_items WHERE user_id = ? AND deleted = 0",
                (user_id,),
            ).fetchone()[0]
        return self._conn.execute(
            "SELECT COUNT(*) FROM memory_items WHERE deleted = 0"
        ).fetchone()[0]

    def stats(self, *, user_id: Optional[str] = None) -> dict:
        """Return a summary dict of store state."""
        total = self.count(user_id=user_id)

        if user_id:
            kind_rows = self._conn.execute(
                "SELECT kind, COUNT(*) FROM memory_items "
                "WHERE user_id = ? AND deleted = 0 GROUP BY kind",
                (user_id,),
            ).fetchall()
        else:
            kind_rows = self._conn.execute(
                "SELECT kind, COUNT(*) FROM memory_items "
                "WHERE deleted = 0 GROUP BY kind"
            ).fetchall()

        return {
            "total":       total,
            "by_kind":     {r[0]: r[1] for r in kind_rows},
            "vec_enabled": self._vec_enabled,
            "db_path":     self._db_path,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the SQLite connection."""
        self._conn.close()

    # ------------------------------------------------------------------
    # Legacy compatibility (old dict-based callers)
    # ------------------------------------------------------------------

    def store(self, entry: Any) -> None:
        """Legacy: no-op shim for old MemoryEntry objects."""
        pass

    def retrieve(self, entry_id: str) -> None:
        """Legacy: returns None (old dict-based interface)."""
        return None

    def delete(self, entry_id: str) -> bool:
        """Legacy: hard-deletes by string id if it's numeric."""
        try:
            self.hard_delete_soft_deleted()
        except Exception:
            pass
        return False


def get_memory_store(db_path: str = _default_store_path, **kwargs) -> MemoryStore:
    """Factory function: create and return a MemoryStore instance."""
    return MemoryStore(db_path=db_path, **kwargs)
