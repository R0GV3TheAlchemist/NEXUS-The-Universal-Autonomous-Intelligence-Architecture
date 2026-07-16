"""
core/sentinel/registry.py
=========================
AlertRegistry — the persistent, append-only alert store for SENTINEL.

Every alert emitted into SENTINEL is recorded here. Records are
immutable once created; state transitions (resolved, interrupted,
escalated) are applied as field updates to the stored record.

Design invariants:
  - Records are NEVER deleted during a session. clear_resolved() removes
    resolved records only after they have been fully processed.
  - Thread safety is not implemented in v1.0. GAIA v1 is single-threaded
    at the engine level. Add a threading.Lock if async I/O is introduced.
  - The registry is in-memory. Persistence to the audit log database
    (schemas/audit_log.py) is handled by a separate flush process.

© 2024-2026 R0GV3 The Alchemist — GAIA Project. All rights reserved.
AGPL-3.0 Licensed. Unauthorised derivative works are prohibited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.sentinel.constants import AlertLevel


@dataclass
class AlertRecord:
    """
    Immutable snapshot of a single alert event.

    Fields are set at creation time. State booleans (resolved,
    interrupted, escalated) are the only mutable fields and are
    updated in-place by the registry.
    """
    alert_id:   str
    source:     str
    level:      AlertLevel
    label:      str
    hex_colour: str
    message:    str
    payload:    dict
    timestamp:  str
    resolved:   bool = False
    interrupted: bool = False
    escalated:  bool = False
    metadata:   dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialise to a plain dict for logging / audit export."""
        return {
            "alert_id":    self.alert_id,
            "source":      self.source,
            "level":       int(self.level),
            "label":       self.label,
            "hex_colour":  self.hex_colour,
            "message":     self.message,
            "payload":     self.payload,
            "timestamp":   self.timestamp,
            "resolved":    self.resolved,
            "interrupted": self.interrupted,
            "escalated":   self.escalated,
            "metadata":    self.metadata,
        }


class AlertRegistry:
    """
    In-memory store for all SENTINEL AlertRecords.

    Provides O(1) lookup by alert_id and O(n) filtered queries
    by level and resolution state.
    """

    def __init__(self) -> None:
        self._records: dict[str, AlertRecord] = {}
        self._insertion_order: list[str] = []

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add(self, record: AlertRecord) -> None:
        """Append a new AlertRecord. Raises ValueError on duplicate ID."""
        if record.alert_id in self._records:
            raise ValueError(f"Duplicate alert_id: {record.alert_id}")
        self._records[record.alert_id] = record
        self._insertion_order.append(record.alert_id)

    def mark_resolved(self, alert_id: str) -> bool:
        """Mark a record as resolved. Returns False if not found."""
        rec = self._records.get(alert_id)
        if rec is None:
            return False
        rec.resolved = True
        return True

    def mark_interrupted(self, alert_id: str) -> bool:
        """Mark a record as having triggered an interrupt."""
        rec = self._records.get(alert_id)
        if rec is None:
            return False
        rec.interrupted = True
        return True

    def mark_escalated(self, alert_id: str) -> bool:
        """Mark a record as having been escalated to Constitutional Layer."""
        rec = self._records.get(alert_id)
        if rec is None:
            return False
        rec.escalated = True
        return True

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, alert_id: str) -> AlertRecord | None:
        """Retrieve a single record by ID."""
        return self._records.get(alert_id)

    def get_active(
        self,
        min_level: AlertLevel = AlertLevel.ADVISORY,
    ) -> list[AlertRecord]:
        """
        Return all unresolved records at or above min_level,
        in insertion order.
        """
        return [
            self._records[aid]
            for aid in self._insertion_order
            if not self._records[aid].resolved
            and self._records[aid].level >= min_level
        ]

    def get_all(self) -> list[AlertRecord]:
        """Return all records (resolved and unresolved) in insertion order."""
        return [self._records[aid] for aid in self._insertion_order]

    def unresolved_count(self) -> int:
        """Return count of currently unresolved records."""
        return sum(
            1 for aid in self._insertion_order
            if not self._records[aid].resolved
        )

    def count_by_level(self, level: AlertLevel) -> int:
        """Return count of all records (including resolved) at a given level."""
        return sum(
            1 for r in self._records.values()
            if r.level == level
        )

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear_resolved(self) -> int:
        """Remove all resolved records. Returns the count removed."""
        to_remove = [
            aid for aid in self._insertion_order
            if self._records[aid].resolved
        ]
        for aid in to_remove:
            del self._records[aid]
        self._insertion_order = [
            aid for aid in self._insertion_order if aid not in to_remove
        ]
        return len(to_remove)

    def __len__(self) -> int:
        return len(self._records)

    def __repr__(self) -> str:
        return (
            f"AlertRegistry(total={len(self)}, "
            f"unresolved={self.unresolved_count()})"
        )
