"""
core/obs — Observability & Audit Layer
Public API for the GAIA-OS observability stack.

Usage:
    from core.obs import get_logger, get_tracer, get_audit, get_telemetry
"""
from .structured_logger import StructuredLogger, LogLevel
from .tracer import TraceContext, get_current_trace_id
from .audit import AuditLog, AuditEvent
from .telemetry import Telemetry

_logger = StructuredLogger()
_audit = AuditLog()
_telemetry = Telemetry()


def get_logger() -> StructuredLogger:
    return _logger


def get_tracer() -> "TraceContext":
    return TraceContext


def get_audit() -> AuditLog:
    return _audit


def get_telemetry() -> Telemetry:
    return _telemetry


__all__ = [
    "get_logger",
    "get_tracer",
    "get_audit",
    "get_telemetry",
    "StructuredLogger",
    "LogLevel",
    "TraceContext",
    "get_current_trace_id",
    "AuditLog",
    "AuditEvent",
    "Telemetry",
]
