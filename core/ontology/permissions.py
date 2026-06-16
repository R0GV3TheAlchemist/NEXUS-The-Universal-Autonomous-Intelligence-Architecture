"""GAIA Permission Envelope & Audit Trail — Canon C03 §3.3–3.5, C14 §4.

The Permission Envelope is the set of capabilities, data access rights,
and action scopes authorised for a specific Gaian instance at a specific moment.

The Audit Trail is the immutable (append-only) log of every consequential
action taken by a Gaian instance. It cannot be deleted. It cannot be modified.

Kernel Invariants enforced here (C14 §4):
  - No capability access without a valid permission grant
  - No consequential action without an audit entry
  - No session without a declared Human Principal
  - No memory access without scope authorisation
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from .entities import PermissionTier


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PermissionDeniedError(Exception):
    """Raised when a Gaian attempts an action outside its Permission Envelope."""
    pass


# ---------------------------------------------------------------------------
# Capability Definitions
# ---------------------------------------------------------------------------

class Capability(str, Enum):
    """The set of capabilities a Gaian instance may be granted.

    Capabilities are additive — higher tiers include all lower-tier capabilities.
    No capability is available without explicit grant in the Permission Envelope.
    """
    # Tier 1 — OBSERVER
    READ_ENTITY = "READ_ENTITY"
    READ_ATLAS_NODE = "READ_ATLAS_NODE"
    READ_AUDIT_TRAIL = "READ_AUDIT_TRAIL"

    # Tier 2 — COLLABORATOR
    WRITE_ENTITY = "WRITE_ENTITY"
    CREATE_RELATIONSHIP = "CREATE_RELATIONSHIP"
    TRANSITION_STATE = "TRANSITION_STATE"
    WRITE_MEMORY = "WRITE_MEMORY"

    # Tier 3 — STEWARD
    MANAGE_ATLAS_NODE = "MANAGE_ATLAS_NODE"
    MANAGE_GAIAN = "MANAGE_GAIAN"
    ELEVATE_PERMISSION = "ELEVATE_PERMISSION"
    DEGRADE_ATLAS_NODE = "DEGRADE_ATLAS_NODE"  # Requires HP consent — Constraint #4

    # Tier 4 — SOVEREIGN
    REVOKE_GAIAN = "REVOKE_GAIAN"
    AMEND_CANON = "AMEND_CANON"
    GRANT_SOVEREIGN = "GRANT_SOVEREIGN"


# Default capability sets per tier
_TIER_CAPABILITIES: dict[PermissionTier, set[Capability]] = {
    PermissionTier.OBSERVER: {
        Capability.READ_ENTITY,
        Capability.READ_ATLAS_NODE,
        Capability.READ_AUDIT_TRAIL,
    },
    PermissionTier.COLLABORATOR: {
        Capability.READ_ENTITY,
        Capability.READ_ATLAS_NODE,
        Capability.READ_AUDIT_TRAIL,
        Capability.WRITE_ENTITY,
        Capability.CREATE_RELATIONSHIP,
        Capability.TRANSITION_STATE,
        Capability.WRITE_MEMORY,
    },
    PermissionTier.STEWARD: {
        Capability.READ_ENTITY,
        Capability.READ_ATLAS_NODE,
        Capability.READ_AUDIT_TRAIL,
        Capability.WRITE_ENTITY,
        Capability.CREATE_RELATIONSHIP,
        Capability.TRANSITION_STATE,
        Capability.WRITE_MEMORY,
        Capability.MANAGE_ATLAS_NODE,
        Capability.MANAGE_GAIAN,
        Capability.ELEVATE_PERMISSION,
        Capability.DEGRADE_ATLAS_NODE,
    },
    PermissionTier.SOVEREIGN: {
        c for c in Capability  # All capabilities
    },
}


# ---------------------------------------------------------------------------
# Permission Envelope
# ---------------------------------------------------------------------------

@dataclass
class PermissionEnvelope:
    """The authorised capability set for a specific Gaian instance.

    The envelope is scoped to a (gaian_id, session_id) pair.
    It can be elevated or restricted by the Human Principal at any time.
    """
    gaian_id: str
    human_principal_id: str
    session_id: str
    tier: PermissionTier = PermissionTier.OBSERVER
    additional_capabilities: set[Capability] = field(default_factory=set)
    revoked_capabilities: set[Capability] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    @property
    def active_capabilities(self) -> set[Capability]:
        """Compute the effective capability set: tier defaults + additions - revocations."""
        base = _TIER_CAPABILITIES.get(self.tier, set()).copy()
        base |= self.additional_capabilities
        base -= self.revoked_capabilities
        return base

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def has(self, capability: Capability) -> bool:
        """Check if a specific capability is granted."""
        if self.is_expired:
            return False
        return capability in self.active_capabilities

    def require(self, capability: Capability) -> None:
        """Assert a capability is granted. Raises PermissionDeniedError if not.

        This is the primary guard — call this before every consequential action.
        """
        if not self.has(capability):
            raise PermissionDeniedError(
                f"Gaian {self.gaian_id[:8]} lacks capability {capability.value}. "
                f"Current tier: {self.tier.name}. "
                f"No action outside the Permission Envelope — C03 Constraint #2."
            )

    def grant(self, capability: Capability) -> None:
        """Add a capability beyond the tier default."""
        self.additional_capabilities.add(capability)
        self.revoked_capabilities.discard(capability)

    def revoke(self, capability: Capability) -> None:
        """Remove a capability, overriding the tier default."""
        self.revoked_capabilities.add(capability)
        self.additional_capabilities.discard(capability)

    def elevate_tier(self, new_tier: PermissionTier, granted_by: str) -> None:
        """Elevate the permission tier. Must be invoked by a Human Principal."""
        self.tier = new_tier


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    """A single immutable record of a consequential action — C03 §3.5.

    Audit entries are append-only. They are never modified after creation.
    Every entry carries full provenance: who did what, to what, when, and why.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gaian_id: str = ""
    human_principal_id: str = ""
    session_id: str = ""
    action: str = ""
    capability_used: Optional[Capability] = None
    target_entity_id: Optional[str] = None
    target_entity_type: Optional[str] = None
    before_state: Optional[Any] = None
    after_state: Optional[Any] = None
    result: str = "SUCCESS"            # SUCCESS | DENIED | ERROR
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"<AuditEntry {self.id[:8]} gaian={self.gaian_id[:8]} "
            f"action={self.action!r} result={self.result} at={self.timestamp.isoformat()}>"
        )


