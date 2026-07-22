"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

incident.py — NEXUS Incident Response Pipeline.

IncidentRecord captures anomalies, ethics violations, and security events.
IncidentResponsePipeline classifies severity, routes to responders,
and tracks resolution. All incidents are immutably hash-chained.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4
import hashlib, json, time


class SeverityLevel(Enum):
    CRITICAL = 0   # ≤ 5 min SLA
    HIGH     = 1   # ≤ 30 min
    MEDIUM   = 2   # ≤ 4 hours
    LOW      = 3   # ≤ 24 hours
    INFO     = 4   # best effort


class IncidentStatus(Enum):
    OPEN        = auto()
    IN_PROGRESS = auto()
    RESOLVED    = auto()
    CLOSED      = auto()


SLA_SECONDS: Dict[SeverityLevel, float] = {
    SeverityLevel.CRITICAL: 300.0,
    SeverityLevel.HIGH:     1800.0,
    SeverityLevel.MEDIUM:   14400.0,
    SeverityLevel.LOW:      86400.0,
    SeverityLevel.INFO:     float("inf"),
}


@dataclass
class IncidentRecord:
    """
    Immutable record of a system anomaly, ethics violation, or security event.
    Hash-chained to the previous incident for tamper detection.
    """
    incident_id:   UUID            = field(default_factory=uuid4)
    title:         str             = ""
    description:   str             = ""
    severity:      SeverityLevel   = SeverityLevel.INFO
    status:        IncidentStatus  = IncidentStatus.OPEN
    source_id:     Optional[UUID]  = None
    related_audit: Optional[UUID]  = None
    created_at:    float           = field(default_factory=time.time)
    resolved_at:   Optional[float] = None
    previous_hash: str             = ""
    hash:          str             = ""
    metadata:      Dict[str, Any]  = field(default_factory=dict)

    def compute_hash(self) -> str:
        payload = json.dumps({
            "incident_id":   str(self.incident_id),
            "title":         self.title,
            "severity":      self.severity.name,
            "created_at":    self.created_at,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def sla_seconds(self) -> float:
        return SLA_SECONDS[self.severity]

    def is_sla_breached(self) -> bool:
        elapsed = time.time() - self.created_at
        return elapsed > self.sla_seconds and \
               self.status not in (IncidentStatus.RESOLVED, IncidentStatus.CLOSED)


class IncidentResponsePipeline:
    """
    Classifies, routes, and tracks resolution of NEXUS incidents.
    Responders register as callables keyed by SeverityLevel.
    All incidents stored in an immutable, hash-chained log.
    """

    def __init__(self) -> None:
        self._incidents:  List[IncidentRecord] = []
        self._responders: Dict[SeverityLevel, List[Callable]] = {
            level: [] for level in SeverityLevel
        }

    def register_responder(self, severity: SeverityLevel,
                           responder: Callable) -> None:
        self._responders[severity].append(responder)

    def report(self, title: str, description: str,
               severity: SeverityLevel,
               source_id: Optional[UUID] = None,
               related_audit: Optional[UUID] = None,
               metadata: Optional[Dict[str, Any]] = None) -> IncidentRecord:
        """Create, hash-chain, log, and route a new incident."""
        prev_hash = self._incidents[-1].hash if self._incidents else ""
        record = IncidentRecord(
            title=title, description=description, severity=severity,
            source_id=source_id, related_audit=related_audit,
            previous_hash=prev_hash, metadata=metadata or {},
        )
        record.hash = record.compute_hash()
        self._incidents.append(record)
        self._route(record)
        return record

    def _route(self, record: IncidentRecord) -> None:
        for responder in self._responders.get(record.severity, []):
            try:
                responder(record)
            except Exception:
                pass

    def resolve(self, incident_id: UUID) -> None:
        for r in self._incidents:
            if r.incident_id == incident_id:
                r.status = IncidentStatus.RESOLVED
                r.resolved_at = time.time()
                return

    def close(self, incident_id: UUID) -> None:
        for r in self._incidents:
            if r.incident_id == incident_id:
                r.status = IncidentStatus.CLOSED
                return

    def classify(self, description: str) -> SeverityLevel:
        """Heuristic severity classifier. Replace with ML backend in production."""
        desc = description.lower()
        if any(k in desc for k in ("critical", "breach", "compromise", "zero-day")):
            return SeverityLevel.CRITICAL
        if any(k in desc for k in ("high", "unauthorized", "violation", "attack")):
            return SeverityLevel.HIGH
        if any(k in desc for k in ("medium", "degraded", "warning", "anomaly")):
            return SeverityLevel.MEDIUM
        if any(k in desc for k in ("low", "minor", "notice")):
            return SeverityLevel.LOW
        return SeverityLevel.INFO

    def open_incidents(self) -> List[IncidentRecord]:
        return [i for i in self._incidents if i.status == IncidentStatus.OPEN]

    def sla_breached(self) -> List[IncidentRecord]:
        return [i for i in self._incidents if i.is_sla_breached()]

    def verify_chain(self) -> bool:
        """Verify hash chain integrity across all incidents."""
        for i, record in enumerate(self._incidents):
            if record.hash != record.compute_hash():
                return False
            if i > 0 and record.previous_hash != self._incidents[i - 1].hash:
                return False
        return True

    def all_incidents(self) -> List[IncidentRecord]:
        return list(self._incidents)
