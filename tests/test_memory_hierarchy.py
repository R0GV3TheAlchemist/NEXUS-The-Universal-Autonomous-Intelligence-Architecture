"""
tests/test_memory_hierarchy.py
Unit + integration tests for the GAIA MemoryHierarchy.

All tests are fully in-process — no network, no filesystem (SQLite
short-term store runs in ':memory:' mode).

See specs/architecture/MEMORY_HIERARCHY_SPEC.md for the full checklist.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.memory.hierarchy import MemoryQuery, MemoryRouter, MemoryStore, MemoryTier
from core.memory.tiers.working import WorkingMemoryStore
from core.memory.tiers.short_term import ShortTermMemoryStore
from core.memory.tiers.episodic import EpisodicMemoryStore
from core.memory.tiers.semantic import SemanticMemoryStore
from core.memory.tiers.long_term import LongTermMemoryStore
from core.memory import build_default_router


# ── Helpers ───────────────────────────────────────────────────────────────── #

def make_in_memory_router() -> MemoryRouter:
    """Build a MemoryRouter wired with fully in-process stores."""
    return MemoryRouter({
        MemoryTier.WORKING:    WorkingMemoryStore(),
        MemoryTier.SHORT_TERM: ShortTermMemoryStore(db_path=":memory:"),
        MemoryTier.EPISODIC:   EpisodicMemoryStore(),
        MemoryTier.SEMANTIC:   SemanticMemoryStore(),
        MemoryTier.LONG_TERM:  LongTermMemoryStore(),
    })


# ── MemoryTier enum ─────────────────────────────────────────────────────────── #

class TestMemoryTier:
    def test_permanent_tiers(self):
        assert MemoryTier.SEMANTIC.is_permanent
        assert MemoryTier.LONG_TERM.is_permanent

    def test_volatile_tiers_not_permanent(self):
        for tier in (MemoryTier.WORKING, MemoryTier.SHORT_TERM, MemoryTier.EPISODIC):
            assert not tier.is_permanent

    def test_default_ttl_working(self):
        assert MemoryTier.WORKING.default_ttl_hours == 0.0

    def test_default_ttl_short_term(self):
        assert MemoryTier.SHORT_TERM.default_ttl_hours == 48.0

    def test_default_ttl_episodic(self):
        assert MemoryTier.EPISODIC.default_ttl_hours == 720.0

    def test_default_ttl_permanent_is_none(self):
        assert MemoryTier.SEMANTIC.default_ttl_hours is None
        assert MemoryTier.LONG_TERM.default_ttl_hours is None

    def test_five_tiers_defined(self):
        assert len(MemoryTier) == 5


# ── MemoryQuery ─────────────────────────────────────────────────────────────── #

class TestMemoryQuery:
    def test_valid_intent_context(self):
        q = MemoryQuery("test", intent="context")
        assert q.intent == "context"

    def test_valid_all_intents(self):
        for intent in ("context", "recall", "fact", "identity", "full"):
            q = MemoryQuery("test", intent=intent)
            assert q.intent == intent

    def test_invalid_intent_raises(self):
        with pytest.raises(ValueError, match="Invalid intent"):
            MemoryQuery("test", intent="unknown")

    def test_recency_weight_out_of_range_raises(self):
        with pytest.raises(ValueError, match="recency_weight"):
            MemoryQuery("test", intent="fact", recency_weight=1.5)

    def test_max_results_clamped_to_at_least_1(self):
        q = MemoryQuery("test", intent="fact", max_results=0)
        assert q.max_results == 1

    def test_default_canon_refs(self):
        q = MemoryQuery("test", intent="fact")
        assert "C34" in q.canon_refs and "C01" in q.canon_refs

    def test_repr_includes_intent(self):
        q = MemoryQuery("shadow work", intent="recall", gaian_id="luna")
        assert "recall" in repr(q)
        assert "luna" in repr(q)


# ── MemoryRouter routing ────────────────────────────────────────────────────── #

class TestMemoryRouterRouting:
    """Verify that intent maps to the correct set of tier stores."""

    def _make_spy_router(self, intent: str):
        """Build a router with mock stores, return (router, mock_stores_dict)."""
        stores = {tier: AsyncMock(spec=MemoryStore) for tier in MemoryTier}
        for mock in stores.values():
            mock.search = AsyncMock(return_value=[])
        router = MemoryRouter(stores)
        return router, stores

    @pytest.mark.asyncio
    async def test_intent_context_calls_working_and_short_term(self):
        router, stores = self._make_spy_router("context")
        await router.search(MemoryQuery("hi", intent="context"))
        stores[MemoryTier.WORKING].search.assert_called_once()
        stores[MemoryTier.SHORT_TERM].search.assert_called_once()
        stores[MemoryTier.EPISODIC].search.assert_not_called()
        stores[MemoryTier.SEMANTIC].search.assert_not_called()
        stores[MemoryTier.LONG_TERM].search.assert_not_called()

    @pytest.mark.asyncio
    async def test_intent_recall_calls_short_term_and_episodic(self):
        router, stores = self._make_spy_router("recall")
        await router.search(MemoryQuery("last session", intent="recall"))
        stores[MemoryTier.WORKING].search.assert_not_called()
        stores[MemoryTier.SHORT_TERM].search.assert_called_once()
        stores[MemoryTier.EPISODIC].search.assert_called_once()

    @pytest.mark.asyncio
    async def test_intent_fact_calls_only_semantic(self):
        router, stores = self._make_spy_router("fact")
        await router.search(MemoryQuery("C32", intent="fact"))
        stores[MemoryTier.SEMANTIC].search.assert_called_once()
        for tier in (MemoryTier.WORKING, MemoryTier.SHORT_TERM, MemoryTier.EPISODIC, MemoryTier.LONG_TERM):
            stores[tier].search.assert_not_called()

    @pytest.mark.asyncio
    async def test_intent_identity_calls_only_long_term(self):
        router, stores = self._make_spy_router("identity")
        await router.search(MemoryQuery("who is luna", intent="identity"))
        stores[MemoryTier.LONG_TERM].search.assert_called_once()
        for tier in (MemoryTier.WORKING, MemoryTier.SHORT_TERM, MemoryTier.EPISODIC, MemoryTier.SEMANTIC):
            stores[tier].search.assert_not_called()

    @pytest.mark.asyncio
    async def test_intent_full_calls_all_tiers(self):
        router, stores = self._make_spy_router("full")
        await router.search(MemoryQuery("everything", intent="full"))
        for tier in MemoryTier:
            stores[tier].search.assert_called_once()

    @pytest.mark.asyncio
    async def test_explicit_tier_override_bypasses_intent(self):
        router, stores = self._make_spy_router("recall")
        explicit_tiers = [MemoryTier.SEMANTIC]
        q = MemoryQuery("canon fact", intent="recall", tiers=explicit_tiers)
        await router.search(q)
        stores[MemoryTier.SEMANTIC].search.assert_called_once()
        stores[MemoryTier.SHORT_TERM].search.assert_not_called()
        stores[MemoryTier.EPISODIC].search.assert_not_called()


# ── MemoryRouter ranking ────────────────────────────────────────────────────── #

class TestMemoryRouterRanking:
    @pytest.mark.asyncio
    async def test_ranking_prefers_high_relevance_at_weight_0(self):
        stores = {tier: AsyncMock(spec=MemoryStore) for tier in MemoryTier}
        stores[MemoryTier.SEMANTIC].search = AsyncMock(return_value=[
            {"key": "a", "value": "high relevance", "_relevance": 0.9, "_recency": 0.1},
            {"key": "b", "value": "low relevance",  "_relevance": 0.1, "_recency": 0.9},
        ])
        for tier in MemoryTier:
            if tier != MemoryTier.SEMANTIC:
                stores[tier].search = AsyncMock(return_value=[])
        router = MemoryRouter(stores)
        results = await router.search(MemoryQuery("q", intent="fact", recency_weight=0.0))
        assert results[0]["key"] == "a"

    @pytest.mark.asyncio
    async def test_ranking_prefers_high_recency_at_weight_1(self):
        stores = {tier: AsyncMock(spec=MemoryStore) for tier in MemoryTier}
        stores[MemoryTier.SEMANTIC].search = AsyncMock(return_value=[
            {"key": "a", "value": "fresh", "_relevance": 0.1, "_recency": 0.9},
            {"key": "b", "value": "stale", "_relevance": 0.9, "_recency": 0.1},
        ])
        for tier in MemoryTier:
            if tier != MemoryTier.SEMANTIC:
                stores[tier].search = AsyncMock(return_value=[])
        router = MemoryRouter(stores)
        results = await router.search(MemoryQuery("q", intent="fact", recency_weight=1.0))
        assert results[0]["key"] == "a"

    @pytest.mark.asyncio
    async def test_max_results_respected(self):
        stores = {tier: AsyncMock(spec=MemoryStore) for tier in MemoryTier}
        stores[MemoryTier.SEMANTIC].search = AsyncMock(return_value=[
            {"key": str(i), "value": i, "_relevance": float(i) / 20, "_recency": 0.5}
            for i in range(20)
        ])
        for tier in MemoryTier:
            if tier != MemoryTier.SEMANTIC:
                stores[tier].search = AsyncMock(return_value=[])
        router = MemoryRouter(stores)
        results = await router.search(MemoryQuery("q", intent="fact", max_results=5))
        assert len(results) == 5


# ── MemoryRouter write + promote ─────────────────────────────────────────────── #

class TestMemoryRouterWriteAndPromote:
    @pytest.mark.asyncio
    async def test_write_and_read_via_working_store(self):
        router = make_in_memory_router()
        await router.write(MemoryTier.WORKING, "session:active", {"turn": 1}, gaian_id="luna")
        store = router._stores[MemoryTier.WORKING]
        val = await store.read("session:active", "luna")
        assert val == {"turn": 1}

    @pytest.mark.asyncio
    async def test_promote_short_term_to_episodic(self):
        router = make_in_memory_router()
        await router.write(MemoryTier.SHORT_TERM, "session:2026-06-02", {"summary": "shadow session"}, gaian_id="luna")
        promoted = await router.promote("session:2026-06-02", MemoryTier.SHORT_TERM, MemoryTier.EPISODIC, gaian_id="luna")
        assert promoted is True
        val = await router._stores[MemoryTier.EPISODIC].read("session:2026-06-02", "luna")
        assert val == {"summary": "shadow session"}

    @pytest.mark.asyncio
    async def test_promote_returns_false_when_key_missing(self):
        router = make_in_memory_router()
        result = await router.promote("nonexistent", MemoryTier.SHORT_TERM, MemoryTier.EPISODIC, gaian_id="luna")
        assert result is False

    @pytest.mark.asyncio
    async def test_evict_all_expired_returns_counts(self):
        router = make_in_memory_router()
        await router.write(MemoryTier.WORKING, "k1", "v1", gaian_id="luna")
        counts = await router.evict_all_expired()
        assert isinstance(counts, dict)
        assert set(counts.keys()) == {t.name for t in MemoryTier}


# ── Working tier ────────────────────────────────────────────────────────────── #

class TestWorkingMemoryStore:
    @pytest.mark.asyncio
    async def test_write_and_read(self):
        store = WorkingMemoryStore()
        await store.write("k", {"data": 42}, gaian_id="luna")
        assert await store.read("k", "luna") == {"data": 42}

    @pytest.mark.asyncio
    async def test_read_missing_returns_none(self):
        assert await WorkingMemoryStore().read("missing") is None

    @pytest.mark.asyncio
    async def test_evict_flushes_all(self):
        store = WorkingMemoryStore()
        await store.write("a", 1)
        await store.write("b", 2)
        count = await store.evict_expired()
        assert count == 2
        assert len(store) == 0

    @pytest.mark.asyncio
    async def test_evict_for_gaian(self):
        store = WorkingMemoryStore()
        await store.write("k1", "val", gaian_id="luna")
        await store.write("k2", "val", gaian_id="sol")
        removed = await store.evict_for_gaian("luna")
        assert removed == 1
        assert await store.read("k1", "luna") is None
        assert await store.read("k2", "sol") == "val"


# ── Short-term tier ─────────────────────────────────────────────────────────── #

class TestShortTermMemoryStore:
    @pytest.mark.asyncio
    async def test_write_read_in_memory(self):
        store = ShortTermMemoryStore(db_path=":memory:")
        await store.write("session:1", {"turns": 3}, gaian_id="luna")
        val = await store.read("session:1", "luna")
        assert val == {"turns": 3}

    @pytest.mark.asyncio
    async def test_expired_entry_returns_none(self):
        store = ShortTermMemoryStore(db_path=":memory:")
        await store.write("expired", "data", gaian_id="luna", ttl_hours=0.000001)
        await asyncio.sleep(0.01)  # let TTL pass
        val = await store.read("expired", "luna")
        assert val is None

    @pytest.mark.asyncio
    async def test_evict_expired(self):
        store = ShortTermMemoryStore(db_path=":memory:")
        await store.write("old", "data", ttl_hours=0.000001)
        await asyncio.sleep(0.01)
        count = await store.evict_expired()
        assert count >= 1


# ── Episodic tier ────────────────────────────────────────────────────────────── #

class TestEpisodicMemoryStore:
    @pytest.mark.asyncio
    async def test_write_read_with_tags(self):
        store = EpisodicMemoryStore()
        await store.write("shadow-session-01", {"type": "ceremony"}, gaian_id="luna", tags=["shadow-work", "ceremony"])
        val = await store.read("shadow-session-01", "luna")
        assert val == {"type": "ceremony"}

    @pytest.mark.asyncio
    async def test_expired_entry_returns_none(self):
        store = EpisodicMemoryStore()
        await store.write("temp", "data", gaian_id="luna", ttl_hours=0.000001)
        await asyncio.sleep(0.01)
        assert await store.read("temp", "luna") is None

    @pytest.mark.asyncio
    async def test_evict_expired(self):
        store = EpisodicMemoryStore()
        await store.write("stale", "x", gaian_id="luna", ttl_hours=0.000001)
        await asyncio.sleep(0.01)
        count = await store.evict_expired()
        assert count >= 1


# ── Semantic tier ─────────────────────────────────────────────────────────────── #

class TestSemanticMemoryStore:
    @pytest.mark.asyncio
    async def test_write_read_permanent(self):
        store = SemanticMemoryStore()
        await store.write("canon:C32", {"title": "Synergy Doctrine"}, canon_refs=["C32"], source="canon_loader")
        val = await store.read("canon:C32")
        assert val == {"title": "Synergy Doctrine"}

    @pytest.mark.asyncio
    async def test_evict_returns_zero(self):
        store = SemanticMemoryStore()
        assert await store.evict_expired() == 0

    @pytest.mark.asyncio
    async def test_search_finds_by_text(self):
        store = SemanticMemoryStore()
        await store.write("canon:C34", "Presence doctrine", tags=["presence"])
        results = await store.search(MemoryQuery("presence", intent="fact"))
        assert any(r["key"] == "canon:C34" for r in results)


# ── Long-term tier ────────────────────────────────────────────────────────────── #

class TestLongTermMemoryStore:
    @pytest.mark.asyncio
    async def test_write_read(self):
        store = LongTermMemoryStore()
        await store.write("identity:core", {"personality": "liminal"}, gaian_id="luna", arc_type="identity")
        val = await store.read("identity:core", "luna")
        assert val == {"personality": "liminal"}

    @pytest.mark.asyncio
    async def test_evict_returns_zero(self):
        assert await LongTermMemoryStore().evict_expired() == 0

    @pytest.mark.asyncio
    async def test_gaian_scoping(self):
        store = LongTermMemoryStore()
        await store.write("arc:shadow", "luna_data", gaian_id="luna")
        await store.write("arc:shadow", "sol_data",  gaian_id="sol")
        assert await store.read("arc:shadow", "luna") == "luna_data"
        assert await store.read("arc:shadow", "sol")  == "sol_data"


# ── build_default_router ──────────────────────────────────────────────────────── #

class TestBuildDefaultRouter:
    def test_all_five_tiers_registered(self):
        router = build_default_router()
        assert set(router.registered_tiers()) == set(MemoryTier)

    def test_custom_semantic_store_injected(self):
        custom = SemanticMemoryStore()
        router = build_default_router(semantic_store=custom)
        assert router._stores[MemoryTier.SEMANTIC] is custom

    def test_custom_long_term_store_injected(self):
        custom = LongTermMemoryStore()
        router = build_default_router(long_term_store=custom)
        assert router._stores[MemoryTier.LONG_TERM] is custom
