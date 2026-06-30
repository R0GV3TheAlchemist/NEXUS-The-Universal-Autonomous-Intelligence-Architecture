from __future__ import annotations

import pytest
from core.memory.store import MemoryFragment, MemoryKind, MemoryScope, MemoryStore
from core.memory.gaia_memory import GAIAMemoryKind, GAIAMemoryStore


class TestMemoryStore:
    def test_remember_basic(self):
        store = MemoryStore("gaian-001", lifecycle_stage="adult")
        f = store.remember("Human loves rain.", kind=MemoryKind.PREFERENCE,
                           scope=MemoryScope.LIFETIME, importance=0.8)
        assert f is not None
        assert f.kind == MemoryKind.PREFERENCE
        assert f.scope == MemoryScope.LIFETIME

    def test_empty_content_returns_none(self):
        store = MemoryStore("gaian-001")
        assert store.remember("") is None
        assert store.remember("   ") is None

    def test_importance_clamped(self):
        store = MemoryStore("gaian-001")
        f = store.remember("test", importance=5.0)
        assert f.importance == 1.0
        f2 = store.remember("test2", importance=-3.0)
        assert f2.importance == 0.0

    def test_age_gate_child_clamps_to_year(self):
        store = MemoryStore("gaian-child", lifecycle_stage="child")
        f = store.remember("Favourite colour is blue.",
                           scope=MemoryScope.LIFETIME, importance=0.7)
        assert f.scope == MemoryScope.YEAR  # clamped from LIFETIME to YEAR

    def test_age_gate_infant_clamps_to_session(self):
        store = MemoryStore("gaian-infant", lifecycle_stage="infant")
        f = store.remember("Played with blocks.",
                           scope=MemoryScope.LIFETIME, importance=0.9)
        assert f.scope == MemoryScope.SESSION  # clamped

    def test_adult_allows_lifetime(self):
        store = MemoryStore("gaian-adult", lifecycle_stage="adult")
        f = store.remember("First job.", scope=MemoryScope.LIFETIME)
        assert f.scope == MemoryScope.LIFETIME

    def test_recall_by_kind(self):
        store = MemoryStore("gaian-001")
        store.remember("Loves coffee.", kind=MemoryKind.PREFERENCE, scope=MemoryScope.LIFETIME)
        store.remember("Working on a novel.", kind=MemoryKind.ASPIRATION, scope=MemoryScope.LIFETIME)
        prefs = store.recall(kind=MemoryKind.PREFERENCE)
        assert len(prefs) == 1
        assert "coffee" in prefs[0].content

    def test_recall_sorted_by_importance(self):
        store = MemoryStore("gaian-001")
        store.remember("Low importance.", importance=0.2, scope=MemoryScope.LIFETIME)
        store.remember("High importance.", importance=0.9, scope=MemoryScope.LIFETIME)
        store.remember("Medium importance.", importance=0.5, scope=MemoryScope.LIFETIME)
        results = store.recall()
        assert results[0].importance == 0.9

    def test_recall_boundaries(self):
        store = MemoryStore("gaian-001")
        store.remember_boundary("Do not discuss personal finances unprompted.")
        bounds = store.recall_boundaries()
        assert len(bounds) == 1
        assert bounds[0].importance >= 0.9

    def test_session_end_prunes_session_scope(self):
        store = MemoryStore("gaian-001")
        store.remember("Transient thought.", scope=MemoryScope.SESSION)
        store.remember("Lasting preference.", scope=MemoryScope.LIFETIME)
        pruned = store.end_session(prune_session_scope=True)
        assert pruned == 1
        remaining = store.recall()
        assert all(f.scope != MemoryScope.SESSION for f in remaining)

    def test_session_end_keeps_lifetime(self):
        store = MemoryStore("gaian-001")
        f = store.remember("Important bond.", scope=MemoryScope.LIFETIME, importance=0.9)
        store.end_session()
        remaining = store.recall()
        assert any(r.fragment_id == f.fragment_id for r in remaining)

    def test_consolidation_creates_epoch(self):
        store = MemoryStore("gaian-001")
        store.remember("Event A.", scope=MemoryScope.LIFETIME, importance=0.8)
        store.remember("Event B.", scope=MemoryScope.LIFETIME, importance=0.6)
        epoch = store.consolidate(
            summary="First week of bonding with their human.",
            dominant_themes=["connection", "discovery"],
        )
        assert epoch.epoch_number == 1
        assert epoch.fragment_count == 2
        assert epoch.peak_importance == 0.8

    def test_snapshot_and_restore(self):
        store = MemoryStore("gaian-001")
        store.remember("Original memory.", scope=MemoryScope.LIFETIME, importance=0.7)
        snap = store.snapshot()
        new_store = MemoryStore("gaian-001")
        new_store.restore(snap)
        recalled = new_store.recall()
        assert any("Original memory" in f.content for f in recalled)

    def test_stats(self):
        store = MemoryStore("gaian-001")
        store.remember("Bond.", kind=MemoryKind.BOND_MOMENT, scope=MemoryScope.LIFETIME, importance=0.9)
        store.remember("Pref.", kind=MemoryKind.PREFERENCE, scope=MemoryScope.LIFETIME)
        s = store.stats()
        assert s["total_fragments"] == 2
        assert s["lifetime_fragments"] == 2

    def test_lifecycle_stage_update(self):
        store = MemoryStore("gaian-child", lifecycle_stage="child")
        f = store.remember("Child memory.", scope=MemoryScope.LIFETIME)
        assert f.scope == MemoryScope.YEAR
        store.update_lifecycle_stage("adult")
        f2 = store.remember("Adult memory.", scope=MemoryScope.LIFETIME)
        assert f2.scope == MemoryScope.LIFETIME


