"""
core/obs/structured_logger.py

Structured JSON logger for GAIA-OS.
Every log entry includes: timestamp, level, trace_id, tool, message, latency_ms, outcome, metadata.
Thread-safe. Writes to stderr by default; configurable to file or any stream.
"""
import json
import sys
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, IO
from .tracer import get_current_trace_id


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    AUDIT = "AUDIT"


class StructuredLogger:
    """
    Emits newline-delimited JSON log records.

    Each record schema:
    {
        "ts": "2026-06-05T07:36:00.000Z",
        "level": "INFO",
        "trace_id": "<uuid or null>",
        "tool": "<tool name or null>",
        "msg": "<message>",
        "latency_ms": <float or null>,
        "outcome": "ok" | "error" | null,
        "meta": {}
    }
    """

    def __init__(self, stream: Optional[IO] = None, min_level: LogLevel = LogLevel.DEBUG):
        self._stream = stream or sys.stderr
        self._min_level = min_level
        self._lock = threading.Lock()
        self._records: list = []

    def _emit(self, record: Dict[str, Any]) -> None:
        with self._lock:
            self._records.append(record)
            line = json.dumps(record, default=str)
            self._stream.write(line + "\n")
            self._stream.flush()

    def _build(
        self,
        level: LogLevel,
        msg: str,
        tool: Optional[str] = None,
        latency_ms: Optional[float] = None,
        outcome: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "trace_id": get_current_trace_id(),
            "tool": tool,
            "msg": msg,
            "latency_ms": latency_ms,
            "outcome": outcome,
            "meta": meta or {},
        }

    def log(
        self,
        level: LogLevel,
        msg: str,
        tool: Optional[str] = None,
        latency_ms: Optional[float] = None,
        outcome: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        record = self._build(level, msg, tool, latency_ms, outcome, meta)
        self._emit(record)

    def debug(self, msg: str, **kwargs) -> None:
        self.log(LogLevel.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        self.log(LogLevel.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        self.log(LogLevel.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self.log(LogLevel.ERROR, msg, **kwargs)

    def tool_call(
        self,
        tool: str,
        latency_ms: float,
        outcome: str = "ok",
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Convenience method: log a completed tool call with timing."""
        self.log(
            LogLevel.INFO,
            f"tool_call:{tool}",
            tool=tool,
            latency_ms=latency_ms,
            outcome=outcome,
            meta=meta,
        )

    def export_json(self) -> str:
        """Export all in-memory log records as a JSON array string."""
        with self._lock:
            return json.dumps(self._records, default=str, indent=2)

    def records(self) -> list:
        with self._lock:
            return list(self._records)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
