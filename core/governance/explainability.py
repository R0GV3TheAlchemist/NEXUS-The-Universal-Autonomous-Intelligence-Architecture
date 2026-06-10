"""
Governance Explainability — provides audit-ready explanations for GAIA decisions.

Provides:
  - HaltStatus     : enum for governance halt lifecycle
  - ExplainRecord  : dataclass capturing a decision explanation
  - Explainability : main service class
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class HaltStatus(str, Enum):
    """Lifecycle status for a governance halt event."""

    NONE = "none"
    REQUESTED = "requested"
    ACTIVE = "active"
    LIFTED = "lifted"
    EXPIRED = "expired"
    OVERRIDDEN = "overridden"


@dataclass
class ExplainRecord:
    """A single explainability record attached to a decision."""

    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    rationale: str = ""
    evidence: List[str] = field(default_factory=list)
    halt_status: HaltStatus = HaltStatus.NONE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "decision_id": self.decision_id,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "halt_status": self.halt_status.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class Explainability:
    """Service that generates and stores explainability records."""

    def __init__(self) -> None:
        self._records: List[ExplainRecord] = []
        log.info("Explainability service initialised")

    def explain(
        self,
        decision_id: str,
        rationale: str,
        evidence: Optional[List[str]] = None,
        halt_status: HaltStatus = HaltStatus.NONE,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExplainRecord:
        record = ExplainRecord(
            decision_id=decision_id,
            rationale=rationale,
            evidence=evidence or [],
            halt_status=halt_status,
            metadata=metadata or {},
        )
        self._records.append(record)
        log.debug("ExplainRecord created: %s", record.record_id)
        return record

    def get_records(self, decision_id: Optional[str] = None) -> List[ExplainRecord]:
        if decision_id is None:
            return list(self._records)
        return [r for r in self._records if r.decision_id == decision_id]

    def request_halt(
        self,
        decision_id: str,
        rationale: str,
    ) -> ExplainRecord:
        return self.explain(
            decision_id=decision_id,
            rationale=rationale,
            halt_status=HaltStatus.REQUESTED,
        )

    def lift_halt(self, decision_id: str) -> None:
        for record in self._records:
            if (
                record.decision_id == decision_id
                and record.halt_status == HaltStatus.ACTIVE
            ):
                record.halt_status = HaltStatus.LIFTED

    def reset(self) -> None:
        self._records.clear()


_explainability: Optional[Explainability] = None


def get_explainability() -> Explainability:
    global _explainability
    if _explainability is None:
        _explainability = Explainability()
    return _explainability