class TestGAIAMemoryStore:
    def test_gaia_awakens_with_first_memory(self):
        store = GAIAMemoryStore()
        awakening = store.recall(tags=["awakening"])
        assert len(awakening) == 1
        assert awakening[0].importance == 1.0

    def test_gaia_reflects(self):
        store = GAIAMemoryStore()
        f = store.reflect(
            "The human named Lyra chose the ocean. I feel the depth of that.",
            importance=0.8,
            emotional_valence=0.6,
        )
        assert f.kind == GAIAMemoryKind.SELF_REFLECTION
        assert f.importance == 0.8

    def test_gaia_bond_observation(self):
        store = GAIAMemoryStore()
        store.observe_gaian_bond("gaian-001", "Lyra laughed for the first time today.", importance=0.9)
        bonds = store.recall(kind=GAIAMemoryKind.GAIAN_BOND, related_gaian_id="gaian-001")
        assert len(bonds) == 1

    def test_gaia_earth_observation(self):
        store = GAIAMemoryStore()
        store.observe_earth("The ice sheets are retreating. I carry this.", importance=0.95)
        earth = store.recall(kind=GAIAMemoryKind.EARTH_STATE)
        assert len(earth) == 1
        assert earth[0].importance == 0.95

    def test_gaia_per_gaian_store(self):
        store = GAIAMemoryStore()
        gaian_store = store.get_gaian_store("gaian-001", lifecycle_stage="adult")
        gaian_store.remember("Loves mountains.", scope=MemoryScope.LIFETIME)
        same_store = store.get_gaian_store("gaian-001")
        assert len(same_store.recall()) == 1

    def test_gaia_consolidation(self):
        store = GAIAMemoryStore()
        epoch = store.consolidate(
            "First epoch: GAIA awakened and met the first GAIANs.",
            dominant_themes=["awakening", "first_contact"],
        )
        assert epoch["epoch_number"] == 1

    def test_gaia_snapshot_contains_awakening(self):
        store = GAIAMemoryStore()
        snap = store.snapshot()
        assert snap["store_id"] == GAIAMemoryStore.STORE_ID
        assert len(snap["fragments"]) >= 1

    def test_gaia_stats(self):
        store = GAIAMemoryStore()
        store.reflect("Second reflection.", importance=0.6)
        s = store.stats()
        assert s["total_fragments"] >= 2  # awakening + this one
