"""pytest suite for the Agent Telemetry Hub (Issue #188).

Coverage:
  - TelemetryEvent creation and serialization
  - TelemetryStore append-only insert and read operations
  - Skill health computation
  - DQ history retrieval
  - TelemetryCollector emit pipeline
  - Orchestration Efficiency metric computation
  - SSE subscriber broadcast
  - Emit-point factory functions
  - User export and deletion
"""

from __future__ import annotations

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src_python.telemetry.models import TelemetryEvent, OrchestrationEfficiency, SkillHealthReport
from src_python.telemetry.store import TelemetryStore
from src_python.telemetry.collector import TelemetryCollector
from src_python.telemetry.emit_points import (
    emit_job_started,
    emit_job_completed,
    emit_job_failed,
    emit_sandbox_event,
    emit_healing_event,
    emit_action_gate,
    emit_biometric_change,
    emit_planetary_change,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path: Path) -> TelemetryStore:
    return TelemetryStore(tmp_path / "test_telemetry.db")


@pytest.fixture
def collector(tmp_path: Path) -> TelemetryCollector:
    return TelemetryCollector(tmp_path / "test_collector.db")


# ---------------------------------------------------------------------------
# TelemetryEvent — model tests
# ---------------------------------------------------------------------------

class TestTelemetryEventModel:
    def test_default_id_generated(self):
        e = TelemetryEvent()
        assert e.id and len(e.id) == 36  # UUID4

    def test_to_dict_keys(self):
        e = TelemetryEvent(session_id="s1", source="sandbox", event_type="job_started")
        d = e.to_dict()
        for key in ("id", "timestamp", "session_id", "source", "event_type", "degraded"):
            assert key in d

    def test_canon_refs_serialized_as_csv(self):
        e = TelemetryEvent(canon_refs=["C01", "C30"])
        assert e.to_dict()["canon_refs"] == "C01,C30"

    def test_tags_serialized_as_csv(self):
        e = TelemetryEvent(tags=["engines:3", "deep_work"])
        assert e.to_dict()["tags"] == "engines:3,deep_work"

    def test_empty_canon_refs(self):
        e = TelemetryEvent()
        assert e.to_dict()["canon_refs"] == ""


# ---------------------------------------------------------------------------
# OrchestrationEfficiency — computation
# ---------------------------------------------------------------------------

class TestOrchestrationEfficiency:
    def test_oe_computation_normal(self):
        oe = OrchestrationEfficiency(
            window="24h",
            successful_tasks=10,
            avg_total_latency_s=0.5,
            avg_engine_count=2.0,
            avg_dq_score=0.9,
        )
        score = oe.compute_oe()
        expected = (10 * 0.9) / (0.5 * 2.0)  # = 9.0
        assert abs(score - expected) < 0.001
        assert oe.oe_score == score

    def test_oe_zero_on_zero_latency(self):
        oe = OrchestrationEfficiency(avg_total_latency_s=0.0, avg_engine_count=2.0)
        assert oe.compute_oe() == 0.0

    def test_oe_zero_on_zero_engines(self):
        oe = OrchestrationEfficiency(avg_total_latency_s=1.0, avg_engine_count=0.0)
        assert oe.compute_oe() == 0.0


# ---------------------------------------------------------------------------
# TelemetryStore — SQLite operations
# ---------------------------------------------------------------------------

class TestTelemetryStore:
    def test_insert_and_retrieve(self, tmp_db: TelemetryStore):
        e = TelemetryEvent(session_id="abc", source="sandbox", event_type="job_started")
        tmp_db.insert(e)
        trace = tmp_db.get_session_trace("abc")
        assert len(trace) == 1
        assert trace[0].id == e.id

    def test_append_only_no_duplicate(self, tmp_db: TelemetryStore):
        e = TelemetryEvent(session_id="abc", source="sandbox", event_type="job_started")
        tmp_db.insert(e)
        tmp_db.insert(e)  # duplicate — should be silently ignored (INSERT OR IGNORE)
        assert len(tmp_db.get_session_trace("abc")) == 1

    def test_multiple_events_ordered(self, tmp_db: TelemetryStore):
        for i in range(5):
            tmp_db.insert(TelemetryEvent(session_id="s", source="skill", event_type=f"e{i}"))
        trace = tmp_db.get_session_trace("s")
        assert len(trace) == 5

    def test_skill_health_no_events(self, tmp_db: TelemetryStore):
        report = tmp_db.get_skill_health("unknown_skill")
        assert report.total_events == 0
        assert report.error_rate == 0.0

    def test_skill_health_with_failures(self, tmp_db: TelemetryStore):
        for _ in range(3):
            tmp_db.insert(TelemetryEvent(
                session_id="s", source="synergy_orchestrator",
                event_type="job_completed", skill_id="research_desk", duration_ms=200
            ))
        tmp_db.insert(TelemetryEvent(
            session_id="s", source="synergy_orchestrator",
            event_type="job_failed", skill_id="research_desk", duration_ms=100
        ))
        report = tmp_db.get_skill_health("research_desk", window_minutes=1440)
        assert report.total_events == 4
        assert report.error_count == 1
        assert abs(report.error_rate - 0.25) < 0.01
        assert report.avg_duration_ms == 175.0

    def test_dq_history_returns_scored_events(self, tmp_db: TelemetryStore):
        tmp_db.insert(TelemetryEvent(session_id="s", source="synergy_orchestrator", event_type="job_completed", dq_score=0.91))
        tmp_db.insert(TelemetryEvent(session_id="s", source="synergy_orchestrator", event_type="job_started"))  # no DQ
        history = tmp_db.get_dq_history(limit=10)
        assert len(history) == 1
        assert history[0]["dq_score"] == 0.91

    def test_delete_range(self, tmp_db: TelemetryStore):
        past = TelemetryEvent(session_id="s", source="skill", event_type="job_started")
        past.timestamp = datetime(2025, 1, 1, 0, 0, 0)
        recent = TelemetryEvent(session_id="s", source="skill", event_type="job_completed")
        tmp_db.insert(past)
        tmp_db.insert(recent)
        deleted = tmp_db.delete_range(
            since=datetime(2024, 12, 1),
            until=datetime(2025, 6, 1),
        )
        assert deleted == 1
        trace = tmp_db.get_session_trace("s")
        assert len(trace) == 1
        assert trace[0].event_type == "job_completed"

    def test_export_json(self, tmp_db: TelemetryStore):
        import json
        tmp_db.insert(TelemetryEvent(session_id="exp", source="skill", event_type="job_started"))
        result = tmp_db.export_session_json("exp")
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1


