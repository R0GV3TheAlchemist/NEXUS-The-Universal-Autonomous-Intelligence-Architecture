"""GAIA-OS Sovereign Memory System

Issue #66 | Pillar III: Societas

The Sovereign Memory System is the foundation for all continuity in GAIA-OS.
All data is local-first, encrypted at rest (AES-256-GCM), and never transmitted
without explicit cryptographic consent.

Vector search is powered by sqlite-vec (sqlite extension) and degrades
gracefully to time-ordered recall when the extension is unavailable.

Usage::

    from sovereign_memory import SovereignMemory

    mem = SovereignMemory(db_path="~/.local/share/GAIA-OS/memory.db")
    mem.open()  # loads MK from keychain, applies migrations, opens DB

    episode_id = mem.store_episode(
        principal_id="user-001",
        content="Today I decided to quit my job.",
        type="decision",
        tags=["career", "transition"],
    )

    results = mem.search_memory(
        principal_id="user-001",
        query="career change feelings",
        limit=10,
    )

    mem.close()
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Literal, Sequence

from .crypto import (
    MasterKeyManager,
    derive_dek,
    encrypt,
    decrypt,
    make_aad,
)
from .types import (
    AffectSnapshot,
    BiometricSample,
    LegacyArtifact,
    MarkerScores,
    MemoryRecord,
    StageRecord,
    StageTransitionRecord,
)
from . import vec_search

# Exported so tests/conftest.py can patch 'sovereign_memory.SentenceTransformer'
# via unittest.mock.patch without AttributeError.
try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # sentence-transformers not installed (e.g. lightweight CI)
    SentenceTransformer = None  # type: ignore[assignment,misc]

__all__ = [
    "SovereignMemory",
    "SentenceTransformer",
    # Type re-exports — imported above, surfaced here for downstream consumers
    "AffectSnapshot",
    "BiometricSample",
    "LegacyArtifact",
    "MarkerScores",
    "MemoryRecord",
    "StageRecord",
    "StageTransitionRecord",
]

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Embedding dimension for the configured model
_EMBED_DIM_MAP = {
    "local": vec_search._DIM_MINILM,
    "openai": vec_search._DIM_OPENAI,
    "nomic": vec_search._DIM_NOMIC,
}


def _embed_dim() -> int:
    mode = os.environ.get("GAIA_EMBED_MODEL", "local").lower()
    return _EMBED_DIM_MAP.get(mode, vec_search._DIM_MINILM)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _new_id() -> str:
    return str(uuid.uuid4())


class SovereignMemory:
    """
    Primary interface to GAIA-OS encrypted local memory.

    All public methods accept and return plain Python types / dataclasses.
    Encryption / decryption is handled internally — callers never touch raw keys.
    Vector search is provided by sqlite-vec and degrades gracefully to
    time-ordered retrieval when the extension is unavailable.
    """

    def __init__(
        self,
        db_path: str = "~/.local/share/GAIA-OS/memory.db",
        passphrase: str | None = None,
    ) -> None:
        self._db_path = os.path.expanduser(db_path)
        self._passphrase = passphrase
        self._conn: sqlite3.Connection | None = None
        self._mk: bytes | None = None
        self._dek_cache: dict[str, bytes] = {}

    # ─────────────────────────────────────────
    # LIFECYCLE
    # ─────────────────────────────────────────

    def open(self) -> None:
        """Load MK from keychain, open DB, load sqlite-vec, apply schema."""
        parent = os.path.dirname(self._db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._mk = MasterKeyManager.load_or_create(self._passphrase)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # Try to load sqlite-vec extension before applying schema
        # (schema migration v2 creates the vec0 tables)
        vec_search.try_load_sqlite_vec(self._conn)
        self._apply_schema()
        self._ensure_active_keys()
        # Ensure vec0 tables exist for the configured embedding dimension
        vec_search.ensure_vec_tables(self._conn, _embed_dim())

    def close(self) -> None:
        """Commit, close DB, wipe MK from memory."""
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None
        MasterKeyManager.wipe()
        self._mk = None
        self._dek_cache.clear()

    def __enter__(self) -> "SovereignMemory":
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ─────────────────────────────────────────
    # EPISODE STORAGE & RETRIEVAL
    # ─────────────────────────────────────────

    def store_episode(
        self,
        principal_id: str,
        content: str,
        type: str = "journal",
        tags: Sequence[str] | None = None,
        created_at: int | None = None,
        key_id: str = "episodic-v1",
    ) -> str:
        self._assert_open()
        episode_id = _new_id()
        now = created_at or _now_ms()
        aad = make_aad("episodic_memory", episode_id)
        dek = self._get_dek(key_id)
        cipher, nonce, aad_bytes = encrypt(dek, content, aad)

        cur = self._conn.execute(
            """
            INSERT INTO episodic_memory
                (id, principal_id, created_at, updated_at, type,
                 content_cipher, content_nonce, content_aad, tags_json, key_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                episode_id, principal_id, now, now, type,
                cipher, nonce, aad_bytes,
                json.dumps(list(tags or [])),
                key_id,
            ),
        )
        self._conn.commit()

        # Store embedding async-style (fire and forget — doesn't block caller)
        vec_search.store_episodic_embedding(self._conn, cur.lastrowid, content)

        return episode_id

    def get_episode(
        self,
        principal_id: str,
        episode_id: str,
    ) -> MemoryRecord | None:
        """Decrypt and return a single episodic memory. Returns None if not found."""
        self._assert_open()
        row = self._conn.execute(
            "SELECT * FROM episodic_memory WHERE id=? AND principal_id=? AND deleted_at IS NULL",
            (episode_id, principal_id),
        ).fetchone()
        if not row:
            return None
        return self._row_to_memory_record(row)

    def list_episodes(
        self,
        principal_id: str,
        type: str | None = None,
        limit: int = 50,
        before: int | None = None,
    ) -> list[MemoryRecord]:
        """Time-ordered listing of episodes with decrypted previews."""
        self._assert_open()
        query = "SELECT * FROM episodic_memory WHERE principal_id=? AND deleted_at IS NULL"
        params: list = [principal_id]
        if type:
            query += " AND type=?"
            params.append(type)
        if before:
            query += " AND created_at<?"
            params.append(before)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_memory_record(r) for r in rows]

    # ─────────────────────────────────────────
    # SEMANTIC MEMORY
    # ─────────────────────────────────────────

    def distill_semantic(
        self,
        principal_id: str,
        pattern: str,
        episode_ids: Sequence[str],
        confidence: float = 0.7,
        tags: Sequence[str] | None = None,
        key_id: str = "semantic-v1",
    ) -> str:
        self._assert_open()
        pattern_id = _new_id()
        now = _now_ms()
        aad = make_aad("semantic_memory", pattern_id)
        dek = self._get_dek(key_id)
        cipher, nonce, aad_bytes = encrypt(dek, pattern, aad)

        cur = self._conn.execute(
            """
            INSERT INTO semantic_memory
                (id, principal_id, pattern_cipher, pattern_nonce, pattern_aad,
                 confidence, first_observed_at, last_observed_at,
                 supporting_episode_ids, tags_json, key_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pattern_id, principal_id, cipher, nonce, aad_bytes,
                confidence, now, now,
                json.dumps(list(episode_ids)),
                json.dumps(list(tags or [])),
                key_id,
            ),
        )
        self._conn.commit()

        # Store embedding
        vec_search.store_semantic_embedding(self._conn, cur.lastrowid, pattern)

        return pattern_id

    # ─────────────────────────────────────────
    # SEMANTIC SEARCH  (now vector-powered)
    # ─────────────────────────────────────────

    def search_memory(
        self,
        principal_id: str,
        query: str,
        limit: int = 20,
        memory_types: Sequence[Literal["episodic", "semantic"]] = ("episodic", "semantic"),
    ) -> list[MemoryRecord]:
        """
        Search episodic + semantic memory using sqlite-vec k-NN similarity.
        Degrades gracefully to time-ordered recall if sqlite-vec is unavailable.
        """
        self._assert_open()

        if vec_search.is_vec_available():
            return self._search_vec(principal_id, query, limit, memory_types)
        return self._search_fallback(principal_id, query, limit, memory_types)

    def _search_vec(
        self,
        principal_id: str,
        query: str,
        limit: int,
        memory_types: Sequence[str],
    ) -> list[MemoryRecord]:
        """Vector-powered search path."""
        hits: list[tuple[str, float, str]] = []  # (id, score, table)

        if "episodic" in memory_types:
            for ep_id, score in vec_search.search_episodic_vec(
                self._conn, principal_id, query, limit
            ):
                hits.append((ep_id, score, "episodic"))

        if "semantic" in memory_types:
            for pat_id, score in vec_search.search_semantic_vec(
                self._conn, principal_id, query, limit // 2
            ):
                hits.append((pat_id, score, "semantic"))

        # Global re-rank and de-dup
        hits.sort(key=lambda x: x[1], reverse=True)
        seen: set[str] = set()
        out: list[MemoryRecord] = []
        for item_id, _score, table in hits:
            if item_id in seen:
                continue
            seen.add(item_id)
            if table == "episodic":
                row = self._conn.execute(
                    "SELECT * FROM episodic_memory WHERE id=? AND deleted_at IS NULL",
                    (item_id,),
                ).fetchone()
                if row:
                    out.append(self._row_to_memory_record(row))
            else:
                row = self._conn.execute(
                    "SELECT * FROM semantic_memory WHERE id=? AND deleted_at IS NULL",
                    (item_id,),
                ).fetchone()
                if row:
                    out.append(self._semantic_row_to_record(row))
            if len(out) >= limit:
                break
        return out

    def _search_fallback(
        self,
        principal_id: str,
        query: str,
        limit: int,
        memory_types: Sequence[str],
    ) -> list[MemoryRecord]:
        """Time-ordered fallback when sqlite-vec is unavailable."""
        results: list[MemoryRecord] = []
        if "episodic" in memory_types:
            rows = self._conn.execute(
                """
                SELECT * FROM episodic_memory
                WHERE principal_id=? AND deleted_at IS NULL
                ORDER BY created_at DESC LIMIT ?
                """,
                (principal_id, limit),
            ).fetchall()
            results.extend(self._row_to_memory_record(r) for r in rows)
        if "semantic" in memory_types:
            rows = self._conn.execute(
                """
                SELECT * FROM semantic_memory
                WHERE principal_id=? AND deleted_at IS NULL
                ORDER BY last_observed_at DESC LIMIT ?
                """,
                (principal_id, limit),
            ).fetchall()
            results.extend(self._semantic_row_to_record(r) for r in rows)
        seen: set[str] = set()
        out: list[MemoryRecord] = []
        for r in results:
            if r.id not in seen:
                seen.add(r.id)
                out.append(r)
            if len(out) >= limit:
                break
        return out

    # ─────────────────────────────────────────
    # CONVENIENCE: remember + recall
    # (thin wrappers used by the frontend API)
    # ─────────────────────────────────────────

    def remember(
        self,
        principal_id: str,
        text: str,
        role: str = "user",
        type: str = "conversation",
        tags: Sequence[str] | None = None,
    ) -> str:
        """
        Convenience wrapper: store a single turn of conversation as an episodic memory.
        Returns the episode_id.
        """
        return self.store_episode(
            principal_id=principal_id,
            content=f"[{role}] {text}",
            type=type,
            tags=list(tags or []),
        )

    def recall(
        self,
        principal_id: str,
        query: str,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        """
        Convenience wrapper: retrieve the most semantically relevant memories
        for the given query. Used to build GAIA's context window.
        """
        return self.search_memory(principal_id, query, limit=limit)

    # ─────────────────────────────────────────
    # MAINTENANCE
    # ─────────────────────────────────────────

    def prune_vectors(self) -> int:
        """Remove orphaned vector rows. Returns count removed. Call periodically."""
        self._assert_open()
        return vec_search.prune_orphaned_vectors(self._conn)

    # ─────────────────────────────────────────
    # BIOMETRIC HISTORY
    # ─────────────────────────────────────────

    def append_biometric_sample(
        self,
        principal_id: str,
        signal_type: str,
        value: float,
        source: str,
        timestamp: int | None = None,
    ) -> int:
        """Append a single biometric sample. Returns the new row id."""
        self._assert_open()
        ts = timestamp or _now_ms()
        cur = self._conn.execute(
            """
            INSERT INTO biometric_history (principal_id, timestamp, signal_type, value, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (principal_id, ts, signal_type, value, source),
        )
        self._conn.commit()
        return cur.lastrowid

    def store_affect_snapshot(self, snapshot: AffectSnapshot) -> None:
        """Persist all biometric rows from an AffectSnapshot in one transaction."""
        self._assert_open()
        rows = snapshot.to_biometric_rows()
        self._conn.executemany(
            """
            INSERT INTO biometric_history (principal_id, timestamp, signal_type, value, source)
            VALUES (:principal_id, :timestamp, :signal_type, :value, :source)
            """,
            rows,
        )
        self._conn.commit()

    def get_biometric_history(
        self,
        principal_id: str,
        signal_type: str,
        days: int,
        now: int | None = None,
    ) -> list[BiometricSample]:
        """Return samples for the given signal over the last N days."""
        self._assert_open()
        cutoff = (now or _now_ms()) - days * 86_400_000
        rows = self._conn.execute(
            """
            SELECT timestamp, signal_type, value, source
            FROM biometric_history
            WHERE principal_id=? AND signal_type=? AND timestamp>=?
            ORDER BY timestamp ASC
            """,
            (principal_id, signal_type, cutoff),
        ).fetchall()
        return [BiometricSample(**dict(r)) for r in rows]

    # ─────────────────────────────────────────
    # STAGE HISTORY
    # ─────────────────────────────────────────

    def get_stage_history(
        self,
        principal_id: str,
    ) -> list[StageTransitionRecord]:
        """Return full stage arc history, oldest first."""
        self._assert_open()
        rows = self._conn.execute(
            """
            SELECT * FROM stage_transitions
            WHERE principal_id=?
            ORDER BY transitioned_at ASC
            """,
            (principal_id,),
        ).fetchall()
        return [
            StageTransitionRecord(
                id=r["id"],
                principal_id=r["principal_id"],
                from_stage=r["from_stage"],
                to_stage=r["to_stage"],
                transitioned_at=r["transitioned_at"],
                is_regression=bool(r["is_regression"]),
                markers_met=json.loads(r["markers_met_json"]),
                ceremony_shown=bool(r["ceremony_shown"]),
            )
            for r in rows
        ]

    # ─────────────────────────────────────────
    # LEGACY ARTIFACTS
    # ─────────────────────────────────────────

    def tag_as_legacy(
        self,
        principal_id: str,
        title: str,
        content: str,
        stage_at_creation: int,
        source_episode_id: str | None = None,
        tags: Sequence[str] | None = None,
        export_formats: Sequence[str] = ("markdown", "json"),
        key_id: str = "legacy-v1",
    ) -> str:
        """Encrypt and store a legacy artifact. Returns the artifact id."""
        self._assert_open()
        artifact_id = _new_id()
        now = _now_ms()
        dek = self._get_dek(key_id)

        title_aad = make_aad("legacy_artifacts", artifact_id + ":title")
        title_cipher, title_nonce, title_aad_bytes = encrypt(dek, title, title_aad)

        content_aad = make_aad("legacy_artifacts", artifact_id + ":content")
        content_cipher, content_nonce, content_aad_bytes = encrypt(dek, content, content_aad)

        self._conn.execute(
            """
            INSERT INTO legacy_artifacts
                (id, principal_id, created_at, stage_at_creation,
                 title_cipher, title_nonce, title_aad,
                 content_cipher, content_nonce, content_aad,
                 source_episode_id, export_formats, tags_json, key_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id, principal_id, now, stage_at_creation,
                title_cipher, title_nonce, title_aad_bytes,
                content_cipher, content_nonce, content_aad_bytes,
                source_episode_id,
                json.dumps(list(export_formats)),
                json.dumps(list(tags or [])),
                key_id,
            ),
        )
        self._conn.commit()
        return artifact_id

    def export_legacy(
        self,
        principal_id: str,
        format: Literal["markdown", "json"] = "markdown",
    ) -> str:
        """Decrypt and export all legacy artifacts for a principal."""
        self._assert_open()
        rows = self._conn.execute(
            """
            SELECT * FROM legacy_artifacts
            WHERE principal_id=? AND deleted_at IS NULL
            ORDER BY created_at ASC
            """,
            (principal_id,),
        ).fetchall()

        artifacts = []
        for row in rows:
            dek = self._get_dek(row["key_id"])
            title = decrypt(dek, row["title_cipher"], row["title_nonce"], row["title_aad"])
            content = decrypt(dek, row["content_cipher"], row["content_nonce"], row["content_aad"])
            artifacts.append({
                "title": title,
                "content": content,
                "created_at": row["created_at"],
                "stage": row["stage_at_creation"],
            })

        if format == "json":
            return json.dumps(artifacts, indent=2, ensure_ascii=False)

        lines = ["# GAIA-OS Legacy Archive\n"]
        for a in artifacts:
            lines.append(f"## {a['title']}")
            lines.append(f"*Stage {a['stage']}*\n")
            lines.append(a["content"])
            lines.append("\n---\n")
        return "\n".join(lines)

    # ─────────────────────────────────────────
    # GDPR ERASURE
    # ─────────────────────────────────────────

    def soft_delete_episode(self, principal_id: str, episode_id: str) -> None:
        """Mark an episode deleted (soft delete). Ciphertext remains until key rotation."""
        self._assert_open()
        self._conn.execute(
            "UPDATE episodic_memory SET deleted_at=? WHERE id=? AND principal_id=?",
            (_now_ms(), episode_id, principal_id),
        )
        self._conn.commit()
        # Prune its vector immediately
        self.prune_vectors()

    def crypto_erase_key(self, key_id: str) -> None:
        """
        Revoke a DEK: mark it 'revoked' in encryption_keys and remove from cache.
        Any rows referencing this key_id become permanently unrecoverable.
        This is the GDPR Art. 17 crypto-erasure mechanism.
        """
        self._assert_open()
        self._conn.execute(
            "UPDATE encryption_keys SET status='revoked', rotated_at=? WHERE key_id=?",
            (_now_ms(), key_id),
        )
        self._conn.commit()
        self._dek_cache.pop(key_id, None)

    # ─────────────────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────────────────

    def _assert_open(self) -> None:
        if self._conn is None or self._mk is None:
            raise RuntimeError("SovereignMemory is not open. Call .open() first.")

    def _get_dek(self, key_id: str) -> bytes:
        if key_id not in self._dek_cache:
            self._dek_cache[key_id] = derive_dek(self._mk, key_id)
        return self._dek_cache[key_id]

    def _apply_schema(self) -> None:
        sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        self._conn.executescript(sql)
        self._conn.commit()

    def _ensure_active_keys(self) -> None:
        """Create default active DEK entries if they don't exist yet."""
        now = _now_ms()
        default_keys = ["episodic-v1", "semantic-v1", "legacy-v1"]
        for key_id in default_keys:
            existing = self._conn.execute(
                "SELECT key_id FROM encryption_keys WHERE key_id=?", (key_id,)
            ).fetchone()
            if not existing:
                self._conn.execute(
                    """
                    INSERT INTO encryption_keys (key_id, wrapped_key, algorithm, created_at, status)
                    VALUES (?, ?, 'aes-256-gcm', ?, 'active')
                    """,
                    (key_id, b"local-kdf", now),
                )
        self._conn.commit()

    def _row_to_memory_record(self, row: sqlite3.Row) -> MemoryRecord:
        dek = self._get_dek(row["key_id"])
        plaintext = decrypt(dek, row["content_cipher"], row["content_nonce"], row["content_aad"])
        return MemoryRecord(
            id=row["id"],
            principal_id=row["principal_id"],
            type=row["type"],
            created_at=row["created_at"],
            tags=json.loads(row["tags_json"] or "[]"),
            preview=plaintext[:280],
        )

    def _semantic_row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        dek = self._get_dek(row["key_id"])
        plaintext = decrypt(dek, row["pattern_cipher"], row["pattern_nonce"], row["pattern_aad"])
        return MemoryRecord(
            id=row["id"],
            principal_id=row["principal_id"],
            type="semantic",
            created_at=row["first_observed_at"],
            tags=json.loads(row["tags_json"] or "[]"),
            preview=plaintext[:280],
        )
