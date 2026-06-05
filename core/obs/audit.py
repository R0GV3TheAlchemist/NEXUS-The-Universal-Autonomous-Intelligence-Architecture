"""
core/obs/audit.py

Immutable append-only audit log for sensitive and irreversible GAIA-OS actions.
All entries are timestamped, linked to a trace_id, and exportable to JSON.
Gaian-owned: the audit log can be exported and deleted by the Gaian only.

Audit events include:
    - permission grants and denials
    - memory writes and deletions
    - external API calls
    - file system writes
    - agent action completions
    - policy decisions
"""
import json
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from .tracer import get_current_trace_id


@dataclass
class AuditEvent:
    event_type: str
    actor: str
    action: str
    outcome: str
    trace_id: Optional[str]
    ts: str
    resource: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Canonical audit event types
class AuditEventType:
    PERMISSION_GRANT = "permission.grant"
    PERMISSION_DENY = "permission.deny"
    MEMORY_WRITE = "memory.write"
    MEMORY_DELETE = "memory.delete"
    MEMORY_READ = "memory.read"
    EXTERNAL_API_CALL = "external.api_call"
    FILE_WRITE = "file.write"
    FILE_DELETE = "file.delete"
    AGENT_ACTION = "agent.action"
    POLICY_DECISION = "policy.decision"
    RAG_INGEST = "rag.ingest"
    RAG_QUERY = "rag.query"
    SESSION_START = "session.start"
    SESSION_END = "session.end"


class AuditLog:
    """
    Append-only in-memory audit log.
    Thread-safe. Export to JSON for persistence.

    Note: For production use, persist to encrypted storage via core/security.
    This implementation is the in-memory foundation that the persistence layer wraps.
    """

    def __init__(self):
        self._events: List[AuditEvent] = []
        self._lock = threading.Lock()

    def record(
        self,
        event_type: str,
        actor: str,
        action: str,
        outcome: str = "ok",
        resource: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Record an audit event. Returns the created event.
        Once appended, events cannot be modified or removed (append-only contract).
        """
        event = AuditEvent(
            event_type=event_type,
            actor=actor,
            action=action,
            outcome=outcome,
            trace_id=get_current_trace_id(),
            ts=datetime.now(timezone.utc).isoformat(),
            resource=resource,
            meta=meta or {},
        )
        with self._lock:
            self._events.append(event)
        return event

    def query(
        self,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        outcome: Optional[str] = None,
        since: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Filter audit events by optional criteria. Returns a copy."""
        with self._lock:
            results = list(self._events)
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if actor:
            results = [e for e in results if e.actor == actor]
        if outcome:
            results = [e for e in results if e.outcome == outcome]
        if since:
            results = [e for e in results if e.ts >= since]
        return results

    def export_json(self) -> str:
        """Export all audit events as a JSON array. Gaian-owned export."""
        with self._lock:
            return json.dumps([e.to_dict() for e in self._events], indent=2, default=str)

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def all_events(self) -> List[AuditEvent]:
        with self._lock:
            return list(self._events)
