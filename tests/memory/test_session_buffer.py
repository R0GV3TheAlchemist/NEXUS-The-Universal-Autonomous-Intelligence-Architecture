"""Unit tests: M0 Session Buffer."""

import pytest
from core.memory.session_buffer import SessionBuffer
from core.memory.layers import MemoryLayer, MemoryTag


@pytest.fixture
def buf():
    return SessionBuffer("session-001", "gaian-001", "hp-001")


class TestSessionBuffer:
    def test_append_creates_record(self, buf):
        r = buf.append("First thought", tags=[MemoryTag.FACTUAL])
        assert r.layer == MemoryLayer.M0_SESSION
        assert MemoryTag.FACTUAL in r.tags

    def test_count_reflects_active_records(self, buf):
        buf.append("A")
        buf.append("B")
        assert buf.count() == 2

    def test_recent_returns_last_n(self, buf):
        for i in range(5):
            buf.append(f"record {i}")
        recent = buf.recent(3)
        assert len(recent) == 3
        assert recent[-1].content == "record 4"

    def test_close_returns_all_records(self, buf):
        buf.append("X")
        buf.append("Y")
        records = buf.close()
        assert len(records) == 2
        assert buf.is_closed

    def test_cannot_append_after_close(self, buf):
        buf.close()
        with pytest.raises(RuntimeError, match="closed"):
            buf.append("Too late")

    def test_clear_empties_buffer(self, buf):
        buf.append("data")
        buf.close()
        buf.clear()
        assert buf.count() == 0

    def test_by_tag_filters_correctly(self, buf):
        buf.append("breakthrough!", tags=[MemoryTag.BREAKTHROUGH])
        buf.append("just a fact", tags=[MemoryTag.FACTUAL])
        breakthroughs = buf.by_tag(MemoryTag.BREAKTHROUGH)
        assert len(breakthroughs) == 1
