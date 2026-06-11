"""
core.obs.audit
==============
Audit logging primitives for GAIA-OS observability layer.

Provides:
  AuditEventType  — enum of event categories
  AuditEvent      — single immutable audit record
  AuditLog        — in-memory append-only audit log with query helpers
  get_audit()     — module-level singleton accessor
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional


class AuditEventType(str, Enum):
    # --- original set ---
    ACTION_REQUESTED  = "action_requested"
    ACTION_APPROVED   = "action_approved"
    ACTION_BLOCKED    = "action_blocked"
    CONSENT_GRANTED   = "consent_granted"
    CONSENT_REVOKED   = "consent_revoked"
    HALT_TRIGGERED    = "halt_triggered"
    HALT_CLEARED      = "halt_cleared"
    SESSION_START     = "session_start"
    SESSION_END       = "session_end"
    IDENTITY_VERIFIED = "identity_verified"
    POLICY_EVALUATED  = "policy_evaluated"
    ANOMALY_DETECTED  = "anomaly_detected"
    GENERIC           = "generic"
    # --- added to match test expectations ---
    MEMORY_WRITE       = "memory_write"
    MEMORY_READ        = "memory_read"
    AGENT_ACTION       = "agent_action"
    EXTERNAL_API_CALL  = "external_api_call"
    POLICY_DECISION    = "policy_decision"
    TOOL_CALL          = "tool_call"
    SAFETY_VIOLATION   = "safety_violation"


@dataclass(frozen=True)
class AuditEvent:
    """A single immutable audit record."""
    event_type: AuditEventType
    # 'action' is the canonical field name used by tests; 'message' is kept
    # as a read-only alias via property below (frozen dataclass workaround:
    # we store both and make one shadow the other).
    action: str
    actor: str = "system"
    outcome: str = "ok"
    target: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def message(self) -> str:  # backward-compat alias
        return self.action

    def to_dict(self) -> dict:
        return {
            "event_id":   self.event_id,
            "event_type": self.event_type.value,
            "action":     self.action,
            "actor":      self.actor,
            "outcome":    self.outcome,
            "target":     self.target,
            "metadata":   self.metadata,
            "timestamp":  self.timestamp,
        }


class AuditLog:
    """
    Thread-safe in-memory append-only audit log.

    Three ways to call record():

        # 1. Pass a pre-built AuditEvent object:
        log.record(AuditEvent(AuditEventType.AGENT_ACTION, "loop:step1"))

        # 2. Pass 3 positional args (event_type, outcome, detail):
        log.record(AuditEventType.MEMORY_WRITE, "ok", "wrote key=x")

        # 3. Pass keyword arguments (convenience form):
        log.record(event_type=AuditEventType.MEMORY_WRITE,
                   actor="gaian", action="write:memory:session", outcome="ok")
    """

    def __init__(self, max_size: int = 10_000) -> None:
        self._events: List[AuditEvent] = []
        self._max_size = max_size
        self._lock = threading.Lock()
        self._listeners: List[Callable[[AuditEvent], None]] = []

    # ------------------------------------------------------------------
    # Core append
    # ------------------------------------------------------------------

    def record(
        self,
        event_type_or_event=None,
        outcome: str = "ok",
        detail: str = "",
        *,
        event_type=None,
        action: str = "",
        actor: str = "system",
        target=None,
        **metadata,
    ) -> AuditEvent:
        """
        Append an audit event.  Returns the stored AuditEvent.

        Accepts:
          record(AuditEvent(...))                          # positional object
          record(AuditEventType.X, "ok", "detail text")   # 3-positional form
          record(event_type=..., actor=..., action=...)    # keyword form
        """
        if isinstance(event_type_or_event, AuditEventType):
            _et = event_type_or_event
            _action = detail or action
            _outcome = outcome
        elif isinstance(event_type_or_event, AuditEvent):
            # record(AuditEvent(...))
            with self._lock:
                self._events.append(event_type_or_event)
            return event_type_or_event
        else:
            _et = event_type
            _action = action
            _outcome = outcome
        if _et is None:
            raise ValueError("record() requires an AuditEvent or event_type=")
        ev = AuditEvent(
            event_type=_et,
            action=_action,
            actor=actor,
            outcome=_outcome,
            target=target,
            metadata=metadata,
        )
        with self._lock:
            self._events.append(ev)
            if len(self._events) > self._max_size:
                self._events = self._events[-self._max_size:]
        for cb in self._listeners:
            try:
                cb(ev)
            except Exception:
                pass
        return ev

    # ------------------------------------------------------------------
    # Convenience emit (kept for backward compat)
    # ------------------------------------------------------------------

    def emit(
        self,
        event_type: AuditEventType,
        message: str,
        actor: str = "system",
        target: Optional[str] = None,
        **metadata,
    ) -> AuditEvent:
        """Build and record an event in one call (legacy name)."""
        return self.record(
            event_type=event_type,
            action=message,
            actor=actor,
            target=target,
            **metadata,
        )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the total number of stored events."""
        with self._lock:
            return len(self._events)

    def all_events(self) -> List[AuditEvent]:
        """Return a snapshot of all stored events (oldest first)."""
        with self._lock:
            return list(self._events)

    def query(
        self,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
        outcome: Optional[str] = None,
    ) -> List[AuditEvent]:
        """
        Return events matching ALL supplied filters.

        Args:
            event_type: filter by AuditEventType
            actor:      filter by actor string
            outcome:    filter by outcome string ("ok", "deny", …)
        """
        with self._lock:
            results = list(self._events)
        if event_type is not None:
            results = [e for e in results if e.event_type == event_type]
        if actor is not None:
            results = [e for e in results if e.actor == actor]
        if outcome is not None:
            results = [e for e in results if e.outcome == outcome]
        return results

    def tail(self, n: int = 50) -> List[AuditEvent]:
        """Return the n most recent events."""
        with self._lock:
            return self._events[-n:]

    def filter_by_type(self, event_type: AuditEventType) -> List[AuditEvent]:
        """Backward-compat alias for query(event_type=...)."""
        return self.query(event_type=event_type)

    def filter_by_actor(self, actor: str) -> List[AuditEvent]:
        """Backward-compat alias for query(actor=...)."""
        return self.query(actor=actor)

    def export_json(self) -> str:
        """Serialize all events to a JSON string."""
        import json
        return json.dumps([e.to_dict() for e in self.all_events()], default=str)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def add_listener(self, callback: Callable[[AuditEvent], None]) -> None:
        """Register a callback fired on every new event."""
        self._listeners.append(callback)

    def __len__(self) -> int:
        return self.count()

    def __iter__(self):
        return iter(self.all_events())


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_audit_log: Optional[AuditLog] = None


def get_audit() -> AuditLog:
    """Return the process-wide AuditLog singleton."""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log
