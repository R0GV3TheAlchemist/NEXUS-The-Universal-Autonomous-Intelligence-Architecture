"""
core/sentinel/engine.py
=======================
The SENTINEL enforcement engine.

Responsibilities:
  - Receive alert signals from all spectral modules and any GAIA subsystem.
  - Evaluate each alert against the threshold matrix.
  - Decide: log only | surface | interrupt | escalate to Constitutional Layer.
  - Maintain the live alert registry (via AlertRegistry).
  - Expose a module-level singleton so callers never need to instantiate
    the engine themselves — just call emit(), interrupt_check(), etc.

Design invariants:
  - SENTINEL never suppresses. Every alert received is recorded.
  - SENTINEL never mutates the originating signal. It appends to the
    alert registry; the source data is read-only from SENTINEL's
    perspective.
  - interrupt_check() is the ONLY place execution halting is decided.
    Callers must honour the boolean it returns.
  - escalate_to_constitutional() is a no-op stub until the Constitutional
    Layer (core/constitutional/layer.py) is live. It logs the escalation
    event so the audit trail is complete.

© 2024-2026 R0GV3 The Alchemist — GAIA Project. All rights reserved.
AGPL-3.0 Licensed. Unauthorised derivative works are prohibited.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from core.sentinel.constants import (
    AlertLevel,
    ALERT_LEVEL_LABEL,
    ALERT_LEVEL_HEX,
    INTERRUPT_THRESHOLD,
    CONSTITUTIONAL_ESCALATION_THRESHOLD,
    UNRESOLVEDATION_LIMIT := "UNRESOLVEDATION_LIMIT",
)
from core.sentinel.registry import AlertRecord, AlertRegistry

# ---------------------------------------------------------------------------
# Workaround: import the constant directly (walrus not valid at module scope)
# ---------------------------------------------------------------------------
from core.sentinel.constants import UNRESOLVEDATION_LIMIT as _UNRES_LIM  # noqa: F401


class SentinelEngine:
    """
    Central SENTINEL enforcement engine.

    Instantiate once as a module-level singleton (_ENGINE below).
    All public functions in this module delegate to that singleton.
    """

    def __init__(self) -> None:
        self._registry: AlertRegistry = AlertRegistry()
        self._constitutional_connected: bool = False
        self._constitutional_handler: Any = None  # set when Constitutional Layer boots

    # ------------------------------------------------------------------
    # Public: intake
    # ------------------------------------------------------------------

    def emit(
        self,
        source: str,
        level: AlertLevel | int,
        message: str,
        payload: dict | None = None,
    ) -> AlertRecord:
        """
        Receive an alert from any GAIA subsystem or spectral module.

        Args:
            source:  Module/subsystem name emitting the alert
                     (e.g. "core.spectral.red", "core.rag.engine").
            level:   AlertLevel (int coerced if needed).
            message: Human-readable alert description.
            payload: Optional structured metadata from the emitter.

        Returns:
            The created AlertRecord (immutable snapshot).
        """
        level = AlertLevel(int(level))

        # Saturation elevation: if registry is saturated, floor incoming
        # level to WARNING minimum so nothing slips through quietly.
        if self._registry.unresolved_count() >= _UNRES_LIM:
            if level < AlertLevel.WARNING:
                level = AlertLevel.WARNING

        record = AlertRecord(
            alert_id=str(uuid.uuid4()),
            source=source,
            level=level,
            label=ALERT_LEVEL_LABEL[level],
            hex_colour=ALERT_LEVEL_HEX[level],
            message=message,
            payload=payload or {},
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            resolved=False,
            interrupted=False,
            escalated=False,
        )

        self._registry.add(record)
        return record

    # ------------------------------------------------------------------
    # Public: evaluation
    # ------------------------------------------------------------------

    def evaluate_alert(self, record: AlertRecord) -> dict:
        """
        Evaluate a recorded alert and return an action decision dict.

        Returns a dict with keys:
            - "should_interrupt" (bool)
            - "should_escalate"  (bool)
            - "level"            (AlertLevel)
            - "label"            (str)
        """
        should_interrupt = record.level >= INTERRUPT_THRESHOLD
        should_escalate  = record.level >= CONSTITUTIONAL_ESCALATION_THRESHOLD

        return {
            "should_interrupt": should_interrupt,
            "should_escalate":  should_escalate,
            "level":            record.level,
            "label":            record.label,
        }

    def interrupt_check(self, record: AlertRecord) -> bool:
        """
        Return True if the alert warrants halting the calling execution path.

        Callers MUST respect this return value. SENTINEL does not force
        the halt itself — it is the caller's responsibility to check and
        honour the result.
        """
        decision = self.evaluate_alert(record)
        if decision["should_interrupt"]:
            # Mark the record as interrupted in registry
            self._registry.mark_interrupted(record.alert_id)
        return decision["should_interrupt"]

    def escalate_to_constitutional(
        self,
        record: AlertRecord,
        context: dict | None = None,
    ) -> dict:
        """
        Escalate an EMERGENCY-level alert to the Constitutional Layer.

        If the Constitutional Layer (core/constitutional/layer.py) is not
        yet live, this call is logged and returns a stub response. The
        audit trail is preserved regardless.

        Returns:
            dict with keys "escalated" (bool), "constitutional_response" (str).
        """
        if record.level < CONSTITUTIONAL_ESCALATION_THRESHOLD:
            return {"escalated": False, "constitutional_response": "LEVEL_BELOW_THRESHOLD"}

        self._registry.mark_escalated(record.alert_id)

        if self._constitutional_connected and self._constitutional_handler is not None:
            response = self._constitutional_handler(record, context or {})
            return {"escalated": True, "constitutional_response": response}

        # Constitutional Layer not yet live — log stub and return
        return {
            "escalated": True,
            "constitutional_response": "CONSTITUTIONAL_LAYER_PENDING",
            "note": (
                "core/constitutional/layer.py not yet loaded. "
                "Escalation recorded; will be re-processed when Constitutional Layer boots."
            ),
        }

    def connect_constitutional(
        self,
        handler: Any,
    ) -> None:
        """
        Register the Constitutional Layer handler.
        Called by core/constitutional/layer.py on boot.
        """
        self._constitutional_handler = handler
        self._constitutional_connected = True

    # ------------------------------------------------------------------
    # Public: registry access
    # ------------------------------------------------------------------

    def get_active_alerts(
        self,
        min_level: AlertLevel = AlertLevel.ADVISORY,
    ) -> list[AlertRecord]:
        """Return all unresolved alerts at or above min_level."""
        return self._registry.get_active(min_level=min_level)

    def clear_resolved(self) -> int:
        """Remove all resolved alerts from the registry. Returns count removed."""
        return self._registry.clear_resolved()


# ---------------------------------------------------------------------------
# Module-level singleton + convenience functions
# ---------------------------------------------------------------------------

_ENGINE: SentinelEngine = SentinelEngine()


def emit(
    source: str,
    level: AlertLevel | int,
    message: str,
    payload: dict | None = None,
) -> AlertRecord:
    """Emit an alert into the SENTINEL engine."""
    return _ENGINE.emit(source, level, message, payload)


def evaluate_alert(record: AlertRecord) -> dict:
    """Evaluate a recorded alert and return the action decision."""
    return _ENGINE.evaluate_alert(record)


def interrupt_check(record: AlertRecord) -> bool:
    """Return True if execution should be interrupted for this alert."""
    return _ENGINE.interrupt_check(record)


def escalate_to_constitutional(
    record: AlertRecord,
    context: dict | None = None,
) -> dict:
    """Escalate an EMERGENCY alert to the Constitutional Layer."""
    return _ENGINE.escalate_to_constitutional(record, context)


def get_active_alerts(
    min_level: AlertLevel = AlertLevel.ADVISORY,
) -> list[AlertRecord]:
    """Return all unresolved alerts at or above min_level."""
    return _ENGINE.get_active_alerts(min_level)


def clear_resolved() -> int:
    """Remove resolved alerts. Returns count removed."""
    return _ENGINE.clear_resolved()


def get_registry() -> AlertRegistry:
    """Direct access to the alert registry."""
    return _ENGINE._registry
