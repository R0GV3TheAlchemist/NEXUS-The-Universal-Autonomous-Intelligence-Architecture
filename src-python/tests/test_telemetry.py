"""pytest suite for Issue #188 — Agent Telemetry Hub.

Covers:
- TelemetryEvent schema and to_dict/from_dict round-trip
- TelemetryCollector: emit, persist, query, export, delete (Canon C01)
- Auto risk-tier promotion for degraded + conflict events
- Glass Room subscriber broadcasting
- OrchestrationEfficiencyService: OE computation for all windows
- OE formula correctness
- Bottleneck intent detection
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
import pytest

from src_python.telemetry.telemetry_event import (
    TelemetryEvent, TelemetrySource, TrustTier, RiskTier
)
from src_python.telemetry.telemetry_collector import TelemetryCollector
from src_python.telemetry.orchestration_efficiency import (
    OrchestrationEfficiencyRecord,
    OrchestrationEfficiencyService,
    OEWindowDuration,
)


# ---------------------------------------------------------------------------
# TelemetryEvent
# ---------------------------------------------------------------------------

class TestTelemetryEvent:
    def test_default_risk_tier_is_green(self):
        e = TelemetryEvent()
        assert e.risk_tier == RiskTier.GREEN

    def test_to_dict_round_trip(self):
        e = TelemetryEvent(
            source=TelemetrySource.SELF_HEALING_ENGINE,
            event_type="fallback_used",
            degraded=True,
            skill_id="crystal_graphrag",
        )
        d = e.to_dict()
        assert d["source"] == "self_healing_engine"
        assert d["degraded"] is True
        assert d["skill_id"] == "crystal_graphrag"

    def test_from_dict_restores_fields(self):
        e = TelemetryEvent(event_type="test", session_id="abc123")
        d = e.to_dict()
        e2 = TelemetryEvent.from_dict(d)
        assert e2.event_type == "test"
        assert e2.session_id == "abc123"


# ---------------------------------------------------------------------------
# TelemetryCollector
# ---------------------------------------------------------------------------

@pytest.fixture
def collector(tmp_path):
    """Provide a TelemetryCollector backed by a temp SQLite DB."""
    c = TelemetryCollector(db_path=tmp_path / "test_events.db")
    asyncio.get_event_loop().run_until_complete(c.start())
    yield c
    asyncio.get_event_loop().run_until_complete(c.stop())


class TestTelemetryCollector:
    @pytest.mark.asyncio
    async def test_emit_and_query(self, collector):
        e = TelemetryEvent(event_type="test_event", session_id="s1", skill_id="soul_mirror")
        await collector.emit(e)
        results = collector.query(session_id="s1")
        assert len(results) == 1
        assert results[0]["skill_id"] == "soul_mirror"

    @pytest.mark.asyncio
    async def test_emit_dict(self, collector):
        await collector.emit({"event_type": "retry", "skill_id": "article_loader", "session_id": "s2"})
        results = collector.query(session_id="s2")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_degraded_event_auto_promoted_to_yellow(self, collector):
        e = TelemetryEvent(event_type="fallback_used", degraded=True)
        await collector.emit(e)
        results = collector.query(risk_tier="yellow")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_safety_conflict_promoted_to_red(self, collector):
        e = TelemetryEvent(
            event_type="conflict_resolved",
            conflict_type="SAFETY_ETHICAL_OVERRIDE",
            conflict_detected=True,
        )
        await collector.emit(e)
        results = collector.query(risk_tier="red")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_export_session(self, collector):
        for i in range(3):
            await collector.emit(TelemetryEvent(event_type="op", session_id="sess_export"))
        exported = collector.export_session("sess_export")
        assert len(exported) == 3

    @pytest.mark.asyncio
    async def test_delete_session_erasure(self, collector):
        await collector.emit(TelemetryEvent(event_type="op", session_id="sess_delete"))
        deleted = collector.delete_session("sess_delete")
        assert deleted == 1
        assert collector.query(session_id="sess_delete") == []

    @pytest.mark.asyncio
    async def test_subscriber_receives_events(self, collector):
        received = []
        collector.subscribe(received.append)
        e = TelemetryEvent(event_type="broadcast_test")
        await collector.emit(e)
        assert len(received) == 1
        assert received[0].event_type == "broadcast_test"

    @pytest.mark.asyncio
    async def test_emit_never_raises_on_bad_event(self, collector):
        # Should never raise even with malformed input
        await collector.emit({"__bad__": True})


# ---------------------------------------------------------------------------
# OrchestrationEfficiencyService
# ---------------------------------------------------------------------------

class TestOrchestrationEfficiency:
    def _service_with_records(
        self,
        n: int = 10,
        latency: float = 1.0,
        engines: int = 3,
        dq: float = 0.9,
        degraded: bool = False,
    ) -> OrchestrationEfficiencyService:
        svc = OrchestrationEfficiencyService()
        for i in range(n):
            svc.record(OrchestrationEfficiencyRecord(
                session_id=f"s{i}",
                intent_class="research",
                engines_invoked=[f"e{j}" for j in range(engines)],
                total_latency_s=latency,
                dq_score=dq,
                degraded=degraded,
            ))
        return svc

    def test_oe_formula_correct(self):
        svc = self._service_with_records(n=10, latency=1.0, engines=3, dq=0.9)
        w = svc.compute_window(OEWindowDuration.HOUR_24)
        # OE = (10 * 0.9) / (1.0 * 3) = 9 / 3 = 3.0
        assert abs(w.oe_score - 3.0) < 0.01

    def test_empty_window_returns_zero_oe(self):
        svc = OrchestrationEfficiencyService()
        w = svc.compute_window(OEWindowDuration.HOUR_1)
        assert w.oe_score == 0.0
        assert w.total_tasks == 0

    def test_degraded_fraction_computed(self):
        svc = OrchestrationEfficiencyService()
        for i in range(5):
            svc.record(OrchestrationEfficiencyRecord(
                session_id=f"s{i}", intent_class="reflection",
                engines_invoked=["soul_mirror"], total_latency_s=0.8,
                dq_score=0.85, degraded=(i < 2)
            ))
        w = svc.compute_window(OEWindowDuration.HOUR_24)
        assert abs(w.degraded_fraction - 0.4) < 0.01

    def test_bottleneck_hint_identifies_slow_intent(self):
        svc = OrchestrationEfficiencyService()
        for i in range(5):
            svc.record(OrchestrationEfficiencyRecord(
                session_id=f"fast_{i}", intent_class="reflection",
                engines_invoked=["soul_mirror"], total_latency_s=0.5,
                dq_score=0.9, degraded=False,
            ))
        for i in range(5):
            svc.record(OrchestrationEfficiencyRecord(
                session_id=f"slow_{i}", intent_class="research",
                engines_invoked=["research_desk", "crystal_graphrag"],
                total_latency_s=3.5, dq_score=0.9, degraded=False,
            ))
        w = svc.compute_window(OEWindowDuration.HOUR_24)
        assert w.bottleneck_hint == "research"

    def test_compute_all_windows_returns_four_entries(self):
        svc = self._service_with_records(n=5)
        all_w = svc.compute_all_windows()
        assert set(all_w.keys()) == {"1h", "24h", "7d", "30d"}
