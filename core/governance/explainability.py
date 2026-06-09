"""DecisionExplainer — decision explainability layer for GAIA (issue #251).

Consumes TraceRecord JSON-Lines written by core/trace.py and turns them
into human-readable decision reports, Canon citation chains, full
chain-of-thought exports, and counterfactual diff analyses.

Design goals:
- Any logged decision can be explained to a non-technical stakeholder
  in plain language.
- Canon influence is traceable per decision.
- Full CoT trace is exportable per session / correlation-id.
- Counterfactual: "what would have changed if Canon passage X were absent?"
- All logic is pure Python — no LLM call required for the explainability
  layer itself (explanations are derived from structured trace data).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_AUDIT_DIR = Path("core/audit")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CanonCitation:
    """A single Canon passage that influenced a decision."""
    ref: str                   # e.g. "C01", "C32"
    trace_ids: list[str]       # which trace records cited this passage
    event_types: list[str]     # which event types referenced it
    frequency: int             # how many times it appeared


@dataclass
class DecisionStep:
    """One step in a chain-of-thought trace."""
    trace_id: str
    event: str
    started_at: str
    latency_ms: Optional[float]
    canon_refs: list[str]
    inputs_summary: str
    outputs_summary: str
    error: Optional[str]


@dataclass
class DecisionReport:
    """Human-readable explanation for a session or correlation."""
    session_id: str            # correlation_id used as session key
    generated_at: str
    total_steps: int
    canon_citations: list[CanonCitation]
    chain_of_thought: list[DecisionStep]
    plain_language_summary: str
    error_count: int
    total_latency_ms: float


@dataclass
class CounterfactualResult:
    """Result of asking: what changes if Canon passage *ref* were absent?"""
    counterfactual_ref: str
    affected_steps: list[str]  # trace_ids that would change
    affected_event_types: list[str]
    impact_summary: str
    canon_dependency_depth: int  # how many unique events relied on this ref


@dataclass
class DashboardEntry:
    """Gaian-facing summary of a recent decision session."""
    session_id: str
    started_at: str
    step_count: int
    error_count: int
    top_canon_refs: list[str]
    total_latency_ms: float
    plain_summary: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _summarise(data: dict[str, Any], max_keys: int = 4) -> str:
    """Produce a compact, non-technical one-liner from an inputs/outputs dict."""
    if not data:
        return "(no data)"
    items = list(data.items())[:max_keys]
    parts = []
    for k, v in items:
        if isinstance(v, float):
            parts.append(f"{k}={v:.3g}")
        elif isinstance(v, (list, dict)):
            parts.append(f"{k}=[{type(v).__name__}, len={len(v)}]")
        else:
            s = str(v)
            parts.append(f"{k}={s[:40]}" if len(s) > 40 else f"{k}={s}")
    suffix = f" (+{len(data) - max_keys} more)" if len(data) > max_keys else ""
    return ", ".join(parts) + suffix


def _plain_summary(steps: list[DecisionStep], citations: list[CanonCitation]) -> str:
    """Generate a plain-language paragraph suitable for a non-technical reader."""
    if not steps:
        return "No decision steps were recorded for this session."

    n = len(steps)
    errors = sum(1 for s in steps if s.error)
    top_events = _top_n([s.event for s in steps], 3)
    top_canon = [c.ref for c in sorted(citations, key=lambda c: -c.frequency)][:3]
    latency = sum(s.latency_ms or 0 for s in steps)

    lines = [
        f"GAIA completed {n} reasoning step{'s' if n != 1 else ''} "
        f"in {latency:.0f} ms.",
    ]
    if top_events:
        lines.append(
            f"The primary activities were: {', '.join(top_events)}."
        )
    if top_canon:
        lines.append(
            f"Decisions were grounded in Canon passages: "
            f"{', '.join(top_canon)}."
        )
    if errors:
        lines.append(
            f"{errors} step{'s' if errors != 1 else ''} encountered an error "
            f"and were handled safely."
        )
    else:
        lines.append("All steps completed without errors.")
    return " ".join(lines)


def _top_n(items: list[str], n: int) -> list[str]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return [k for k, _ in sorted(counts.items(), key=lambda x: -x[1])][:n]


# ---------------------------------------------------------------------------
# DecisionExplainer
# ---------------------------------------------------------------------------


class DecisionExplainer:
    """Ingests TraceRecord JSONL from the audit directory and exposes
    explainability methods.

    All methods operate on in-memory data loaded from disk; the audit
    directory is the single source of truth.
    """

    def __init__(self, audit_dir: Path = _AUDIT_DIR) -> None:
        self._audit_dir = audit_dir

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_records(
        self,
        since_iso: Optional[str] = None,
        gaian_id: Optional[str] = None,
    ) -> list[dict]:
        """Load all TraceRecord dicts from JSONL audit files.

        Args:
            since_iso: ISO-8601 timestamp; records before this are excluded.
            gaian_id:  If set, only records from this GAIAN are returned.
        """
        cutoff: Optional[datetime] = None
        if since_iso:
            try:
                cutoff = datetime.fromisoformat(since_iso)
                if cutoff.tzinfo is None:
                    cutoff = cutoff.replace(tzinfo=timezone.utc)
            except ValueError:
                logger.warning("Invalid since_iso: %s — ignoring filter", since_iso)

        records: list[dict] = []
        for path in sorted(self._audit_dir.glob("traces_*.jsonl")):
            try:
                with path.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if gaian_id and rec.get("gaian_id") != gaian_id:
                            continue
                        if cutoff:
                            started = rec.get("started_at", "")
                            try:
                                ts = datetime.fromisoformat(started)
                                if ts.tzinfo is None:
                                    ts = ts.replace(tzinfo=timezone.utc)
                                if ts < cutoff:
                                    continue
                            except ValueError:
                                pass
                        records.append(rec)
            except OSError as exc:
                logger.error("Could not read audit file %s: %s", path, exc)
        return records

    # ------------------------------------------------------------------
    # Core explainability methods
    # ------------------------------------------------------------------

    def explain_session(
        self,
        correlation_id: str,
        gaian_id: Optional[str] = None,
    ) -> DecisionReport:
        """Generate a full DecisionReport for a single session.

        Uses correlation_id as the session key (matching core/trace.py).
        """
        all_records = self.load_records(gaian_id=gaian_id)
        session_records = [
            r for r in all_records
            if r.get("correlation_id") == correlation_id
        ]

        steps = [self._record_to_step(r) for r in session_records]
        citations = self._extract_citations(session_records)
        summary = _plain_summary(steps, citations)
        total_latency = sum(s.latency_ms or 0 for s in steps)
        error_count = sum(1 for s in steps if s.error)

        return DecisionReport(
            session_id=correlation_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_steps=len(steps),
            canon_citations=citations,
            chain_of_thought=steps,
            plain_language_summary=summary,
            error_count=error_count,
            total_latency_ms=total_latency,
        )

    def export_trace(
        self,
        correlation_id: str,
        gaian_id: Optional[str] = None,
    ) -> list[dict]:
        """Export the full raw CoT trace for a session as a list of dicts."""
        all_records = self.load_records(gaian_id=gaian_id)
        return [
            r for r in all_records
            if r.get("correlation_id") == correlation_id
        ]

    def canon_citations_for_session(
        self,
        correlation_id: str,
    ) -> list[CanonCitation]:
        """Return all Canon citations for a session, sorted by frequency."""
        all_records = self.load_records()
        session_records = [
            r for r in all_records
            if r.get("correlation_id") == correlation_id
        ]
        return sorted(
            self._extract_citations(session_records),
            key=lambda c: -c.frequency,
        )

    def counterfactual(
        self,
        correlation_id: str,
        absent_canon_ref: str,
    ) -> CounterfactualResult:
        """Analyse what would change if *absent_canon_ref* were not in the Canon.

        Returns which steps relied on that passage and a plain-language
        impact summary.
        """
        all_records = self.load_records()
        session_records = [
            r for r in all_records
            if r.get("correlation_id") == correlation_id
        ]
        affected_steps: list[str] = []
        affected_events: list[str] = []
        for rec in session_records:
            refs = rec.get("canon_refs") or []
            if absent_canon_ref in refs:
                affected_steps.append(rec["trace_id"])
                affected_events.append(rec.get("event", "unknown"))

        unique_events = list(dict.fromkeys(affected_events))
        depth = len(affected_steps)

        if depth == 0:
            impact = (
                f"Canon passage {absent_canon_ref} was not referenced in this "
                f"session. Removing it would have no effect on this decision."
            )
        else:
            impact = (
                f"Canon passage {absent_canon_ref} influenced {depth} "
                f"reasoning step{'s' if depth != 1 else ''} "
                f"({', '.join(unique_events)}). "
                f"Without it, those steps would have lacked their grounding "
                f"constraint, potentially altering the action chosen."
            )

        return CounterfactualResult(
            counterfactual_ref=absent_canon_ref,
            affected_steps=affected_steps,
            affected_event_types=unique_events,
            impact_summary=impact,
            canon_dependency_depth=depth,
        )

    def dashboard(
        self,
        since_iso: Optional[str] = None,
        gaian_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[DashboardEntry]:
        """Return a Gaian-facing summary list of recent decision sessions.

        Groups trace records by correlation_id and produces one entry per
        session, sorted newest-first.
        """
        records = self.load_records(since_iso=since_iso, gaian_id=gaian_id)

        # Group by correlation_id
        sessions: dict[str, list[dict]] = {}
        for rec in records:
            cid = rec.get("correlation_id", "unknown")
            sessions.setdefault(cid, []).append(rec)

        entries: list[DashboardEntry] = []
        for cid, recs in sessions.items():
            steps = [self._record_to_step(r) for r in recs]
            citations = self._extract_citations(recs)
            top_refs = [c.ref for c in sorted(citations, key=lambda c: -c.frequency)][:5]
            total_latency = sum(s.latency_ms or 0 for s in steps)
            error_count = sum(1 for s in steps if s.error)
            started = min((r.get("started_at", "") for r in recs), default="")
            entries.append(
                DashboardEntry(
                    session_id=cid,
                    started_at=started,
                    step_count=len(steps),
                    error_count=error_count,
                    top_canon_refs=top_refs,
                    total_latency_ms=total_latency,
                    plain_summary=_plain_summary(steps, citations),
                )
            )

        # Sort newest-first by started_at
        entries.sort(key=lambda e: e.started_at, reverse=True)
        return entries[:limit]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _record_to_step(rec: dict) -> DecisionStep:
        return DecisionStep(
            trace_id=rec.get("trace_id", "?"),
            event=rec.get("event", "unknown"),
            started_at=rec.get("started_at", ""),
            latency_ms=rec.get("latency_ms"),
            canon_refs=rec.get("canon_refs") or [],
            inputs_summary=_summarise(rec.get("inputs") or {}),
            outputs_summary=_summarise(rec.get("outputs") or {}),
            error=rec.get("error"),
        )

    @staticmethod
    def _extract_citations(records: list[dict]) -> list[CanonCitation]:
        """Build a CanonCitation list from a set of trace records."""
        ref_map: dict[str, dict] = {}
        for rec in records:
            for ref in rec.get("canon_refs") or []:
                if ref not in ref_map:
                    ref_map[ref] = {
                        "trace_ids": [],
                        "event_types": [],
                        "frequency": 0,
                    }
                ref_map[ref]["trace_ids"].append(rec.get("trace_id", "?"))
                event = rec.get("event", "unknown")
                if event not in ref_map[ref]["event_types"]:
                    ref_map[ref]["event_types"].append(event)
                ref_map[ref]["frequency"] += 1
        return [
            CanonCitation(
                ref=ref,
                trace_ids=data["trace_ids"],
                event_types=data["event_types"],
                frequency=data["frequency"],
            )
            for ref, data in ref_map.items()
        ]
