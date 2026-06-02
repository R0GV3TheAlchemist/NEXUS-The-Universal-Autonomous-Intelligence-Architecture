"""
core/trace.py
GAIA Structured Inference Tracing — Sprint G-7

Provides context managers that wrap every significant GAIA inference call,
writing structured JSON Lines to core/audit/ so that any behavioral regression
can be reproduced and debugged without grepping freeform logs.

Usage (sync):
    with GAIATrace(
        event=TraceEventType.SYNERGY_COMPUTE,
        gaian_id=gaian.id,
        canon_refs=["C32"],
        inputs={"dominant_hz": 528.0},
    ) as trace:
        reading, state = engine.compute(**params)
        trace.record_output({"synergy_factor": reading.synergy_factor})

Usage (async):
    async with AsyncGAIATrace(
        event=TraceEventType.LLM_INFERENCE,
        gaian_id=gaian.id,
        canon_refs=["C01"],
    ) as trace:
        response = await llm.complete(prompt)
        trace.record_output({"response_tokens": len(response.tokens)})

Canon Ref: C01 (Sovereignty — honest, complete records of GAIA's reasoning)
           C30 (No silent failures — every inference step is observable)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

try:
    from core.logger import correlation_id_ctx, get_logger
    _logger = get_logger("gaia.trace")
except Exception:  # pragma: no cover — standalone usage without full GAIA stack
    import logging
    _logger = logging.getLogger("gaia.trace")
    class _FallbackCtx:
        def get(self, default: str = "-") -> str:
            return default
    correlation_id_ctx = _FallbackCtx()  # type: ignore[assignment]

_AUDIT_DIR = Path("core/audit")


# ── Event Types ──────────────────────────────────────────────────────────── #

class TraceEventType(str, Enum):
    """First-class trace event types. Using (str, Enum) enables mypy exhaustive
    matching while remaining JSON-serialisable without extra conversion."""
    SYNERGY_COMPUTE      = "synergy_compute"
    LLM_INFERENCE        = "llm_inference"
    MEMORY_RECALL        = "memory_recall"
    MEMORY_WRITE         = "memory_write"
    ACTION_GATE_DECISION = "action_gate_decision"
    TASK_NODE_EXEC       = "task_node_exec"
    CANON_LOAD           = "canon_load"
    STAGE_SESSION        = "stage_session"
    TOOL_CALL            = "tool_call"


# ── Trace Record ─────────────────────────────────────────────────────────── #

@dataclass
class TraceRecord:
    """Immutable-after-flush structured audit record. Every field is JSON-safe."""
    trace_id:       str
    event:          str             # TraceEventType.value
    gaian_id:       str | None
    correlation_id: str
    canon_refs:     list[str]
    started_at:     str             # ISO-8601
    ended_at:       str | None
    latency_ms:     float | None
    inputs:         dict[str, Any]
    outputs:        dict[str, Any]
    error:          str | None
    meta:           dict[str, Any] = field(default_factory=dict)


# ── Synchronous Context Manager ───────────────────────────────────────────── #

class GAIATrace:
    """
    Synchronous context manager for tracing a single GAIA inference step.

    - Writes one JSON Line to core/audit/traces_YYYYMMDD.jsonl on exit.
    - Never suppresses exceptions (returns False from __exit__).
    - Records the exception type + message in TraceRecord.error when raised.
    - Thread-safe for writing: each flush is a single append operation.
    """

    def __init__(
        self,
        event: str | TraceEventType,
        gaian_id: str | None = None,
        canon_refs: list[str] | None = None,
        inputs: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        event_val = event.value if isinstance(event, TraceEventType) else event
        self._record = TraceRecord(
            trace_id=str(uuid.uuid4()),
            event=event_val,
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

    # ── Public API ───────────────────────────────────────────────────────── #

    def record_output(self, data: dict[str, Any]) -> None:
        """Merge additional output fields into the trace record before flush."""
        self._record.outputs.update(data)

    def record_meta(self, data: dict[str, Any]) -> None:
        """Merge additional metadata (e.g. model_id, temperature) into the record."""
        self._record.meta.update(data)

    @property
    def trace_id(self) -> str:
        return self._record.trace_id

    # ── Context Manager Protocol ─────────────────────────────────────────── #

    def __enter__(self) -> "GAIATrace":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self._record.ended_at = datetime.now(timezone.utc).isoformat()
        self._record.latency_ms = (time.monotonic() - self._t0) * 1000
        if exc_val is not None:
            self._record.error = f"{type(exc_val).__name__}: {exc_val}"
        self._flush()
        return False  # never suppress exceptions

    # ── Internal ─────────────────────────────────────────────────────────── #

    def _flush(self) -> None:
        """Append one JSON Line to the daily audit file. Creates the directory
        if absent. Failure here is logged but never raises — tracing must not
        crash GAIA (Canon C30: no silent failures, but tracing infra is meta)."""
        try:
            _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
            log_file = _AUDIT_DIR / f"traces_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(self._record)) + "\n")
        except Exception as exc:  # pragma: no cover
            _logger.error("GAIATrace flush failed: %s", exc)


# ── Async Context Manager ─────────────────────────────────────────────────── #

class AsyncGAIATrace(GAIATrace):
    """
    Async context manager variant. Drop-in replacement for use inside
    `async with` blocks. Inherits all behaviour from GAIATrace; only the
    dunder protocol methods differ to satisfy the async CM protocol.

    Example:
        async with AsyncGAIATrace(
            event=TraceEventType.LLM_INFERENCE,
            gaian_id=gaian.id,
            canon_refs=["C01"],
            inputs={"prompt_tokens": 512},
        ) as trace:
            response = await llm.complete(prompt)
            trace.record_output({"response_tokens": len(response.tokens)})
    """

    async def __aenter__(self) -> "AsyncGAIATrace":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        # Delegate to sync __exit__ — the flush is a simple file append and
        # does not benefit from being awaited.
        return self.__exit__(exc_type, exc_val, exc_tb)


# ── CLI Query Utility ─────────────────────────────────────────────────────── #
# Usage:
#   python -m core.trace query --gaian luna --event synergy_compute --error-only
#   python -m core.trace show  --correlation-id req-abc123
#   python -m core.trace stats --event llm_inference --since 24h

def _load_records(
    audit_dir: Path,
    since_hours: int | None = None,
) -> list[dict]:
    """Load all JSONL trace records from the audit directory, newest-first."""
    records: list[dict] = []
    cutoff: datetime | None = None
    if since_hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    for path in sorted(audit_dir.glob("traces_*.jsonl"), reverse=True):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if cutoff is not None:
                    started = record.get("started_at", "")
                    try:
                        ts = datetime.fromisoformat(started)
                        if ts < cutoff:
                            continue
                    except ValueError:
                        pass
                records.append(record)
    return records


def _cmd_query(args: argparse.Namespace) -> None:
    records = _load_records(_AUDIT_DIR, since_hours=args.since)
    if args.gaian:
        records = [r for r in records if r.get("gaian_id") == args.gaian]
    if args.event:
        records = [r for r in records if r.get("event") == args.event]
    if args.error_only:
        records = [r for r in records if r.get("error") is not None]
    for r in records[:args.limit]:
        print(json.dumps(r, indent=2))
    print(f"\n— {len(records)} record(s) matched —", file=sys.stderr)


def _cmd_show(args: argparse.Namespace) -> None:
    records = _load_records(_AUDIT_DIR)
    matches = [
        r for r in records
        if r.get("trace_id") == args.trace_id
        or r.get("correlation_id") == args.correlation_id
    ]
    if not matches:
        print("No matching trace found.", file=sys.stderr)
        sys.exit(1)
    for r in matches:
        print(json.dumps(r, indent=2))


def _cmd_stats(args: argparse.Namespace) -> None:
    records = _load_records(_AUDIT_DIR, since_hours=args.since)
    if args.event:
        records = [r for r in records if r.get("event") == args.event]

    total = len(records)
    errors = sum(1 for r in records if r.get("error"))
    latencies = [r["latency_ms"] for r in records if r.get("latency_ms") is not None]
    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
    max_lat = max(latencies) if latencies else 0.0

    print(json.dumps({
        "event_filter": args.event or "(all)",
        "since_hours": args.since,
        "total": total,
        "errors": errors,
        "error_rate_pct": round(errors / total * 100, 2) if total else 0,
        "avg_latency_ms": round(avg_lat, 2),
        "max_latency_ms": round(max_lat, 2),
    }, indent=2))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core.trace",
        description="GAIA trace query utility",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    q = sub.add_parser("query", help="Filter and display trace records")
    q.add_argument("--gaian", default=None, help="Filter by gaian_id")
    q.add_argument("--event", default=None, help="Filter by event type")
    q.add_argument("--error-only", action="store_true", help="Show only failed traces")
    q.add_argument("--since", type=int, default=None, metavar="HOURS", help="Look back N hours")
    q.add_argument("--limit", type=int, default=50, help="Max records to display (default 50)")
    q.set_defaults(func=_cmd_query)

    s = sub.add_parser("show", help="Show a single trace by ID")
    s.add_argument("--trace-id", default=None, dest="trace_id")
    s.add_argument("--correlation-id", default=None, dest="correlation_id")
    s.set_defaults(func=_cmd_show)

    st = sub.add_parser("stats", help="Aggregate statistics")
    st.add_argument("--event", default=None, help="Filter by event type")
    st.add_argument("--since", type=int, default=24, metavar="HOURS", help="Look back N hours (default 24)")
    st.set_defaults(func=_cmd_stats)

    return parser


if __name__ == "__main__":
    _parser = _build_parser()
    _args = _parser.parse_args()
    _args.func(_args)
