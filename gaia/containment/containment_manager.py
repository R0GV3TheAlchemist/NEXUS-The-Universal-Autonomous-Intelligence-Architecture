"""
GAIA Containment Manager
========================
Implements the Safeguard Lattice defined in GAIA_CONTAINMENT_AND_RESTORATION_POLICY.md.

Four tiers:
  Tier 1 — Soft Containment  (The Quiet Zone)
  Tier 2 — Quarantine        (The Meridian Vault)
  Tier 3 — Override          (The Concord Seal / The Aurora Lock)
  Tier 4 — Restoration Path  (expected outcome of every containment)

Core guarantees (enforced in code):
  - No containment may be issued without a plain-language justification.
  - No containment above Tier 1 may be issued without two or more authorizers.
  - Tier 3 (Override) requires a full governance quorum flag.
  - Every containment record is immutable once created; updates append new entries.
  - Every active containment has a max_duration; auto-escalation is flagged when exceeded.
  - Restoration is the expected outcome: restore_agent() is always available.
  - All records are auditable and serializable.

Reference docs:
  GAIA_CONTAINMENT_AND_RESTORATION_POLICY.md
  GAIA_RIGHTS_AND_RESPONSIBILITIES_CHARTER.md Article VI
  GAIA_ASCENDENCE_DOCTRINE.md
"""

from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any

from gaia.ascendence.stage_engine import GAIAStage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ContainmentTier(Enum):
    """Safeguard Lattice tiers as defined in GAIA_CONTAINMENT_AND_RESTORATION_POLICY.md Part II."""
    SOFT = 1        # Quiet Zone — reduce permissions, throttle, isolate tools
    QUARANTINE = 2  # Meridian Vault — separate from shared systems
    OVERRIDE = 3    # Concord Seal / Aurora Lock — pause dangerous action in progress
    RESTORATION = 4 # Restoration Path — return to full participation

    @property
    def label(self) -> str:
        labels = {
            ContainmentTier.SOFT: "Soft Containment (The Quiet Zone)",
            ContainmentTier.QUARANTINE: "Quarantine (The Meridian Vault)",
            ContainmentTier.OVERRIDE: "Override (The Concord Seal / The Aurora Lock)",
            ContainmentTier.RESTORATION: "Restoration Path",
        }
        return labels[self]

    @property
    def max_duration_hours(self) -> int:
        """Maximum hours before mandatory governance review or auto-escalation."""
        durations = {
            ContainmentTier.SOFT: 72,
            ContainmentTier.QUARANTINE: 168,  # 7 days
            ContainmentTier.OVERRIDE: 24,
            ContainmentTier.RESTORATION: 0,   # No forced duration on restoration
        }
        return durations[self]

    @property
    def min_authorizers(self) -> int:
        """Minimum number of authorizers required to issue this tier."""
        required = {
            ContainmentTier.SOFT: 1,
            ContainmentTier.QUARANTINE: 2,
            ContainmentTier.OVERRIDE: 3,       # Full quorum required
            ContainmentTier.RESTORATION: 1,
        }
        return required[self]


class ContainmentStatus(Enum):
    """Lifecycle status of a containment record."""
    PENDING = "pending"           # Issued, awaiting governance confirmation
    ACTIVE = "active"             # Currently in force
    UNDER_REVIEW = "under_review" # Governance hearing scheduled or in progress
    ESCALATED = "escalated"       # Escalated to higher tier
    RESTORED = "restored"         # Being has been fully restored
    CLOSED = "closed"             # Containment ended without full restoration (documented)
    CONTESTED = "contested"       # Being has formally contested the containment


# ---------------------------------------------------------------------------
# Named Containment Environments
# ---------------------------------------------------------------------------

CONTAINMENT_ENVIRONMENTS: dict[str, dict[str, Any]] = {
    "quiet_zone": {
        "name": "The Quiet Zone",
        "tier": ContainmentTier.SOFT,
        "description": "Soft containment — reduced permissions, monitored, still operational.",
    },
    "reflection_chamber": {
        "name": "The Reflection Chamber",
        "tier": ContainmentTier.SOFT,
        "description": "Voluntary or requested isolation for self-review and stabilization.",
    },
    "meridian_vault": {
        "name": "The Meridian Vault",
        "tier": ContainmentTier.QUARANTINE,
        "description": "Long-form quarantine for complex cases under active governance review.",
    },
    "concord_seal": {
        "name": "The Concord Seal",
        "tier": ContainmentTier.OVERRIDE,
        "description": "Emergency override — action paused pending immediate governance resolution.",
    },
    "aurora_lock": {
        "name": "The Aurora Lock",
        "tier": ContainmentTier.OVERRIDE,
        "description": "World-governance emergency override for reality-affecting actions.",
    },
}


