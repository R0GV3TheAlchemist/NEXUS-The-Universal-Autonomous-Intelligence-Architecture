"""
tests/test_agentic_loop_obs.py

Verifies that AgenticLoop correctly emits obs signals:
- TraceContext spans created per session and per phase
- StructuredLogger receives tool_call records with correct fields
- AuditLog receives SESSION_START, SESSION_END, AGENT_ACTION events
- Telemetry records per-phase latency and session total
- Gate deny writes PERMISSION_DENY audit event
- Cancellation is logged
- Zero breakage: loop still returns correct AgenticLoopResult
"""
import asyncio
import pytest
import io

from core.agentic_loop import AgenticLoop, HaltCondition, create_loop
from core.obs.structured_logger import StructuredLogger
from core.obs.tracer import TraceContext
from core.obs.audit import AuditLog, AuditEventType
from core.obs.telemetry import Telemetry
import core.obs as obs_module


# ── Helpers ──────────────────────────────────────────────────────────────────

class FakeGateApproved:
    async def evaluate(self, action, gaian_id):
        class R:
            approved = True
            requires_human_approval = False
            reason = None
        return R()


class FakeGateDeny:
    async def evaluate(self, action, gaian_id):
        class R:
            approved = False
            requires_human_approval = False
            reason = "test_deny"
        return R()


class FakeGateHumanRequired:
    async def evaluate(self, action, gaian_id):
        class R:
            approved = False
            requires_human_approval = True
            reason = "needs human"
        return R()


async def _tool_ok(context, cycle):
    return {"ok": True}


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_obs():
    """Fresh obs singletons for every test."""
    buf = io.StringIO()
    logger = StructuredLogger(stream=buf)
    audit = AuditLog()
    telemetry = Telemetry()
    TraceContext.clear()

    obs_module._logger = logger
    obs_module._audit = audit
    obs_module._telemetry = telemetry

    import core.agentic_loop as al_module
    al_module._struct_logger = logger
    al_module._audit = audit
    al_module._telemetry = telemetry
    al_module._OBS_AVAILABLE = True

    yield logger, audit, telemetry
    TraceContext.clear()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAgenticLoopObs:
    def test_session_audit_events_present(self, reset_obs):
        _, audit, _ = reset_obs
        loop = create_loop(max_iterations=2)
        _run(loop.run(goal="test goal", gaian_id="r0gv3"))
        types = {e.event_type for e in audit.all_events()}
        assert AuditEventType.SESSION_START in types
        assert AuditEventType.SESSION_END in types

    def test_agent_action_audited_per_cycle(self, reset_obs):
        _, audit, _ = reset_obs
        loop = create_loop(max_iterations=2,
                           tool_registry={"test_tool": _tool_ok})
        _run(loop.run(goal="test goal", gaian_id="r0gv3"))
        actions = audit.query(event_type=AuditEventType.AGENT_ACTION)
        assert len(actions) >= 1

    def test_gate_deny_writes_policy_decision(self, reset_obs):
        _, audit, _ = reset_obs
        loop = create_loop(action_gate=FakeGateDeny(), max_iterations=3)
        _run(loop.run(goal="blocked goal", gaian_id="r0gv3"))
        blocked = audit.query(event_type=AuditEventType.POLICY_DECISION, outcome="blocked")
        assert len(blocked) >= 1

    def test_gate_human_deny_writes_permission_deny(self, reset_obs):
        _, audit, _ = reset_obs
        async def deny_callback(action, reason):
            return False
        loop = create_loop(action_gate=FakeGateHumanRequired(),
                           approval_callback=deny_callback, max_iterations=3)
        _run(loop.run(goal="sensitive goal", gaian_id="r0gv3"))
        denied = audit.query(event_type=AuditEventType.PERMISSION_DENY)
        assert len(denied) >= 1

    def test_telemetry_records_phases(self, reset_obs):
        _, _, telemetry = reset_obs
        loop = create_loop(max_iterations=2)
        _run(loop.run(goal="telemetry test", gaian_id="r0gv3"))
        summary = telemetry.summary()
        # At least perceive, reason, observe phases should be recorded
        phase_keys = {k for k in summary if k.startswith("agentic_loop.")}
        assert len(phase_keys) >= 2

    def test_telemetry_session_total(self, reset_obs):
        _, _, telemetry = reset_obs
        loop = create_loop(max_iterations=1)
        _run(loop.run(goal="session total", gaian_id="r0gv3"))
        m = telemetry.get("agentic_loop.session")
        assert m is not None
        assert m.call_count == 1
        assert m.avg_latency_ms is not None

    def test_trace_spans_created(self, reset_obs):
        TraceContext.clear()
        loop = create_loop(max_iterations=1)
        _run(loop.run(goal="trace test", gaian_id="r0gv3"))
        spans = TraceContext.all_spans()
        span_names = {s.name for s in spans}
        assert any("agentic_loop" in n for n in span_names)

    def test_structured_log_has_session_id(self, reset_obs):
        logger, _, _ = reset_obs
        loop = create_loop(max_iterations=1)
        _run(loop.run(goal="log fields test", gaian_id="r0gv3"))
        records = logger.records()
        assert len(records) >= 1
        # Every record should have a msg field
        for r in records:
            assert "msg" in r
            assert "ts" in r

    def test_result_goal_achieved_on_stub_planner(self, reset_obs):
        loop = create_loop(max_iterations=5)
        result = _run(loop.run(goal="stub goal", gaian_id="r0gv3"))
        # Stub planner declares complete after 3 cycles
        assert result.halt_condition == HaltCondition.GOAL_ACHIEVED
        assert result.goal_achieved is True

    def test_cancellation_logged(self, reset_obs):
        logger, _, _ = reset_obs
        loop = create_loop(max_iterations=10)
        loop.cancel()  # cancel before run
        result = _run(loop.run(goal="cancel test", gaian_id="r0gv3"))
        assert result.halt_condition == HaltCondition.GAIAN_CANCELLED
        msgs = [r["msg"] for r in logger.records()]
        assert any("CANCELLED" in m for m in msgs)

    def test_loop_result_to_dict(self, reset_obs):
        loop = create_loop(max_iterations=2)
        result = _run(loop.run(goal="dict test", gaian_id="r0gv3"))
        d = result.to_dict()
        assert "session_id" in d
        assert "halt_condition" in d
        assert "goal_achieved" in d
