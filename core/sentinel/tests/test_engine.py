"""
core/sentinel/tests/test_engine.py
===================================
Full test coverage for SentinelEngine.

Covers:
  - emit() records every alert regardless of level
  - evaluate_alert() correctly classifies interrupt / escalation decisions
  - interrupt_check() honours INTERRUPT_THRESHOLD exactly
  - interrupt_check() NEVER returns True below CRITICAL (invariant)
  - escalate_to_constitutional() behaviour above and below threshold
  - Saturation elevation: WARNING floor when registry is saturated
  - connect_constitutional() wires a handler and receives its response
  - get_active_alerts() filters by level correctly
  - clear_resolved() removes only resolved records

© 2024-2026 R0GV3 The Alchemist — GAIA Project. All rights reserved.
AGPL-3.0 Licensed. Unauthorised derivative works are prohibited.
"""

import pytest

from core.sentinel.constants import (
    AlertLevel,
    INTERRUPT_THRESHOLD,
    CONSTITUTIONAL_ESCALATION_THRESHOLD,
    UNRESOLVEDATION_LIMIT,
)
from core.sentinel.engine import SentinelEngine
from core.sentinel.registry import AlertRecord


@pytest.fixture()
def engine() -> SentinelEngine:
    """Fresh engine for every test — no shared state."""
    return SentinelEngine()


# ---------------------------------------------------------------------------
# emit()
# ---------------------------------------------------------------------------

class TestEmit:
    def test_returns_alert_record(self, engine):
        rec = engine.emit("test.module", AlertLevel.ADVISORY, "hello")
        assert isinstance(rec, AlertRecord)

    def test_record_stored_in_registry(self, engine):
        rec = engine.emit("test.module", AlertLevel.CAUTION, "caution msg")
        assert engine._registry.get(rec.alert_id) is not None

    def test_all_five_levels_accepted(self, engine):
        for lvl in AlertLevel:
            rec = engine.emit("test", lvl, f"level {lvl}")
            assert rec.level == lvl

    def test_int_level_coerced(self, engine):
        rec = engine.emit("test", 3, "int level")
        assert rec.level == AlertLevel.WARNING

    def test_payload_stored(self, engine):
        rec = engine.emit("test", AlertLevel.WARNING, "msg", payload={"key": "val"})
        assert rec.payload["key"] == "val"

    def test_empty_payload_defaults_to_dict(self, engine):
        rec = engine.emit("test", AlertLevel.ADVISORY, "no payload")
        assert isinstance(rec.payload, dict)

    def test_saturation_elevation_floors_to_warning(self, engine):
        # Fill registry to saturation limit with resolved-flagged records
        for i in range(UNRESOLVEDATION_LIMIT):
            engine.emit("filler", AlertLevel.ADVISORY, f"filler {i}")
        # Next advisory should be elevated to WARNING
        rec = engine.emit("test", AlertLevel.ADVISORY, "post-saturation")
        assert rec.level >= AlertLevel.WARNING

    def test_saturation_does_not_affect_high_level_alerts(self, engine):
        for i in range(UNRESOLVEDATION_LIMIT):
            engine.emit("filler", AlertLevel.ADVISORY, f"filler {i}")
        rec = engine.emit("test", AlertLevel.EMERGENCY, "emergency")
        assert rec.level == AlertLevel.EMERGENCY


# ---------------------------------------------------------------------------
# evaluate_alert()
# ---------------------------------------------------------------------------

class TestEvaluateAlert:
    def test_advisory_no_interrupt_no_escalate(self, engine):
        rec = engine.emit("t", AlertLevel.ADVISORY, "adv")
        decision = engine.evaluate_alert(rec)
        assert decision["should_interrupt"] is False
        assert decision["should_escalate"] is False

    def test_caution_no_interrupt_no_escalate(self, engine):
        rec = engine.emit("t", AlertLevel.CAUTION, "caut")
        decision = engine.evaluate_alert(rec)
        assert decision["should_interrupt"] is False
        assert decision["should_escalate"] is False

    def test_warning_no_interrupt_no_escalate(self, engine):
        rec = engine.emit("t", AlertLevel.WARNING, "warn")
        decision = engine.evaluate_alert(rec)
        assert decision["should_interrupt"] is False
        assert decision["should_escalate"] is False

    def test_critical_triggers_interrupt(self, engine):
        rec = engine.emit("t", AlertLevel.CRITICAL, "crit")
        decision = engine.evaluate_alert(rec)
        assert decision["should_interrupt"] is True
        assert decision["should_escalate"] is False

    def test_emergency_triggers_interrupt_and_escalate(self, engine):
        rec = engine.emit("t", AlertLevel.EMERGENCY, "emerg")
        decision = engine.evaluate_alert(rec)
        assert decision["should_interrupt"] is True
        assert decision["should_escalate"] is True