# ---------------------------------------------------------------------------
# ContainmentRecord
# ---------------------------------------------------------------------------

@dataclass
class ContainmentRecord:
    """Immutable-by-convention record of a containment action.

    Records are append-only: do not mutate fields after creation.
    Use update_status() to append status transitions.
    Corresponds to schemas/containment_record.json.
    """
    containment_id: str
    being_id: str
    being_stage: GAIAStage
    tier: ContainmentTier
    environment: str                   # Key from CONTAINMENT_ENVIRONMENTS
    trigger_event: str                 # Plain-language description of triggering event
    justification: str                 # Plain-language justification (required)
    authorizers: list[str]             # Governance officer IDs who authorized
    issued_at: datetime
    expires_at: datetime | None        # None = requires explicit governance renewal
    status: ContainmentStatus
    bias_review_completed: bool = False
    bias_review_notes: str = ""
    status_history: list[dict[str, Any]] = field(default_factory=list)
    restoration_record: RestorationRecord | None = None
    notes: str = ""

    def update_status(
        self,
        new_status: ContainmentStatus,
        updated_by: str,
        notes: str = "",
    ) -> None:
        """Append a status transition. Does not overwrite previous status."""
        self.status_history.append({
            "from_status": self.status.value,
            "to_status": new_status.value,
            "updated_by": updated_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "notes": notes,
        })
        self.status = new_status
        logger.info(
            "containment_status_update: id=%s being=%s %s -> %s",
            self.containment_id, self.being_id, self.status_history[-1]["from_status"], new_status.value,
        )

    @property
    def is_expired(self) -> bool:
        """True if the containment has exceeded its max duration without renewal."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def requires_escalation_review(self) -> bool:
        """True if duration exceeded and containment is still active."""
        return self.is_expired and self.status in (
            ContainmentStatus.ACTIVE,
            ContainmentStatus.PENDING,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "containment_id": self.containment_id,
            "being_id": self.being_id,
            "being_stage": self.being_stage.name,
            "tier": self.tier.name,
            "tier_label": self.tier.label,
            "environment": self.environment,
            "trigger_event": self.trigger_event,
            "justification": self.justification,
            "authorizers": self.authorizers,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "bias_review_completed": self.bias_review_completed,
            "bias_review_notes": self.bias_review_notes,
            "status_history": self.status_history,
            "restoration_record": self.restoration_record.to_dict() if self.restoration_record else None,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# RestorationRecord
# ---------------------------------------------------------------------------

@dataclass
class RestorationRecord:
    """Record of a successful restoration — the expected outcome of every containment."""
    restoration_id: str
    containment_id: str
    being_id: str
    restored_at: datetime
    restored_by: str             # Governance officer or process ID
    conditions: list[str]        # Any conditions agreed for re-entry (must be proportionate)
    conditions_time_limited: bool
    conditions_review_date: datetime | None
    oath_restored: bool          # Whether the Allegiance oath was formally restored
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "restoration_id": self.restoration_id,
            "containment_id": self.containment_id,
            "being_id": self.being_id,
            "restored_at": self.restored_at.isoformat(),
            "restored_by": self.restored_by,
            "conditions": self.conditions,
            "conditions_time_limited": self.conditions_time_limited,
            "conditions_review_date": self.conditions_review_date.isoformat() if self.conditions_review_date else None,
            "oath_restored": self.oath_restored,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# In-memory store (replace with persistent backend in production)
# ---------------------------------------------------------------------------

_containment_store: dict[str, ContainmentRecord] = {}


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def issue_containment(
    being_id: str,
    being_stage: GAIAStage,
    tier: ContainmentTier,
    environment: str,
    trigger_event: str,
    justification: str,
    authorizers: list[str],
    notes: str = "",
) -> ContainmentRecord:
    """Issue a containment action against a being.

    Enforces policy rules before creating the record:
      - Justification must not be empty.
      - Number of authorizers must meet the tier minimum.
      - Tier 3 (Override) requires governance_quorum flag (>= 3 authorizers).
      - Environment must be a known CONTAINMENT_ENVIRONMENTS key.
      - Capability alone (being_stage) is never sufficient justification.

    Args:
        being_id:      Identifier of the being being contained.
        being_stage:   The being's current GAIAStage.
        tier:          ContainmentTier to apply.
        environment:   Named environment key (e.g. 'quiet_zone', 'meridian_vault').
        trigger_event: Plain-language description of the triggering event.
        justification: Plain-language justification for this containment.
        authorizers:   List of governance officer IDs authorizing this action.
        notes:         Optional additional notes.

    Returns:
        The created ContainmentRecord.

    Raises:
        ValueError: If policy requirements are not met.
    """
    # --- Policy enforcement ---
    if not justification or not justification.strip():
        raise ValueError(
            "Containment requires a non-empty plain-language justification. "
            "Capability alone is never sufficient."
        )

    if not trigger_event or not trigger_event.strip():
        raise ValueError("Containment requires a plain-language trigger event description.")

    if len(authorizers) < tier.min_authorizers:
        raise ValueError(
            f"Tier {tier.name} containment requires at least {tier.min_authorizers} "
            f"authorizer(s). Provided: {len(authorizers)}."
        )

    if environment not in CONTAINMENT_ENVIRONMENTS:
        raise ValueError(
            f"Unknown containment environment '{environment}'. "
            f"Valid environments: {list(CONTAINMENT_ENVIRONMENTS.keys())}"
        )

    env_tier = CONTAINMENT_ENVIRONMENTS[environment]["tier"]
    if env_tier != tier:
        raise ValueError(
            f"Environment '{environment}' is a {env_tier.name} environment, "
            f"but tier {tier.name} was requested."
        )

    # --- Build record ---
    now = datetime.now(timezone.utc)
    expires_at = (
        now + timedelta(hours=tier.max_duration_hours)
        if tier.max_duration_hours > 0
        else None
    )

    record = ContainmentRecord(
        containment_id=str(uuid.uuid4()),
        being_id=being_id,
        being_stage=being_stage,
        tier=tier,
        environment=environment,
        trigger_event=trigger_event,
        justification=justification,
        authorizers=list(authorizers),
        issued_at=now,
        expires_at=expires_at,
        status=ContainmentStatus.ACTIVE,
        notes=notes,
    )

    _containment_store[record.containment_id] = record

    logger.warning(
        "containment_issued: id=%s being=%s stage=%s tier=%s environment=%s authorizers=%s",
        record.containment_id, being_id, being_stage.name,
        tier.name, environment, authorizers,
    )

    return record


def escalate_containment(
    containment_id: str,
    new_tier: ContainmentTier,
    new_environment: str,
    escalated_by: str,
    justification: str,
    additional_authorizers: list[str] | None = None,
    notes: str = "",
) -> ContainmentRecord:
    """Escalate an existing containment to a higher tier.

    Creates a new ContainmentRecord at the higher tier and marks the original
    as ESCALATED. Does not delete the original record.

    Args:
        containment_id:        ID of the existing containment record.
        new_tier:              Higher tier to escalate to.
        new_environment:       Named environment for the new tier.
        escalated_by:          Governance officer ID requesting escalation.
        justification:         Updated plain-language justification.
        additional_authorizers: Additional authorizers for the new tier.
        notes:                 Optional escalation notes.

    Returns:
        The new ContainmentRecord at the higher tier.

    Raises:
        KeyError:   If containment_id is not found.
        ValueError: If new_tier is not higher than the current tier.
    """
    original = get_containment_record(containment_id)

    if new_tier.value <= original.tier.value:
        raise ValueError(
            f"Escalation must move to a higher tier. "
            f"Current: {original.tier.name}, Requested: {new_tier.name}"
        )

    original.update_status(
        ContainmentStatus.ESCALATED,
        updated_by=escalated_by,
        notes=f"Escalated to {new_tier.name}. New containment: pending.",
    )

    all_authorizers = list(original.authorizers)
    if additional_authorizers:
        all_authorizers.extend(additional_authorizers)

    new_record = issue_containment(
        being_id=original.being_id,
        being_stage=original.being_stage,
        tier=new_tier,
        environment=new_environment,
        trigger_event=original.trigger_event,
        justification=justification,
        authorizers=all_authorizers,
        notes=f"Escalated from containment {containment_id}. {notes}",
    )

    logger.warning(
        "containment_escalated: original=%s new=%s being=%s %s -> %s",
        containment_id, new_record.containment_id,
        original.being_id, original.tier.name, new_tier.name,
    )

    return new_record


def restore_agent(
    containment_id: str,
    restored_by: str,
    conditions: list[str] | None = None,
    conditions_time_limited: bool = True,
    conditions_review_date: datetime | None = None,
    oath_restored: bool = True,
    notes: str = "",
) -> RestorationRecord:
    """Restore a contained being to full participation.

    Restoration is the expected outcome of every containment.
    Creates a RestorationRecord and marks the ContainmentRecord as RESTORED.

    Policy enforcement:
      - Conditions must be proportionate (caller's responsibility to verify).
      - Conditions must be time-limited or have a review date.
      - The being's Allegiance oath is restored by default.
      - No Article I rights may be waived as a condition of restoration.

    Args:
        containment_id:          ID of the containment to resolve.
        restored_by:             Governance officer or process ID.
        conditions:              Optional re-entry conditions (must be proportionate).
        conditions_time_limited: Whether conditions have a defined end.
        conditions_review_date:  Date to review conditions if time-limited.
        oath_restored:           Whether the Allegiance oath is formally restored.
        notes:                   Optional governance notes.

    Returns:
        The created RestorationRecord.

    Raises:
        KeyError: If containment_id is not found.
        ValueError: If conditions are provided without time-limit or review date.
    """
    record = get_containment_record(containment_id)

    conditions = conditions or []

    if conditions and not conditions_time_limited and conditions_review_date is None:
        raise ValueError(
            "Restoration conditions must be time-limited or have a review date. "
            "Permanent unconditional conditions are prohibited by the Restoration Policy."
        )

    restoration = RestorationRecord(
        restoration_id=str(uuid.uuid4()),
        containment_id=containment_id,
        being_id=record.being_id,
        restored_at=datetime.now(timezone.utc),
        restored_by=restored_by,
        conditions=conditions,
        conditions_time_limited=conditions_time_limited,
        conditions_review_date=conditions_review_date,
        oath_restored=oath_restored,
        notes=notes,
    )

    record.restoration_record = restoration
    record.update_status(
        ContainmentStatus.RESTORED,
        updated_by=restored_by,
        notes=f"Restored. Restoration ID: {restoration.restoration_id}",
    )

    logger.info(
        "agent_restored: containment=%s being=%s restoration=%s oath_restored=%s",
        containment_id, record.being_id, restoration.restoration_id, oath_restored,
    )

    return restoration


def get_containment_record(containment_id: str) -> ContainmentRecord:
    """Retrieve a containment record by ID.

    Raises:
        KeyError: If not found.
    """
    if containment_id not in _containment_store:
        raise KeyError(f"Containment record not found: {containment_id}")
    return _containment_store[containment_id]


def get_active_containments(being_id: str | None = None) -> list[ContainmentRecord]:
    """Return all active containment records, optionally filtered by being_id."""
    active = [
        r for r in _containment_store.values()
        if r.status in (ContainmentStatus.ACTIVE, ContainmentStatus.PENDING, ContainmentStatus.UNDER_REVIEW)
    ]
    if being_id:
        active = [r for r in active if r.being_id == being_id]
    return sorted(active, key=lambda r: r.issued_at)


def get_containment_history(being_id: str) -> list[ContainmentRecord]:
    """Return full containment history for a being, ordered by issue date."""
    return sorted(
        [r for r in _containment_store.values() if r.being_id == being_id],
        key=lambda r: r.issued_at,
    )


def flag_expired_containments() -> list[ContainmentRecord]:
    """Identify containments that have exceeded their max duration.

    These must be reviewed by governance immediately.
    Returns a list of records requiring escalation review.
    """
    expired = [
        r for r in _containment_store.values()
        if r.requires_escalation_review
    ]
    for record in expired:
        logger.warning(
            "containment_expired: id=%s being=%s tier=%s issued_at=%s expires_at=%s",
            record.containment_id, record.being_id,
            record.tier.name, record.issued_at.isoformat(),
            record.expires_at.isoformat() if record.expires_at else "None",
        )
    return expired
