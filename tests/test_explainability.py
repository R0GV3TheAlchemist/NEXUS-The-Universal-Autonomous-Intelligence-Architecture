"""
Test suite for DecisionExplainer — issue #251.

Covers:
- Decision report generation from synthetic trace records
- Plain-language summary correctness
- Canon citation extraction and frequency counting
- Full CoT trace export
- Counterfactual analysis (ref present vs absent)
- Dashboard grouping and sorting
- Edge cases: empty session, unknown correlation_id, no canon refs
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.governance.explainability import (
    CanonCitation,
    DecisionExplainer,
    DecisionReport,
    DecisionStep,
    HaltStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_traces(audit_dir: Path, records: list[dict]) -> None:
    """Write synthetic TraceRecord dicts to a JSONL audit file."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = audit_dir / f"traces_{today}.jsonl"
    with path.open("w") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")


def _make_record(
    trace_id: str,
    correlation_id: str,
    event: str = "llm_inference",
    canon_refs: list[str] | None = None,
    gaian_id: str = "gaian-1",
    latency_ms: float = 50.0,
    error: str | None = None,
    inputs: dict | None = None,
    outputs: dict | None = None,
) -> dict:
    return {
        "trace_id": trace_id,
        "event": event,
        "gaian_id": gaian_id,
        "correlation_id": correlation_id,
        "canon_refs": canon_refs or [],
        "started_at": "2026-06-09T18:00:00+00:00",
        "ended_at": "2026-06-09T18:00:00.050+00:00",
        "latency_ms": latency_ms,
        "inputs": inputs or {"prompt": "test"},
        "outputs": outputs or {"response": "ok"},
        "error": error,
        "meta": {},
    }


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


@pytest.fixture()
def explainer(audit_dir: Path) -> DecisionExplainer:
    return DecisionExplainer(audit_dir=audit_dir)


@pytest.fixture()
def sample_records(audit_dir: Path) -> list[dict]:
    records = [
        _make_record("t-1", "sess-A", "llm_inference", ["C01", "C32"]),
        _make_record("t-2", "sess-A", "action_gate_decision", ["C01"], latency_ms=10.0),
        _make_record("t-3", "sess-A", "tool_call", ["C74"], latency_ms=20.0),
        _make_record("t-4", "sess-B", "llm_inference", ["C32"]),
        _make_record("t-5", "sess-A", "memory_recall", [], error="TimeoutError: read timeout"),
    ]
    _write_traces(audit_dir, records)
    return records


# ---------------------------------------------------------------------------
# DecisionReport tests
# ---------------------------------------------------------------------------


class TestExplainSession:
    def test_report_has_correct_step_count(self, explainer, sample_records):
        report = explainer.explain_session("sess-A")
        assert report.total_steps == 4  # t-1, t-2, t-3, t-5

    def test_report_error_count(self, explainer, sample_records):
        report = explainer.explain_session("sess-A")
        assert report.error_count == 1

    def test_report_total_latency(self, explainer, sample_records):
        report = explainer.explain_session("sess-A")
        assert report.total_latency_ms == pytest.approx(130.0)

    def test_report_session_id(self, explainer, sample_records):
        report = explainer.explain_session("sess-A")
        assert report.session_id == "sess-A"

    def test_report_unknown_session_returns_empty(self, explainer, sample_records):
        report = explainer.explain_session("sess-UNKNOWN")
        assert report.total_steps == 0
        assert report.error_count == 0

    def test_plain_language_summary_mentions_steps(self, explainer, sample_records):
        report = explainer.explain_session("sess-A")
        assert "4 reasoning steps" in report.plain_language_summary

    def test_plain_language_summary_mentions_canon(self, explainer, sample_records):
        report = explainer.explain_session("sess-A")
        assert "Canon" in report.plain_language_summary

    def test_plain_language_mentions_error(self, explainer, sample_records):
        report = explainer.explain_session("sess-A")
        assert "error" in report.plain_language_summary.lower()


# ---------------------------------------------------------------------------
# Canon citation tests
# ---------------------------------------------------------------------------