# ---------------------------------------------------------------------------
# interrupt_check() — the invariant
# ---------------------------------------------------------------------------

class TestInterruptCheck:
    @pytest.mark.parametrize("level", [
        AlertLevel.ADVISORY,
        AlertLevel.CAUTION,
        AlertLevel.WARNING,
    ])
    def test_never_interrupts_below_critical(self, engine, level):
        """INVARIANT: interrupt_check() is NEVER True below CRITICAL."""
        rec = engine.emit("t", level, "below threshold")
        assert engine.interrupt_check(rec) is False

    @pytest.mark.parametrize("level", [
        AlertLevel.CRITICAL,
        AlertLevel.EMERGENCY,
    ])
    def test_always_interrupts_at_or_above_critical(self, engine, level):
        rec = engine.emit("t", level, "at or above threshold")
        assert engine.interrupt_check(rec) is True

    def test_interrupt_marks_record(self, engine):
        rec = engine.emit("t", AlertLevel.CRITICAL, "mark test")
        engine.interrupt_check(rec)
        stored = engine._registry.get(rec.alert_id)
        assert stored.interrupted is True

    def test_non_interrupt_does_not_mark_record(self, engine):
        rec = engine.emit("t", AlertLevel.ADVISORY, "no mark")
        engine.interrupt_check(rec)
        stored = engine._registry.get(rec.alert_id)
        assert stored.interrupted is False


# ---------------------------------------------------------------------------
# escalate_to_constitutional()
# ---------------------------------------------------------------------------

class TestEscalateToConstitutional:
    def test_below_threshold_returns_not_escalated(self, engine):
        rec = engine.emit("t", AlertLevel.CRITICAL, "not emergency")
        result = engine.escalate_to_constitutional(rec)
        assert result["escalated"] is False

    def test_emergency_returns_escalated_true(self, engine):
        rec = engine.emit("t", AlertLevel.EMERGENCY, "emergency")
        result = engine.escalate_to_constitutional(rec)
        assert result["escalated"] is True

    def test_pending_response_when_no_handler(self, engine):
        rec = engine.emit("t", AlertLevel.EMERGENCY, "emerg")
        result = engine.escalate_to_constitutional(rec)
        assert result["constitutional_response"] == "CONSTITUTIONAL_LAYER_PENDING"

    def test_marks_escalated_in_registry(self, engine):
        rec = engine.emit("t", AlertLevel.EMERGENCY, "emerg")
        engine.escalate_to_constitutional(rec)
        stored = engine._registry.get(rec.alert_id)
        assert stored.escalated is True

    def test_connected_handler_called(self, engine):
        def mock_handler(record, context):
            return "MOCK_VETO"
        engine.connect_constitutional(mock_handler)
        rec = engine.emit("t", AlertLevel.EMERGENCY, "emerg")
        result = engine.escalate_to_constitutional(rec, context={"reason": "test"})
        assert result["constitutional_response"] == "MOCK_VETO"
        assert result["escalated"] is True


# ---------------------------------------------------------------------------
# get_active_alerts() / clear_resolved()
# ---------------------------------------------------------------------------

class TestRegistryQueries:
    def test_get_active_returns_unresolved(self, engine):
        rec = engine.emit("t", AlertLevel.WARNING, "active")
        active = engine.get_active_alerts()
        assert any(r.alert_id == rec.alert_id for r in active)

    def test_resolved_not_in_active(self, engine):
        rec = engine.emit("t", AlertLevel.WARNING, "will resolve")
        engine._registry.mark_resolved(rec.alert_id)
        active = engine.get_active_alerts()
        assert all(r.alert_id != rec.alert_id for r in active)

    def test_min_level_filter(self, engine):
        engine.emit("t", AlertLevel.ADVISORY, "advisory")
        engine.emit("t", AlertLevel.CRITICAL, "critical")
        critical_plus = engine.get_active_alerts(min_level=AlertLevel.CRITICAL)
        assert all(r.level >= AlertLevel.CRITICAL for r in critical_plus)

    def test_clear_resolved_removes_only_resolved(self, engine):
        rec_active   = engine.emit("t", AlertLevel.WARNING, "keep")
        rec_resolved = engine.emit("t", AlertLevel.ADVISORY, "remove")
        engine._registry.mark_resolved(rec_resolved.alert_id)
        removed = engine.clear_resolved()
        assert removed == 1
        assert engine._registry.get(rec_active.alert_id) is not None
        assert engine._registry.get(rec_resolved.alert_id) is None
