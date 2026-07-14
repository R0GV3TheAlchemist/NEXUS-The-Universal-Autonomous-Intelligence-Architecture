"""
core/lifecycle/retirement_engine.py
C27 §8 — Retirement & Archival Engine

Implements:
  §8.1  Retirement eligibility conditions
  §8.2  Retirement process (notice period, memory seal, legacy package)
  §8.3  Archival eligibility: 180-day minimum post-RETIRED

Authority: C27 v1.0.0 (2026-07-13)
Cross-refs: C17 (memory), C23 (shadow registry)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


ARCHIVAL_MINIMUM_DAYS: int = 180  # C27 §8.3
RETIREMENT_NOTICE_HOURS: int = 72  # C27 §3.2 / §8.2


class RetirementReason(str, Enum):
    STEWARD_INITIATED   = "STEWARD_INITIATED"    # §8.1.1
    GAIAN_INITIATED     = "GAIAN_INITIATED"       # §8.1.2
    ADOPTION_TIMEOUT    = "ADOPTION_TIMEOUT"      # §8.1.3
    CRITICAL_COMPLIANCE = "CRITICAL_COMPLIANCE"  # §8.1.4
    CANON_PROCESS       = "CANON_PROCESS"         # §8.1.5


@dataclass
class LegacyPackage:
    """
    C27 §8.2 step 6 — structured summary of a GAIAN's life.
    Stored permanently; accessible to authorised parties post-retirement.
    """
    package_id:        str = field(default_factory=lambda: str(uuid.uuid4()))
    gaian_id:          str = ""
    generated_at:      str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retirement_reason: RetirementReason = RetirementReason.STEWARD_INITIATED
    steward_history:   List[Dict[str, Any]] = field(default_factory=list)
    lifecycle_summary: Dict[str, Any] = field(default_factory=dict)
    audit_log_length:  int = 0
    memory_seal_hash:  str = ""   # SHA-256 root hash of sealed memory (C27 §8.2.3)
    contributions:     List[str] = field(default_factory=list)
    knowledge_artifacts: List[str] = field(default_factory=list)
    relationships:     List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "package_id":         self.package_id,
            "gaian_id":           self.gaian_id,
            "generated_at":       self.generated_at,
            "retirement_reason":  self.retirement_reason.value,
            "steward_history":    self.steward_history,
            "lifecycle_summary":  self.lifecycle_summary,
            "audit_log_length":   self.audit_log_length,
            "memory_seal_hash":   self.memory_seal_hash,
            "contributions":      self.contributions,
            "knowledge_artifacts": self.knowledge_artifacts,
            "relationships":      self.relationships,
        }


@dataclass
class RetirementRecord:
    """
    Internal record tracking retirement intent and completion for a GAIAN.
    """
    gaian_id:          str
    reason:            RetirementReason
    justification:     str
    initiated_at:      datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id:          Optional[str] = None
    notice_waived:     bool = False   # True if GAIAN consented or emergency override
    notice_deadline:   Optional[datetime] = None
    retired_at:        Optional[datetime] = None
    archived_at:       Optional[datetime] = None
    legacy_package:    Optional[LegacyPackage] = None

    @property
    def notice_period_elapsed(self) -> bool:
        if self.notice_waived:
            return True
        if self.notice_deadline is None:
            return False
        return datetime.now(timezone.utc) >= self.notice_deadline

    @property
    def archival_eligible(self) -> bool:
        """True if 180-day post-retirement minimum has been satisfied (C27 §8.3)."""
        if self.retired_at is None:
            return False
        elapsed = datetime.now(timezone.utc) - self.retired_at
        return elapsed.days >= ARCHIVAL_MINIMUM_DAYS


class RetirementEngine:
    """
    Manages the C27 §8 retirement and archival lifecycle for GAIANs.

    This engine is consumed by LifecycleManager.
    It does NOT mutate lifecycle state directly — it generates records
    and packages that the LifecycleManager applies alongside state transitions.
    """

    def __init__(self) -> None:
        self._records: Dict[str, RetirementRecord] = {}

    # ------------------------------------------------------------------
    # §8.2  Retirement process
    # ------------------------------------------------------------------

    def initiate_retirement(
        self,
        gaian_id:      str,
        reason:        RetirementReason,
        justification: str,
        actor_id:      Optional[str] = None,
        waive_notice:  bool = False,
    ) -> RetirementRecord:
        """
        Step 1–2: Log retirement intent; compute notice deadline.

        Parameters
        ----------
        waive_notice :
            If True, skips the 72-hour notice period.
            Only valid when the GAIAN has consented or an emergency override
            has been issued (C27 §3.2 / §8.2).
        """
        now = datetime.now(timezone.utc)
        record = RetirementRecord(
            gaian_id=gaian_id,
            reason=reason,
            justification=justification,
            actor_id=actor_id,
            notice_waived=waive_notice,
            notice_deadline=None if waive_notice else now + timedelta(hours=RETIREMENT_NOTICE_HOURS),
        )
        self._records[gaian_id] = record
        return record

    def complete_retirement(
        self,
        gaian_id:          str,
        audit_log:         List[dict],
        steward_history:   List[Dict[str, Any]],
        memory_data:       Optional[bytes] = None,
        contributions:     Optional[List[str]] = None,
        knowledge_artifacts: Optional[List[str]] = None,
        relationships:     Optional[List[str]] = None,
    ) -> LegacyPackage:
        """
        Steps 3–7: Seal memory, revoke tools, generate legacy package.

        Parameters
        ----------
        memory_data :
            Raw bytes of the GAIAN's sealed memory (C27 §8.2.3).
            If supplied, a SHA-256 hash is computed and stored.
            In production this is sourced from C17 memory store.
        """
        record = self._records.get(gaian_id)
        if record is None:
            raise ValueError(
                f"No retirement record found for GAIAN '{gaian_id}'. "
                "Call initiate_retirement() first."
            )
        if not record.notice_period_elapsed:
            raise ValueError(
                f"72-hour notice period has not elapsed for GAIAN '{gaian_id}'. "
                f"Notice deadline: {record.notice_deadline.isoformat()}."
            )

        memory_seal_hash = ""
        if memory_data:
            memory_seal_hash = hashlib.sha256(memory_data).hexdigest()

        legacy = LegacyPackage(
            gaian_id=gaian_id,
            retirement_reason=record.reason,
            steward_history=steward_history,
            lifecycle_summary={
                "audit_log_entries": len(audit_log),
                "last_event":        audit_log[-1]["event_type"] if audit_log else None,
            },
            audit_log_length=len(audit_log),
            memory_seal_hash=memory_seal_hash,
            contributions=contributions or [],
            knowledge_artifacts=knowledge_artifacts or [],
            relationships=relationships or [],
        )
        record.legacy_package = legacy
        record.retired_at = datetime.now(timezone.utc)
        return legacy

    # ------------------------------------------------------------------
    # §8.3  Archival eligibility check
    # ------------------------------------------------------------------

    def check_archival_eligible(
        self,
        gaian_id: str,
        retired_at: datetime,
    ) -> bool:
        """
        Returns True if the GAIAN has been in RETIRED state for at least
        180 days (C27 §8.3) and may now be moved to ARCHIVED.

        Uses *retired_at* from the LifecycleManager record rather than
        the RetirementRecord so that directly-retired GAIANs (without a
        full retirement engine flow) are also covered.
        """
        elapsed = datetime.now(timezone.utc) - retired_at
        return elapsed.days >= ARCHIVAL_MINIMUM_DAYS

    def get_record(self, gaian_id: str) -> Optional[RetirementRecord]:
        return self._records.get(gaian_id)