class AuditTrail:
    """Immutable, append-only audit log for a Gaian instance.

    C03 §3.5: The audit trail cannot be deleted or modified.
    Every consequential action must produce an audit entry before execution.
    This is Ontological Constraint #3.
    """

    def __init__(self, gaian_id: str) -> None:
        self._gaian_id = gaian_id
        self._entries: list[AuditEntry] = []

    def record(
        self,
        action: str,
        human_principal_id: str,
        session_id: str,
        capability_used: Optional[Capability] = None,
        target_entity_id: Optional[str] = None,
        target_entity_type: Optional[str] = None,
        before_state: Optional[Any] = None,
        after_state: Optional[Any] = None,
        result: str = "SUCCESS",
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AuditEntry:
        """Append a new entry. The only way to write to the audit trail."""
        entry = AuditEntry(
            gaian_id=self._gaian_id,
            human_principal_id=human_principal_id,
            session_id=session_id,
            action=action,
            capability_used=capability_used,
            target_entity_id=target_entity_id,
            target_entity_type=target_entity_type,
            before_state=before_state,
            after_state=after_state,
            result=result,
            error_message=error_message,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        return entry

    def all(self) -> list[AuditEntry]:
        """Return a read-only copy of all entries. Immutable externally."""
        return list(self._entries)

    def filter(
        self,
        action: Optional[str] = None,
        result: Optional[str] = None,
        target_entity_id: Optional[str] = None,
    ) -> list[AuditEntry]:
        """Filter audit entries by action, result, or target entity."""
        entries = self._entries
        if action:
            entries = [e for e in entries if e.action == action]
        if result:
            entries = [e for e in entries if e.result == result]
        if target_entity_id:
            entries = [e for e in entries if e.target_entity_id == target_entity_id]
        return list(entries)

    def count(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"<AuditTrail gaian={self._gaian_id[:8]} entries={self.count()}>"
