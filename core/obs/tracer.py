"""
core/obs/tracer.py

Trace context manager for GAIA-OS.
Links all log entries within a multi-step agent loop by a shared trace_id.
Uses threading.local so concurrent sessions have independent trace IDs.

Usage:
    from core.obs import TraceContext

    with TraceContext(name="ingest_canon") as trace:
        # all log calls inside here carry trace.trace_id
        pass
"""
import uuid
import time
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional


_local = threading.local()


def get_current_trace_id() -> Optional[str]:
    """Returns the active trace_id for the current thread, or None."""
    return getattr(_local, "trace_id", None)


@dataclass
class TraceSpan:
    name: str
    trace_id: str
    started_at: str
    ended_at: Optional[str] = None
    duration_ms: Optional[float] = None
    outcome: str = "ok"
    meta: Dict[str, Any] = field(default_factory=dict)
    children: List["TraceSpan"] = field(default_factory=list)


class TraceContext:
    """
    Context manager that sets a trace_id for the duration of a block.
    Supports nesting: child spans carry the same root trace_id.

    Usage:
        with TraceContext("query_rag") as ctx:
            do_work()
            print(ctx.trace_id)
    """

    _spans: List[TraceSpan] = []
    _lock = threading.Lock()

    def __init__(self, name: str, meta: Optional[Dict[str, Any]] = None):
        self.name = name
        self.meta = meta or {}
        self.trace_id: Optional[str] = None
        self._span: Optional[TraceSpan] = None
        self._start: Optional[float] = None
        self._parent_id: Optional[str] = None

    def __enter__(self) -> "TraceContext":
        self._parent_id = getattr(_local, "trace_id", None)
        if self._parent_id is None:
            self.trace_id = str(uuid.uuid4())
        else:
            self.trace_id = self._parent_id
        _local.trace_id = self.trace_id
        self._start = time.monotonic()
        self._span = TraceSpan(
            name=self.name,
            trace_id=self.trace_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            meta=self.meta,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        elapsed = (time.monotonic() - self._start) * 1000
        self._span.ended_at = datetime.now(timezone.utc).isoformat()
        self._span.duration_ms = round(elapsed, 3)
        self._span.outcome = "error" if exc_type else "ok"
        with TraceContext._lock:
            TraceContext._spans.append(self._span)
        _local.trace_id = self._parent_id
        return False

    @classmethod
    def all_spans(cls) -> List[TraceSpan]:
        with cls._lock:
            return list(cls._spans)

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._spans.clear()

    @classmethod
    def export_json(cls) -> str:
        import json
        from dataclasses import asdict
        with cls._lock:
            return json.dumps([asdict(s) for s in cls._spans], indent=2)


@contextmanager
def trace(name: str, meta: Optional[Dict[str, Any]] = None) -> Generator[TraceContext, None, None]:
    """Functional alias for TraceContext for use with `with trace('name'):` syntax."""
    ctx = TraceContext(name, meta)
    with ctx as c:
        yield c
