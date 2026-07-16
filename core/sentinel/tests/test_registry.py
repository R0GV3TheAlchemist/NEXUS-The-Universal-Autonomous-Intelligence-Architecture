"""
core/sentinel/tests/test_registry.py
=====================================
Full test coverage for AlertRegistry and AlertRecord.

Covers:
  - add() stores records and rejects duplicates
  - get() retrieves by ID
  - get_active() filters by level and resolution
  - get_all() returns everything in insertion order
  - mark_resolved() / mark_interrupted() / mark_escalated() state transitions
  - unresolved_count() accuracy
  - count_by_level() accuracy
  - clear_resolved() removes only resolved, returns correct count
  - to_dict() serialises completely

© 2024-2026 R0GV3 The Alchemist — GAIA Project. All rights reserved.
AGPL-3.0 Licensed. Unauthorised derivative works are prohibited.
"""

import pytest

from core.sentinel.constants import AlertLevel, ALERT_LEVEL_LABEL, ALERT_LEVEL_HEX
from core.sentinel.registry import AlertRecord, AlertRegistry


def make_record(
    alert_id: str = "test-001",
    source: str = "test.module",
    level: AlertLevel = AlertLevel.WARNING,
    message: str = "test message",
) -> AlertRecord:
    return AlertRecord(
        alert_id=alert_id,
        source=source,
        level=level,
        label=ALERT_LEVEL_LABEL[level],
        hex_colour=ALERT_LEVEL_HEX[level],
        message=message,
        payload={},
        timestamp="2026-07-16T00:00:00Z",
    )


@pytest.fixture()
def registry() -> AlertRegistry:
    return AlertRegistry()


# ---------------------------------------------------------------------------
# add()
# ---------------------------------------------------------------------------

class TestAdd:
    def test_add_stores_record(self, registry):
        rec = make_record()
        registry.add(rec)
        assert registry.get("test-001") is rec

    def test_add_duplicate_raises(self, registry):
        rec = make_record()
        registry.add(rec)
        with pytest.raises(ValueError, match="Duplicate alert_id"):
            registry.add(rec)

    def test_len_reflects_add(self, registry):
        registry.add(make_record(alert_id="a"))
        registry.add(make_record(alert_id="b"))
        assert len(registry) == 2


# ---------------------------------------------------------------------------
# get() / get_all()
# ---------------------------------------------------------------------------

class TestGet:
    def test_get_returns_none_for_missing(self, registry):
        assert registry.get("nonexistent") is None

    def test_get_all_insertion_order(self, registry):
        ids = ["c", "a", "b"]
        for i in ids:
            registry.add(make_record(alert_id=i))
        returned_ids = [r.alert_id for r in registry.get_all()]
        assert returned_ids == ids


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

class TestStateTransitions:
    def test_mark_resolved(self, registry):
        rec = make_record()
        registry.add(rec)
        assert registry.mark_resolved("test-001") is True
        assert registry.get("test-001").resolved is True

    def test_mark_interrupted(self, registry):
        rec = make_record()
        registry.add(rec)
        assert registry.mark_interrupted("test-001") is True
        assert registry.get("test-001").interrupted is True

    def test_mark_escalated(self, registry):
        rec = make_record()
        registry.add(rec)
        assert registry.mark_escalated("test-001") is True
        assert registry.get("test-001").escalated is True

    def test_mark_missing_returns_false(self, registry):
        assert registry.mark_resolved("ghost") is False
        assert registry.mark_interrupted("ghost") is False
        assert registry.mark_escalated("ghost") is False


# ---------------------------------------------------------------------------
# get_active()
# ---------------------------------------------------------------------------

class TestGetActive:
    def test_unresolved_returned(self, registry):
        rec = make_record(level=AlertLevel.WARNING)
        registry.add(rec)
        active = registry.get_active()
        assert rec in active

    def test_resolved_excluded(self, registry):
        rec = make_record()
        registry.add(rec)
        registry.mark_resolved(rec.alert_id)
        assert registry.get_active() == []

    def test_min_level_filter(self, registry):
        low  = make_record(alert_id="low",  level=AlertLevel.ADVISORY)
        high = make_record(alert_id="high", level=AlertLevel.CRITICAL)
        registry.add(low)
        registry.add(high)
        result = registry.get_active(min_level=AlertLevel.CRITICAL)
        assert high in result
        assert low not in result


# ---------------------------------------------------------------------------
# unresolved_count() / count_by_level()
# ---------------------------------------------------------------------------

class TestCounts:
    def test_unresolved_count_initial(self, registry):
        assert registry.unresolved_count() == 0

    def test_unresolved_count_after_add(self, registry):
        registry.add(make_record(alert_id="x"))
        assert registry.unresolved_count() == 1

    def test_unresolved_count_after_resolve(self, registry):
        registry.add(make_record(alert_id="x"))
        registry.mark_resolved("x")
        assert registry.unresolved_count() == 0

    def test_count_by_level(self, registry):
        registry.add(make_record(alert_id="w1", level=AlertLevel.WARNING))
        registry.add(make_record(alert_id="w2", level=AlertLevel.WARNING))
        registry.add(make_record(alert_id="c1", level=AlertLevel.CRITICAL))
        assert registry.count_by_level(AlertLevel.WARNING) == 2
        assert registry.count_by_level(AlertLevel.CRITICAL) == 1
        assert registry.count_by_level(AlertLevel.EMERGENCY) == 0


# ---------------------------------------------------------------------------
# clear_resolved()
# ---------------------------------------------------------------------------

class TestClearResolved:
    def test_removes_only_resolved(self, registry):
        keep    = make_record(alert_id="keep",    level=AlertLevel.WARNING)
        discard = make_record(alert_id="discard", level=AlertLevel.ADVISORY)
        registry.add(keep)
        registry.add(discard)
        registry.mark_resolved("discard")
        count = registry.clear_resolved()
        assert count == 1
        assert registry.get("keep") is not None
        assert registry.get("discard") is None

    def test_clear_empty_registry_returns_zero(self, registry):
        assert registry.clear_resolved() == 0


# ---------------------------------------------------------------------------
# AlertRecord.to_dict()
# ---------------------------------------------------------------------------

class TestToDict:
    def test_all_keys_present(self):
        rec = make_record()
        d = rec.to_dict()
        expected_keys = {
            "alert_id", "source", "level", "label", "hex_colour",
            "message", "payload", "timestamp",
            "resolved", "interrupted", "escalated", "metadata",
        }
        assert set(d.keys()) == expected_keys

    def test_level_serialised_as_int(self):
        rec = make_record(level=AlertLevel.CRITICAL)
        assert rec.to_dict()["level"] == 4
