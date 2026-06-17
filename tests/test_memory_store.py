"""
tests/test_memory_store.py
Comprehensive test suite for GAIA-OS semantic memory layer.

Covers:
  - Schema / migrations
  - Write path  (remember_sync, remember_item, metadata JSON)
  - Read path   (retrieve_sync fallback, score ordering, filters)
  - Soft-delete & hard-delete
  - Pruner      (capacity enforcement, TTL eviction, PERMANENT items)
  - Stats / count
  - User isolation
  - FallbackEmbedder determinism
  - MemoryItem helpers (is_expired, age_seconds, priority_score)

All tests use FallbackEmbedder (no network, no Ollama, no GPU required)
and a fresh in-memory-style temp SQLite file per test via tmp_path.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import List

import pytest

from core.memory.embedder import FallbackEmbedder
from core.memory.items import (
    MemoryItem,
    MemoryKind,
    MemoryPruner,
    MemoryStore,
    MemoryTier,
    RetrievedMemory,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_memory.db"


@pytest.fixture()
def store(db_path: Path) -> MemoryStore:
    return MemoryStore(db_path=db_path, embedder=FallbackEmbedder(dim=64))


@pytest.fixture()
def pruner(store: MemoryStore) -> MemoryPruner:
    return MemoryPruner(store, capacity=10, batch_size=5, min_age_sec=0)


UID = "user_gaia"
UID2 = "user_other"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _remember(store: MemoryStore, text: str, user_id: str = UID, **kwargs) -> int:
    return store.remember_sync(user_id=user_id, text=text, **kwargs)


# ---------------------------------------------------------------------------
# Schema / migrations
# ---------------------------------------------------------------------------

class TestSchema:
    def test_db_file_created(self, db_path: Path, store: MemoryStore) -> None:
        assert db_path.exists()

    def test_memory_items_table_exists(self, store: MemoryStore) -> None:
        row = store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_items'"
        ).fetchone()
        assert row is not None

    def test_metadata_column_exists(self, store: MemoryStore) -> None:
        cols = [r[1] for r in store._conn.execute("PRAGMA table_info(memory_items)").fetchall()]
        assert "metadata" in cols

    def test_wal_mode_enabled(self, store: MemoryStore) -> None:
        mode = store._conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"

    def test_idempotent_migrations(self, db_path: Path) -> None:
        # Opening the same DB twice should not raise
        s1 = MemoryStore(db_path=db_path, embedder=FallbackEmbedder(dim=64))
        s2 = MemoryStore(db_path=db_path, embedder=FallbackEmbedder(dim=64))
        s1.close()
        s2.close()


# ---------------------------------------------------------------------------
# Write path
# ---------------------------------------------------------------------------

class TestWritePath:
    def test_remember_sync_returns_int(self, store: MemoryStore) -> None:
        item_id = _remember(store, "Hello world")
        assert isinstance(item_id, int)
        assert item_id > 0

    def test_remember_sync_persists_row(self, store: MemoryStore) -> None:
        _remember(store, "Persistent text")
        count = store.count(user_id=UID)
        assert count == 1

    def test_multiple_remembers_increment_count(self, store: MemoryStore) -> None:
        for i in range(5):
            _remember(store, f"Memory {i}")
        assert store.count(user_id=UID) == 5

    def test_kind_is_stored(self, store: MemoryStore) -> None:
        _remember(store, "I hate mornings", kind=MemoryKind.PREFERENCE)
        row = store._conn.execute(
            "SELECT kind FROM memory_items WHERE user_id = ?", (UID,)
        ).fetchone()
        assert row[0] == "preference"

    def test_tier_is_stored(self, store: MemoryStore) -> None:
        _remember(store, "Permanent fact", tier=MemoryTier.PERMANENT)
        row = store._conn.execute(
            "SELECT tier FROM memory_items WHERE user_id = ?", (UID,)
        ).fetchone()
        assert row[0] == "permanent"

    def test_importance_is_stored(self, store: MemoryStore) -> None:
        _remember(store, "High importance", importance=0.99)
        row = store._conn.execute(
            "SELECT importance FROM memory_items WHERE user_id = ?", (UID,)
        ).fetchone()
        assert abs(float(row[0]) - 0.99) < 1e-4

    def test_topic_tag_is_stored(self, store: MemoryStore) -> None:
        _remember(store, "Python tips", topic_tag="programming")
        row = store._conn.execute(
            "SELECT topic_tag FROM memory_items WHERE user_id = ?", (UID,)
        ).fetchone()
        assert row[0] == "programming"

    def test_metadata_json_round_trip(self, store: MemoryStore) -> None:
        meta = {"bond_depth": 42.5, "affect": "curious"}
        _remember(store, "With metadata", metadata=meta)
        row = store._conn.execute(
            "SELECT metadata FROM memory_items WHERE user_id = ?", (UID,)
        ).fetchone()
        recovered = json.loads(row[0])
        assert recovered == meta

    def test_remember_item_convenience(self, store: MemoryStore) -> None:
        item = MemoryItem(
            user_id=UID,
            text="Via remember_item",
            kind=MemoryKind.FACT,
            tier=MemoryTier.LONG_TERM,
            importance=0.8,
        )
        item_id = asyncio.run(store.remember_item(item))
        assert isinstance(item_id, int)
        assert store.count(user_id=UID) == 1

    def test_deleted_defaults_to_zero(self, store: MemoryStore) -> None:
        _remember(store, "Not deleted")
        row = store._conn.execute(
            "SELECT deleted FROM memory_items WHERE user_id = ?", (UID,)
        ).fetchone()
        assert row[0] == 0

    def test_created_at_is_recent_unix_ts(self, store: MemoryStore) -> None:
        before = int(time.time())
        _remember(store, "Timestamp check")
        after = int(time.time())
        row = store._conn.execute(
            "SELECT created_at FROM memory_items WHERE user_id = ?", (UID,)
        ).fetchone()
        assert before <= int(row[0]) <= after


# ---------------------------------------------------------------------------
# Read path (fallback mode — no sqlite-vec)
# ---------------------------------------------------------------------------

class TestReadPath:
    def test_retrieve_sync_returns_list(self, store: MemoryStore) -> None:
        _remember(store, "Some memory")
        results = store.retrieve_sync(user_id=UID, query="memory")
        assert isinstance(results, list)

    def test_retrieve_sync_returns_memory_items(self, store: MemoryStore) -> None:
        _remember(store, "A fact about GAIA")
        results = store.retrieve_sync(user_id=UID, query="GAIA")
        assert all(isinstance(r, MemoryItem) for r in results)

    def test_retrieve_respects_top_k(self, store: MemoryStore) -> None:
        for i in range(20):
            _remember(store, f"Memory item {i}")
        results = store.retrieve_sync(user_id=UID, query="memory", top_k=5)
        assert len(results) <= 5

    def test_retrieve_only_own_user(self, store: MemoryStore) -> None:
        _remember(store, "User one memory", user_id=UID)
        _remember(store, "User two memory", user_id=UID2)
        results = store.retrieve_sync(user_id=UID, query="memory")
        assert all(r.user_id == UID for r in results)

    def test_retrieve_excludes_soft_deleted(self, store: MemoryStore) -> None:
        item_id = _remember(store, "Will be deleted")
        store.forget(item_id)
        results = store.retrieve_sync(user_id=UID, query="deleted")
        assert all(r.id != item_id for r in results)

    def test_kind_filter(self, store: MemoryStore) -> None:
        _remember(store, "Preference item", kind=MemoryKind.PREFERENCE)
        _remember(store, "Fact item",       kind=MemoryKind.FACT)
        results = store.retrieve_sync(
            user_id=UID, query="item", kinds=[MemoryKind.PREFERENCE]
        )
        assert all(r.kind == MemoryKind.PREFERENCE for r in results)
        assert len(results) == 1

    def test_tier_filter(self, store: MemoryStore) -> None:
        _remember(store, "Long-term item",  tier=MemoryTier.LONG_TERM)
        _remember(store, "Ephemeral item",  tier=MemoryTier.EPHEMERAL)
        results = store.retrieve_sync(
            user_id=UID, query="item", tiers=[MemoryTier.LONG_TERM]
        )
        assert all(r.tier == MemoryTier.LONG_TERM for r in results)
        assert len(results) == 1

    def test_topic_tag_filter(self, store: MemoryStore) -> None:
        _remember(store, "Python tips",  topic_tag="programming")
        _remember(store, "Walking tips", topic_tag="fitness")
        results = store.retrieve_sync(
            user_id=UID, query="tips", topic_tag="programming"
        )
        assert all(r.topic_tag == "programming" for r in results)
        assert len(results) == 1

    def test_importance_floor_filter(self, store: MemoryStore) -> None:
        _remember(store, "Low importance",  importance=0.1)
        _remember(store, "High importance", importance=0.9)
        results = store.retrieve_sync(
            user_id=UID, query="importance", importance_floor=0.5
        )
        assert all(r.importance >= 0.5 for r in results)
        assert len(results) == 1

    def test_since_ts_filter(self, store: MemoryStore) -> None:
        _remember(store, "Old memory")
        future_ts = int(time.time()) + 86_400  # 1 day from now
        results = store.retrieve_sync(
            user_id=UID, query="memory", since_ts=future_ts
        )
        assert len(results) == 0

    def test_empty_store_returns_empty_list(self, store: MemoryStore) -> None:
        results = store.retrieve_sync(user_id=UID, query="anything")
        assert results == []


# ---------------------------------------------------------------------------
# Soft-delete & hard-delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_forget_soft_deletes(self, store: MemoryStore) -> None:
        item_id = _remember(store, "To be forgotten")
        store.forget(item_id)
        row = store._conn.execute(
            "SELECT deleted FROM memory_items WHERE id = ?", (item_id,)
        ).fetchone()
        assert row[0] == 1

    def test_forget_reduces_count(self, store: MemoryStore) -> None:
        item_id = _remember(store, "Count me then forget")
        assert store.count(user_id=UID) == 1
        store.forget(item_id)
        assert store.count(user_id=UID) == 0

    def test_forget_user_soft_deletes_all(self, store: MemoryStore) -> None:
        for i in range(5):
            _remember(store, f"Memory {i}")
        deleted = store.forget_user(UID)
        assert deleted == 5
        assert store.count(user_id=UID) == 0

    def test_forget_user_does_not_affect_other_user(self, store: MemoryStore) -> None:
        _remember(store, "User A memory", user_id=UID)
        _remember(store, "User B memory", user_id=UID2)
        store.forget_user(UID)
        assert store.count(user_id=UID2) == 1

    def test_hard_delete_removes_rows(self, store: MemoryStore) -> None:
        item_id = _remember(store, "Hard delete me")
        store.forget(item_id)
        erased = store.hard_delete_soft_deleted()
        assert erased == 1
        row = store._conn.execute(
            "SELECT id FROM memory_items WHERE id = ?", (item_id,)
        ).fetchone()
        assert row is None

    def test_hard_delete_returns_zero_when_nothing_to_delete(self, store: MemoryStore) -> None:
        _remember(store, "Still alive")
        erased = store.hard_delete_soft_deleted()
        assert erased == 0


# ---------------------------------------------------------------------------
# Stats / count
# ---------------------------------------------------------------------------

class TestStats:
    def test_count_zero_for_empty_store(self, store: MemoryStore) -> None:
        assert store.count(user_id=UID) == 0

    def test_count_reflects_inserts(self, store: MemoryStore) -> None:
        for i in range(7):
            _remember(store, f"Item {i}")
        assert store.count(user_id=UID) == 7

    def test_count_all_users(self, store: MemoryStore) -> None:
        _remember(store, "User A", user_id=UID)
        _remember(store, "User B", user_id=UID2)
        assert store.count() == 2

    def test_stats_returns_dict(self, store: MemoryStore) -> None:
        assert isinstance(store.stats(user_id=UID), dict)

    def test_stats_total_key(self, store: MemoryStore) -> None:
        _remember(store, "One")
        stats = store.stats(user_id=UID)
        assert stats["total"] == 1

    def test_stats_by_kind(self, store: MemoryStore) -> None:
        _remember(store, "Preference", kind=MemoryKind.PREFERENCE)
        _remember(store, "Fact",       kind=MemoryKind.FACT)
        stats = store.stats(user_id=UID)
        assert stats["by_kind"]["preference"] == 1
        assert stats["by_kind"]["fact"] == 1

    def test_stats_vec_enabled_key_exists(self, store: MemoryStore) -> None:
        stats = store.stats()
        assert "vec_enabled" in stats

    def test_stats_db_path_key_exists(self, store: MemoryStore) -> None:
        stats = store.stats()
        assert "db_path" in stats


# ---------------------------------------------------------------------------
# User isolation
# ---------------------------------------------------------------------------

class TestUserIsolation:
    def test_counts_are_isolated(self, store: MemoryStore) -> None:
        for _ in range(3):
            _remember(store, "User A mem", user_id=UID)
        for _ in range(5):
            _remember(store, "User B mem", user_id=UID2)
        assert store.count(user_id=UID)  == 3
        assert store.count(user_id=UID2) == 5

    def test_retrieve_never_returns_other_users_items(self, store: MemoryStore) -> None:
        _remember(store, "Secret of user B", user_id=UID2)
        results = store.retrieve_sync(user_id=UID, query="secret")
        assert all(r.user_id == UID for r in results)


# ---------------------------------------------------------------------------
# Pruner
# ---------------------------------------------------------------------------

class TestPruner:
    def test_no_pruning_below_capacity(self, store: MemoryStore, pruner: MemoryPruner) -> None:
        for i in range(5):
            _remember(store, f"Item {i}")
        report = pruner.run(user_id=UID)
        assert report.rows_pruned == 0

    def test_pruning_above_capacity(self, store: MemoryStore, pruner: MemoryPruner) -> None:
        for i in range(20):
            _remember(store, f"Item {i}", importance=0.3)
        report = pruner.run(user_id=UID)
        assert report.rows_pruned > 0
        assert report.rows_after <= pruner._capacity + pruner._batch_size

    def test_permanent_items_never_pruned(self, store: MemoryStore, pruner: MemoryPruner) -> None:
        for i in range(15):
            _remember(store, f"Perm {i}", tier=MemoryTier.PERMANENT, importance=0.1)
        pruner.run(user_id=UID)
        perms = store._conn.execute(
            "SELECT COUNT(*) FROM memory_items WHERE user_id = ? AND tier = 'permanent' AND deleted = 0",
            (UID,)
        ).fetchone()[0]
        assert perms == 15

    def test_prune_report_fields(self, store: MemoryStore, pruner: MemoryPruner) -> None:
        report = pruner.run(user_id=UID)
        assert hasattr(report, "rows_before")
        assert hasattr(report, "rows_pruned")
        assert hasattr(report, "rows_after")
        assert hasattr(report, "duration_ms")

    def test_prune_expired_ttl(self, store: MemoryStore, pruner: MemoryPruner) -> None:
        # TTL already elapsed (1 second, created 10 seconds ago)
        store._conn.execute(
            """
            INSERT INTO memory_items
                (user_id, kind, tier, role, text, importance, created_at, ttl_seconds, deleted)
            VALUES (?, 'message', 'ephemeral', 'user', 'Expired TTL', 0.5, ?, 1, 0)
            """,
            (UID, int(time.time()) - 10),
        )
        store._conn.commit()
        pruned = pruner.prune_expired_ttl(user_id=UID)
        assert pruned == 1
        assert store.count(user_id=UID) == 0

    def test_prune_ttl_does_not_delete_live_items(self, store: MemoryStore, pruner: MemoryPruner) -> None:
        _remember(store, "No TTL — lives forever")
        pruned = pruner.prune_expired_ttl(user_id=UID)
        assert pruned == 0
        assert store.count(user_id=UID) == 1


# ---------------------------------------------------------------------------
# FallbackEmbedder determinism
# ---------------------------------------------------------------------------

class TestFallbackEmbedder:
    def test_embed_returns_correct_dim(self) -> None:
        e = FallbackEmbedder(dim=64)
        vec = asyncio.run(e.embed("hello world"))
        assert len(vec) == 64

    def test_embed_is_deterministic(self) -> None:
        e = FallbackEmbedder(dim=64)
        v1 = asyncio.run(e.embed("same text"))
        v2 = asyncio.run(e.embed("same text"))
        assert v1 == v2

    def test_different_texts_give_different_vectors(self) -> None:
        e = FallbackEmbedder(dim=64)
        v1 = asyncio.run(e.embed("text A"))
        v2 = asyncio.run(e.embed("text B"))
        assert v1 != v2

    def test_values_in_range(self) -> None:
        e = FallbackEmbedder(dim=64)
        vec = asyncio.run(e.embed("range check"))
        assert all(-1.0 <= v <= 1.0 for v in vec)


# ---------------------------------------------------------------------------
# MemoryItem helpers
# ---------------------------------------------------------------------------

class TestMemoryItemHelpers:
    def test_is_expired_false_when_no_ttl(self) -> None:
        item = MemoryItem(user_id=UID, text="No TTL")
        assert item.is_expired() is False

    def test_is_expired_true_when_elapsed(self) -> None:
        item = MemoryItem(
            user_id=UID, text="Expired",
            created_at=int(time.time()) - 100,
            ttl_seconds=10,
        )
        assert item.is_expired() is True

    def test_is_expired_false_when_not_elapsed(self) -> None:
        item = MemoryItem(
            user_id=UID, text="Still live",
            created_at=int(time.time()),
            ttl_seconds=3_600,
        )
        assert item.is_expired() is False

    def test_age_seconds_nonnegative(self) -> None:
        item = MemoryItem(user_id=UID, text="Age check")
        assert item.age_seconds() >= 0

    def test_priority_score_higher_for_important_items(self) -> None:
        high = MemoryItem(user_id=UID, text="High", importance=0.9, tier=MemoryTier.PERMANENT)
        low  = MemoryItem(user_id=UID, text="Low",  importance=0.1, tier=MemoryTier.EPHEMERAL)
        assert high.priority_score() > low.priority_score()

    def test_priority_score_in_range(self) -> None:
        item = MemoryItem(user_id=UID, text="Range", importance=0.5)
        score = item.priority_score()
        assert 0.0 <= score <= 2.0  # generous upper bound
