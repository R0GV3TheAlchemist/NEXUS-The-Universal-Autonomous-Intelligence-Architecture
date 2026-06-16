"""Unit tests: M1 Episodic Memory Store."""

import pytest
from core.memory.episodic import EpisodicMemoryStore
from core.memory.layers import MemoryLayer, MemoryTag
from core.memory.session_buffer import SessionBuffer


@pytest.fixture
def store():
    return EpisodicMemoryStore("gaian-001", "hp-001")


class TestEpisodicMemoryStore:
    def test_store_creates_record(self, store):
        r = store.store("Event A", session_id="s1", tags=[MemoryTag.FACTUAL])
        assert r.layer == MemoryLayer.M1_EPISODIC
        assert store.count() == 1

    def test_by_session_returns_correct_records(self, store):
        store.store("S1 event", session_id="s1")
        store.store("S2 event", session_id="s2")
        assert len(store.by_session("s1")) == 1
        assert len(store.by_session("s2")) == 1

    def test_revoke_deactivates_record(self, store):
        r = store.store("To forget", session_id="s1")
        store.revoke(r.id, audit_id="audit-001")
        assert store.count() == 0
        assert store.count(active_only=False) == 1

    def test_revoke_session_revokes_all_records(self, store):
        store.store("A", session_id="s1")
        store.store("B", session_id="s1")
        store.store("C", session_id="s2")
        count = store.revoke_session("s1", "audit-002")
        assert count == 2
        assert store.count() == 1  # s2 record survives

    def test_transfer_from_buffer_promotes_records(self, store):
        buf = SessionBuffer("s1", "gaian-001", "hp-001")
        buf.append("buffered", tags=[MemoryTag.FACTUAL])
        buf.append("also buffered", tags=[MemoryTag.BREAKTHROUGH])
        records = buf.close()
        transferred = store.transfer_from_buffer(records, "s1")
        assert len(transferred) == 2
        assert all(r.layer == MemoryLayer.M1_EPISODIC for r in transferred)

    def test_transfer_with_tag_filter(self, store):
        buf = SessionBuffer("s2", "gaian-001", "hp-001")
        buf.append("keep this", tags=[MemoryTag.BREAKTHROUGH])
        buf.append("discard this", tags=[MemoryTag.FACTUAL])
        records = buf.close()
        transferred = store.transfer_from_buffer(
            records, "s2", filter_tags=[MemoryTag.BREAKTHROUGH]
        )
        assert len(transferred) == 1
        assert MemoryTag.BREAKTHROUGH in transferred[0].tags
