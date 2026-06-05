"""
tests/test_observability.py

Full test coverage for the GAIA-OS Observability & Audit Layer (Issue #231).
Tests: StructuredLogger, TraceContext, AuditLog, Telemetry.
"""
import json
import time
import threading
import pytest

from core.obs.structured_logger import StructuredLogger, LogLevel
from core.obs.tracer import TraceContext, get_current_trace_id, trace
from core.obs.audit import AuditLog, AuditEventType
from core.obs.telemetry import Telemetry


# ---------------------------------------------------------------------------
# StructuredLogger
# ---------------------------------------------------------------------------

class TestStructuredLogger:
    def setup_method(self):
        import io
        self._buf = io.StringIO()
        self.logger = StructuredLogger(stream=self._buf)

    def _records(self):
        self._buf.seek(0)
        return [json.loads(line) for line in self._buf if line.strip()]

    def test_info_record_has_required_fields(self):
        self.logger.info("hello world", tool="test_tool")
        records = self._records()
        assert len(records) == 1
        r = records[0]
        assert r["level"] == "INFO"
        assert r["msg"] == "hello world"
        assert r["tool"] == "test_tool"
        assert "ts" in r
        assert "trace_id" in r

    def test_tool_call_shorthand(self):
        self.logger.tool_call("rag.query", latency_ms=42.5, outcome="ok")
        records = self._records()
        assert records[0]["tool"] == "rag.query"
        assert records[0]["latency_ms"] == 42.5
        assert records[0]["outcome"] == "ok"

    def test_error_level(self):
        self.logger.error("something broke")
        assert self._records()[0]["level"] == "ERROR"

    def test_export_json(self):
        self.logger.info("a")
        self.logger.info("b")
        exported = json.loads(self.logger.export_json())
        assert len(exported) == 2

    def test_thread_safety(self):
        errors = []
        def write_logs():
            try:
                for _ in range(50):
                    self.logger.info("thread log")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_logs) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(self.logger.records()) == 250


# ---------------------------------------------------------------------------
# TraceContext
# ---------------------------------------------------------------------------

class TestTraceContext:
    def setup_method(self):
        TraceContext.clear()

    def test_trace_id_set_inside_context(self):
        assert get_current_trace_id() is None
        with TraceContext("test_op") as ctx:
            assert get_current_trace_id() == ctx.trace_id
            assert ctx.trace_id is not None
        assert get_current_trace_id() is None

    def test_nested_traces_share_root_id(self):
        with TraceContext("outer") as outer:
            outer_id = outer.trace_id
            with TraceContext("inner") as inner:
                assert inner.trace_id == outer_id

    def test_span_recorded_on_exit(self):
        with TraceContext("recorded_op"):
            pass
        spans = TraceContext.all_spans()
        assert len(spans) == 1
        assert spans[0].name == "recorded_op"
        assert spans[0].duration_ms is not None
        assert spans[0].outcome == "ok"

    def test_span_outcome_error_on_exception(self):
        with pytest.raises(ValueError):
            with TraceContext("failing_op"):
                raise ValueError("oops")
        spans = TraceContext.all_spans()
        assert spans[-1].outcome == "error"

    def test_functional_trace_alias(self):
        with trace("func_trace") as ctx:
            assert ctx.trace_id is not None

    def test_export_json(self):
        with TraceContext("export_test"):
            pass
        exported = json.loads(TraceContext.export_json())
        assert isinstance(exported, list)
        assert exported[0]["name"] == "export_test"


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------

class TestAuditLog:
    def setup_method(self):
        self.audit = AuditLog()

    def test_record_creates_event(self):
        event = self.audit.record(
            event_type=AuditEventType.MEMORY_WRITE,
            actor="gaian",
            action="write:memory:session",
            outcome="ok",
        )
        assert event.event_type == AuditEventType.MEMORY_WRITE
        assert event.actor == "gaian"
        assert self.audit.count() == 1

    def test_append_only_contract(self):
        self.audit.record(AuditEventType.AGENT_ACTION, "system", "loop:step1")
        self.audit.record(AuditEventType.AGENT_ACTION, "system", "loop:step2")
        events = self.audit.all_events()
        assert len(events) == 2
        # Cannot delete individual events (no delete method)
        assert not hasattr(self.audit, "delete_event")

    def test_query_by_event_type(self):
        self.audit.record(AuditEventType.MEMORY_WRITE, "gaian", "w1")
        self.audit.record(AuditEventType.EXTERNAL_API_CALL, "system", "api1")
        writes = self.audit.query(event_type=AuditEventType.MEMORY_WRITE)
        assert len(writes) == 1
        assert writes[0].action == "w1"

    def test_query_by_outcome(self):
        self.audit.record(AuditEventType.POLICY_DECISION, "system", "p1", outcome="ok")
        self.audit.record(AuditEventType.POLICY_DECISION, "system", "p2", outcome="deny")
        denied = self.audit.query(outcome="deny")
        assert len(denied) == 1

    def test_export_json(self):
        self.audit.record(AuditEventType.SESSION_START, "gaian", "boot")
        exported = json.loads(self.audit.export_json())
        assert isinstance(exported, list)
        assert exported[0]["event_type"] == AuditEventType.SESSION_START

    def test_thread_safety(self):
        errors = []
        def write_audit():
            try:
                for _ in range(20):
                    self.audit.record(AuditEventType.AGENT_ACTION, "sys", "act")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_audit) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert self.audit.count() == 100


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

class TestTelemetry:
    def setup_method(self):
        self.tel = Telemetry()

    def test_record_and_retrieve(self):
        self.tel.record("rag.query", latency_ms=50.0)
        self.tel.record("rag.query", latency_ms=100.0)
        m = self.tel.get("rag.query")
        assert m.call_count == 2
        assert m.avg_latency_ms == 75.0
        assert m.error_rate == 0.0

    def test_error_rate(self):
        self.tel.record("rag.ingest", latency_ms=10.0, error=False)
        self.tel.record("rag.ingest", latency_ms=20.0, error=True)
        m = self.tel.get("rag.ingest")
        assert m.error_rate == 0.5

    def test_percentiles(self):
        for i in range(1, 101):
            self.tel.record("tool_x", latency_ms=float(i))
        m = self.tel.get("tool_x")
        assert m.p50 is not None
        assert m.p95 is not None
        assert m.p99 is not None
        assert m.p50 <= m.p95 <= m.p99

    def test_summary_includes_all_tools(self):
        self.tel.record("tool_a", latency_ms=1.0)
        self.tel.record("tool_b", latency_ms=2.0)
        summary = self.tel.summary()
        assert "tool_a" in summary
        assert "tool_b" in summary

    def test_export_json(self):
        self.tel.record("x", latency_ms=5.0)
        exported = json.loads(self.tel.export_json())
        assert "x" in exported

    def test_reset_single_tool(self):
        self.tel.record("tool_a", latency_ms=1.0)
        self.tel.record("tool_b", latency_ms=1.0)
        self.tel.reset("tool_a")
        assert self.tel.get("tool_a") is None
        assert self.tel.get("tool_b") is not None