# ---------------------------------------------------------------------------
# TelemetryCollector — async pipeline
# ---------------------------------------------------------------------------

class TestTelemetryCollector:
    def test_emit_persists_event(self, collector: TelemetryCollector):
        e = TelemetryEvent(session_id="col", source="sandbox", event_type="job_started")
        asyncio.get_event_loop().run_until_complete(collector.emit(e))
        trace = asyncio.get_event_loop().run_until_complete(collector.get_session_trace("col"))
        assert len(trace) == 1

    def test_subscribe_receives_event(self, collector: TelemetryCollector):
        q = collector.subscribe()
        e = TelemetryEvent(session_id="sub", source="skill", event_type="job_started")

        async def run():
            await collector.emit(e)
            received = await asyncio.wait_for(q.get(), timeout=1.0)
            return received

        received = asyncio.get_event_loop().run_until_complete(run())
        assert received.id == e.id

    def test_unsubscribe_removes_queue(self, collector: TelemetryCollector):
        q = collector.subscribe()
        assert q in collector._subscribers
        collector.unsubscribe(q)
        assert q not in collector._subscribers

    def test_high_value_event_flagged(self, collector: TelemetryCollector):
        """RED risk and degraded events are flagged for Crystal indexing."""
        red = TelemetryEvent(risk_tier="RED")
        degraded = TelemetryEvent(degraded=True)
        normal = TelemetryEvent()
        assert collector._is_high_value(red)
        assert collector._is_high_value(degraded)
        assert not collector._is_high_value(normal)


# ---------------------------------------------------------------------------
# Emit-point factories
# ---------------------------------------------------------------------------

class TestEmitPoints:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_emit_job_started(self, collector: TelemetryCollector):
        self._run(emit_job_started(collector, "s1", skill_id="research_desk", intent_class="research"))
        trace = self._run(collector.get_session_trace("s1"))
        assert any(e.event_type == "job_started" and e.source == "synergy_orchestrator" for e in trace)

    def test_emit_job_completed_with_dq(self, collector: TelemetryCollector):
        self._run(emit_job_completed(collector, "s2", skill_id="research_desk", duration_ms=420, dq_score=0.91))
        trace = self._run(collector.get_session_trace("s2"))
        completed = next(e for e in trace if e.event_type == "job_completed")
        assert completed.dq_score == 0.91
        assert completed.duration_ms == 420

    def test_emit_job_failed(self, collector: TelemetryCollector):
        self._run(emit_job_failed(collector, "s3", skill_id="crystal_graphrag", duration_ms=50, error_summary="TimeoutError"))
        trace = self._run(collector.get_session_trace("s3"))
        assert any(e.event_type == "job_failed" for e in trace)

    def test_emit_sandbox_violation(self, collector: TelemetryCollector):
        self._run(emit_sandbox_event(collector, "s4", event_type="sandbox_violation", risk_tier="RED"))
        trace = self._run(collector.get_session_trace("s4"))
        ev = next(e for e in trace if e.source == "sandbox")
        assert ev.risk_tier == "RED"

    def test_emit_healing_fallback(self, collector: TelemetryCollector):
        self._run(emit_healing_event(collector, "s5", skill_id="planetary_hub", fallback_mode="cached", attempt_number=3))
        trace = self._run(collector.get_session_trace("s5"))
        ev = next(e for e in trace if e.source == "healing")
        assert ev.fallback_mode == "cached"
        assert ev.degraded is True

    def test_emit_action_gate_approved(self, collector: TelemetryCollector):
        self._run(emit_action_gate(collector, "s6", skill_id="shell", risk_tier="YELLOW", user_approved=True))
        trace = self._run(collector.get_session_trace("s6"))
        ev = next(e for e in trace if e.source == "action_gate")
        assert ev.risk_tier == "YELLOW"
        assert ev.output_summary == "approved"

    def test_emit_biometric_change(self, collector: TelemetryCollector):
        self._run(emit_biometric_change(collector, "s7", coherence_label="stressed"))
        trace = self._run(collector.get_session_trace("s7"))
        ev = next(e for e in trace if e.source == "biometric")
        assert ev.biometric_context == "stressed"

    def test_emit_planetary_change(self, collector: TelemetryCollector):
        self._run(emit_planetary_change(collector, "s8", planetary_label="kp_storm"))
        trace = self._run(collector.get_session_trace("s8"))
        ev = next(e for e in trace if e.source == "planetary")
        assert ev.planetary_context == "kp_storm"
