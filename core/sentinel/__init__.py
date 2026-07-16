"""
core/sentinel/__init__.py
=========================
Public API for the SENTINEL enforcement engine.

SENTINEL is the central alert authority for GAIA. Every spectral
module emits alerts here. SENTINEL evaluates, classifies, logs,
and — where thresholds are exceeded — interrupts execution or
escalates to the Constitutional Layer.

© 2024-2026 R0GV3 The Alchemist — GAIA Project. All rights reserved.
AGPL-3.0 Licensed. Unauthorised derivative works are prohibited.
"""

from core.sentinel.constants import (
    AlertLevel,
    ALERT_LEVEL_LABEL,
    ALERT_LEVEL_HEX,
    INTERRUPT_THRESHOLD,
    CONSTITUTIONAL_ESCALATION_THRESHOLD,
    SENTINEL_VERSION,
)
from core.sentinel.engine import (
    SentinelEngine,
    evaluate_alert,
    emit,
    interrupt_check,
    escalate_to_constitutional,
    get_active_alerts,
    clear_resolved,
)
from core.sentinel.registry import (
    AlertRegistry,
    AlertRecord,
    get_registry,
)

__all__ = [
    # constants
    "AlertLevel",
    "ALERT_LEVEL_LABEL",
    "ALERT_LEVEL_HEX",
    "INTERRUPT_THRESHOLD",
    "CONSTITUTIONAL_ESCALATION_THRESHOLD",
    "SENTINEL_VERSION",
    # engine
    "SentinelEngine",
    "evaluate_alert",
    "emit",
    "interrupt_check",
    "escalate_to_constitutional",
    "get_active_alerts",
    "clear_resolved",
    # registry
    "AlertRegistry",
    "AlertRecord",
    "get_registry",
]
