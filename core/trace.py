"""
core/trace.py
GAIA Structured Inference Tracing — Sprint G-7

Provides context managers (sync and async) that wrap every significant GAIA
inference call, writing structured JSON Lines to core/audit/ so that any
behavioral regression can be reproduced and debugged without grepping
freeform logs.

Canon Ref: C01 (Sovereignty — honest, complete records of GAIA's reasoning)
           C30 (No silent failures — every inference step is observable)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Correlation ID context — propagated across async boundaries
# ---------------------------------------------------------------------------

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")


def set_correlation_id(cid: str) -> None:
    """Set the correlation ID for the current async context."""
    correlation_id_ctx.set(cid)


def new_correlation_id() -> str:
    """Generate and set a fresh correlation ID; return it."""
    cid = f"req-{uuid.uuid4().hex[:12]}"
    correlation_id_ctx.set(cid)
    return cid


# ---------------------------------------------------------------------------
# Audit directory
# ---------------------------------------------------------------------------

_AUDIT_DIR = Path("core/audit")


# ---------------------------------------------------------------------------
# TraceEventType — type-safe, iterable, mypy-checkable
# ---------------------------------------------------------------------------

class TraceEventType(str, Enum):
    """All recognised GAIA trace event types.

    Extending str allows instances to serialise directly to JSON as strings.
    Using Enum gives exhaustive matching, iteration, and mypy safety.
    """
    SYNERGY_COMPUTE      = "synergy_compute"
    LLM_INFERENCE        = "llm_inference"
    MEMORY_RECALL        = "memory_recall"
    MEMORY_WRITE         = "memory_write"
    ACTION_GATE_DECISION = "action_gate_decision"
    TASK_NODE_EXEC       = "task_node_exec"
    CANON_LOAD           = "canon_load"
    STAGE_SESSION        = "stage_session"
    TOOL_CALL            = "tool_call"


# ---------------------------------------------------------------------------
# TraceRecord — the structured data written to audit/
# ---------------------------------------------------------------------------

@dataclass
class TraceRecord:
    trace_id:       str
    event:          str
    gaian_id:       str | None
    correlation_id: str
    canon_refs:     list[str]
    started_at:     str            # ISO-8601 UTC
    ended_at:       str | None
    latency_ms:     float | None
    inputs:         dict[str, Any]
    outputs:        dict[str, Any]
    error:          str | None
    meta:           dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# GAIATrace — synchronous context manager
# ---------------------------------------------------------------------------

class GAIATrace:
    """
    Synchronous context manager for tracing a GAIA inference step.

    Usage::

        with GAIATrace(
            event=TraceEventType.SYNERGY_COMPUTE,
            gaian_id=gaian.id,
            canon_refs=["C32"],
            inputs={"dominant_hz": 528.0},
        ) as trace:
            reading, state = engine.compute(**params)
            trace.record_output({"synergy_factor": reading.synergy_factor})

    The trace record is flushed to ``core/audit/traces_YYYYMMDD.jsonl`` on
    ``__exit__``, whether or not an exception was raised.  Exceptions are
    **never** suppressed — they propagate normally after being recorded.
    """

    def __init__(
        self,
        event: str | TraceEventType,
        gaian_id: str | None = None,
        canon_refs: list[str] | None = None,
        inputs: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        self._record = TraceRecord(
            trace_id=str(uuid.uuid4()),
            event=str(event),
            gaian_id=gaian_id,
            correlation_id=correlation_id_ctx.get("-"),
            canon_refs=canon_refs or [],
            started_at=datetime.now(timezone.utc).isoformat(),
            ended_at=None,
            latency_ms=None,
            inputs=inputs or {},
            outputs={},
            error=None,
            meta=meta or {},
        )
        self._t0 = time.monotonic()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_output(self, data: dict[str, Any]) -> None:
        """Merge ``data`` into the outputs dict before the trace is flushed."""
        self._record.outputs.update(data)

    def record_meta(self, data: dict[str, Any]) -> None:
        """Merge ``data`` into the meta dict (e.g. model version, tokens)."""
        self._record.meta.update(data)

    @property
    def trace_id(self) -> str:
        return self._record.trace_id

    @property
    def correlation_id(self) -> str:
        return self._record.correlation_id

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "GAIATrace":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._record.ended_at = datetime.now(timezone.utc).isoformat()
        self._record.latency_ms = (time.monotonic() - self._t0) * 1000
        if exc_val:
            self._record.error = f"{type(exc_val).__name__}: {exc_val}"
        self._flush()
        return False  # never suppress exceptions

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _flush(self) -> None:
        """Append the trace record as a JSON Line to the daily audit file."""
        _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        log_file = _AUDIT_DIR / f"traces_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
        line = json.dumps(asdict(self._record), default=str)
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


# ---------------------------------------------------------------------------
# AsyncGAIATrace — async context manager variant
# ---------------------------------------------------------------------------

class AsyncGAIATrace(GAIATrace):
    """
    Async context manager variant — use inside ``async with`` blocks.

    Usage::

        async with AsyncGAIATrace(
            event=TraceEventType.LLM_INFERENCE,
            gaian_id=gaian.id,
            canon_refs=["C01"],
        ) as trace:
            response = await llm.complete(prompt)
            trace.record_output({"response_tokens": len(response.tokens)})
    """

    async def __aenter__(self) -> "AsyncGAIATrace":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        return self.__exit__(exc_type, exc_val, exc_tb)


# ---------------------------------------------------------------------------
# CLI query utility — python -m core.trace
# ---------------------------------------------------------------------------

def _load_records(since_hours: int | None = None) -> list[dict]:
    """Load all JSONL trace records from core/audit/, optionally filtered."""
    records: list[dict] = []
    if not _AUDIT_DIR.exists():
        return records
    cutoff = None
    if since_hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    for path in sorted(_AUDIT_DIR.glob("traces_*.jsonl")):
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if cutoff and rec.get("started_at"):
                        ts = datetime.fromisoformat(rec["started_at"])
                        if ts < cutoff:
                            continue
                    records.append(rec)
                except json.JSONDecodeError:
                    continue
    return records


def _cmd_query(args: argparse.Namespace) -> None:
    since_h = None
    if args.since and args.since.endswith("h"):
        since_h = int(args.since[:-1])
    records = _load_records(since_h)
    if args.gaian:
        records = [r for r in records if r.get("gaian_id") == args.gaian]
    if args.event:
        records = [r for r in records if r.get("event") == args.event]
    if args.error_only:
        records = [r for r in records if r.get("error") is not None]
    for r in records:
        print(json.dumps(r, default=str))
    print(f"\n[{len(records)} records]", file=sys.stderr)


def _cmd_show(args: argparse.Namespace) -> None:
    records = _load_records()
    matches = [r for r in records if r.get("correlation_id") == args.correlation_id]
    for r in matches:
        print(json.dumps(r, indent=2, default=str))
    if not matches:
        print(f"No traces found for correlation_id={args.correlation_id!r}", file=sys.stderr)


def _cmd_stats(args: argparse.Namespace) -> None:
    since_h = None
    if args.since and args.since.endswith("h"):
        since_h = int(args.since[:-1])
    records = _load_records(since_h)
    if args.event:
        records = [r for r in records if r.get("event") == args.event]
    count = len(records)
    errors = sum(1 for r in records if r.get("error"))
    latencies = [r["latency_ms"] for r in records if r.get("latency_ms") is not None]
    avg_ms = sum(latencies) / len(latencies) if latencies else 0.0
    p99_ms = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) >= 100 else (max(latencies) if latencies else 0.0)
    print(f"Event filter : {args.event or '(all)'}") 
    print(f"Total traces : {count}")
    print(f"Errors       : {errors}")
    print(f"Avg latency  : {avg_ms:.1f}ms")
    print(f"P99 latency  : {p99_ms:.1f}ms")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core.trace",
        description="GAIA Trace CLI — query and inspect audit traces",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    q = sub.add_parser("query", help="Stream matching trace records")
    q.add_argument("--gaian", help="Filter by gaian_id")
    q.add_argument("--event", help="Filter by event type")
    q.add_argument("--since", default="24h", help="Time window, e.g. 24h (default: 24h)")
    q.add_argument("--error-only", action="store_true", help="Only show failed traces")
    q.set_defaults(func=_cmd_query)

    s = sub.add_parser("show", help="Show all traces for a correlation ID")
    s.add_argument("--correlation-id", required=True)
    s.set_defaults(func=_cmd_show)

    st = sub.add_parser("stats", help="Aggregate stats for an event type")
    st.add_argument("--event", help="Event type to aggregate")
    st.add_argument("--since", default="24h", help="Time window, e.g. 24h")
    st.set_defaults(func=_cmd_stats)

    return parser


if __name__ == "__main__":
    _parser = _build_parser()
    _args = _parser.parse_args()
    _args.func(_args)