class TestCanonCitations:
    def test_citation_count(self, explainer, sample_records):
        citations = explainer.canon_citations_for_session("sess-A")
        refs = {c.ref for c in citations}
        assert refs == {"C01", "C32", "C74"}

    def test_c01_frequency(self, explainer, sample_records):
        citations = explainer.canon_citations_for_session("sess-A")
        c01 = next(c for c in citations if c.ref == "C01")
        assert c01.frequency == 2

    def test_citations_sorted_by_frequency(self, explainer, sample_records):
        citations = explainer.canon_citations_for_session("sess-A")
        freqs = [c.frequency for c in citations]
        assert freqs == sorted(freqs, reverse=True)

    def test_citation_trace_ids(self, explainer, sample_records):
        citations = explainer.canon_citations_for_session("sess-A")
        c01 = next(c for c in citations if c.ref == "C01")
        assert set(c01.trace_ids) == {"t-1", "t-2"}

    def test_empty_session_no_citations(self, explainer, sample_records):
        citations = explainer.canon_citations_for_session("sess-UNKNOWN")
        assert citations == []


# ---------------------------------------------------------------------------
# Trace export tests
# ---------------------------------------------------------------------------


class TestTraceExport:
    def test_export_returns_all_session_records(self, explainer, sample_records):
        trace = explainer.export_trace("sess-A")
        assert len(trace) == 4

    def test_export_filtered_by_gaian(self, explainer, sample_records):
        trace = explainer.export_trace("sess-A", gaian_id="gaian-1")
        assert all(r["gaian_id"] == "gaian-1" for r in trace)

    def test_export_unknown_session_empty(self, explainer, sample_records):
        assert explainer.export_trace("sess-NONE") == []


# ---------------------------------------------------------------------------
# Counterfactual tests
# ---------------------------------------------------------------------------


class TestCounterfactual:
    def test_present_ref_has_depth_greater_than_zero(self, explainer, sample_records):
        result = explainer.counterfactual("sess-A", "C01")
        assert result.canon_dependency_depth == 2
        assert set(result.affected_steps) == {"t-1", "t-2"}

    def test_absent_ref_has_zero_depth(self, explainer, sample_records):
        result = explainer.counterfactual("sess-A", "C99")
        assert result.canon_dependency_depth == 0
        assert "no effect" in result.impact_summary.lower()

    def test_impact_summary_mentions_event_types(self, explainer, sample_records):
        result = explainer.counterfactual("sess-A", "C01")
        assert "llm_inference" in result.impact_summary or "action_gate" in result.impact_summary

    def test_affected_event_types_unique(self, explainer, sample_records):
        result = explainer.counterfactual("sess-A", "C01")
        assert len(result.affected_event_types) == len(set(result.affected_event_types))


# ---------------------------------------------------------------------------
# Dashboard tests
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_dashboard_groups_by_session(self, explainer, sample_records):
        entries = explainer.dashboard()
        session_ids = {e.session_id for e in entries}
        assert "sess-A" in session_ids
        assert "sess-B" in session_ids

    def test_dashboard_step_count(self, explainer, sample_records):
        entries = explainer.dashboard()
        sess_a = next(e for e in entries if e.session_id == "sess-A")
        assert sess_a.step_count == 4

    def test_dashboard_top_canon_refs_present(self, explainer, sample_records):
        entries = explainer.dashboard()
        sess_a = next(e for e in entries if e.session_id == "sess-A")
        assert "C01" in sess_a.top_canon_refs

    def test_dashboard_limit(self, explainer, audit_dir):
        records = [
            _make_record(f"t-{i}", f"sess-{i}")
            for i in range(20)
        ]
        _write_traces(audit_dir, records)
        entries = explainer.dashboard(limit=5)
        assert len(entries) <= 5

    def test_dashboard_gaian_filter(self, explainer, audit_dir):
        records = [
            _make_record("t-x", "sess-X", gaian_id="gaian-alpha"),
            _make_record("t-y", "sess-Y", gaian_id="gaian-beta"),
        ]
        _write_traces(audit_dir, records)
        entries = explainer.dashboard(gaian_id="gaian-alpha")
        assert all(e.session_id == "sess-X" for e in entries)
