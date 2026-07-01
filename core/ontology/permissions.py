# core/ontology/permissions.py
# Rewritten to match the test contract in tests/ontology/test_permissions.py
# PermissionTier is imported from entities.py (OBSERVER/COLLABORATOR/STEWARD/SOVEREIGN)
# AuditTrail.record() accepts action, human_principal_id, session_id, result, target_entity_id
# PermissionEnvelope.has() / require() / grant() / revoke() use Capability enum

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .entities import PermissionTier


# ---------------------------------------------------------------------------
# Capability
# ---------------------------------------------------------------------------

class Capability(str, Enum):
    """All capabilities a GAIA agent may be granted (C03 §3.3)."""
    READ_ENTITY           = "read_entity"
    WRITE_ENTITY          = "write_entity"
    DELETE_ENTITY         = "delete_entity"
    MANAGE_ATLAS_NODE     = "manage_atlas_node"
    INVOKE_SENTINEL       = "invoke_sentinel"
    ISSUE_HALT            = "issue_halt"
    MODIFY_STATE          = "modify_state"
    DEGRADE_ATLAS_NODE    = "degrade_atlas_node"
    BROADCAST_COLLECTIVE  = "broadcast_collective"
    OVERRIDE_CANON        = "override_canon"
    EXPORT_DATA           = "export_data"
    REVOKE_GAIAN          = "revoke_gaian"


# Tier → capability map (C03 §3.4)
PERMISSION_MAP: Dict[PermissionTier, set] = {
    PermissionTier.OBSERVER: {
        Capability.READ_ENTITY,
    },
    PermissionTier.COLLABORATOR: {
        Capability.READ_ENTITY,
        Capability.WRITE_ENTITY,
        Capability.EXPORT_DATA,
    },
    PermissionTier.STEWARD: {
        Capability.READ_ENTITY,
        Capability.WRITE_ENTITY,
        Capability.DELETE_ENTITY,
        Capability.EXPORT_DATA,
        Capability.INVOKE_SENTINEL,
        Capability.ISSUE_HALT,
        Capability.MODIFY_STATE,
        Capability.MANAGE_ATLAS_NODE,
    },
    PermissionTier.SOVEREIGN: set(Capability),
}


def has_permission(tier: PermissionTier, capability: Capability) -> bool:
    """Return True if the given tier grants the given capability."""
    return capability in PERMISSION_MAP.get(tier, set())


# ---------------------------------------------------------------------------
# PermissionDeniedError
# ---------------------------------------------------------------------------

class PermissionDeniedError(PermissionError):
    """
    Raised when a principal attempts an action that exceeds their
    PermissionTier or lacks the required Capability.
    """

    def __init__(
        self,
        message: str = "Permission denied",
        *,
        principal: Optional[str] = None,
        capability: Optional[Capability] = None,
        tier: Optional[PermissionTier] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.principal = principal
        self.capability = capability
        self.tier = tier
        self.context = context or {}

    def __repr__(self) -> str:
        return (
            f"PermissionDeniedError("
            f"principal={self.principal!r}, "
            f"capability={self.capability}, "
            f"tier={self.tier})"
        )


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    """
    One auditable event in the GAIA permission system.

    Fields match the test contract:
      action            — string label for the event
      human_principal_id— HP identity performing the action
      session_id        — session context
      result            — outcome string e.g. "SUCCESS", "DENIED"
      target_entity_id  — entity the action was performed on
      context           — arbitrary extra metadata
      timestamp         — unix epoch float
    """
    action: str
    human_principal_id: Optional[str] = None
    session_id: Optional[str] = None
    result: Optional[str] = None
    target_entity_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "human_principal_id": self.human_principal_id,
            "session_id": self.session_id,
            "result": self.result,
            "target_entity_id": self.target_entity_id,
            "context": self.context,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# AuditTrail
# ---------------------------------------------------------------------------

class AuditTrail:
    """
    An ordered, append-only trail of AuditEntry records.

    Interface contract (from tests/ontology/test_permissions.py):
      trail.record(action=..., human_principal_id=..., session_id=...,
                   result=..., target_entity_id=...)
      trail.count()  → int
      trail.all()    → List[AuditEntry] (copy)
      trail.filter(result=..., target_entity_id=...)  → List[AuditEntry]
    """

    def __init__(
        self,
        *,
        gaian_id: Optional[str] = None,
        gaianid: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.gaian_id: Optional[str] = gaian_id or gaianid
        self._entries: List[AuditEntry] = []

    def record(
        self,
        action: str,
        human_principal_id: Optional[str] = None,
        session_id: Optional[str] = None,
        result: Optional[str] = None,
        target_entity_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AuditEntry:
        """
        Construct and append an AuditEntry in one call.
        Returns the new entry.
        """
        entry = AuditEntry(
            action=action,
            human_principal_id=human_principal_id,
            session_id=session_id,
            result=result,
            target_entity_id=target_entity_id,
            context=context or {},
        )
        self._entries.append(entry)
        return entry

    def append(self, entry: AuditEntry) -> None:
        """Append a pre-constructed AuditEntry."""
        self._entries.append(entry)

    def all(self) -> List[AuditEntry]:
        """Return a shallow copy of all entries."""
        return list(self._entries)

    def count(self) -> int:
        """Return the number of entries in the trail."""
        return len(self._entries)

    def filter(
        self,
        *,
        action: Optional[str] = None,
        human_principal_id: Optional[str] = None,
        result: Optional[str] = None,
        target_entity_id: Optional[str] = None,
        **kwargs: Any,
    ) -> List[AuditEntry]:
        """Return entries matching all supplied criteria."""
        res = self._entries
        if action is not None:
            res = [e for e in res if e.action == action]
        if human_principal_id is not None:
            res = [e for e in res if e.human_principal_id == human_principal_id]
        if result is not None:
            res = [e for e in res if e.result == result]
        if target_entity_id is not None:
            res = [e for e in res if e.target_entity_id == target_entity_id]
        return res

    def denied(self) -> List[AuditEntry]:
        """Return all entries with result == 'DENIED'."""
        return self.filter(result="DENIED")

    def to_list(self) -> List[Dict[str, Any]]:
        """Serialise all entries to a list of dicts."""
        return [e.to_dict() for e in self._entries]

    def __len__(self) -> int:
        return len(self._entries)


# ---------------------------------------------------------------------------
# PermissionEnvelope
# ---------------------------------------------------------------------------

class PermissionEnvelope:
    """
    The complete permission context for a single principal (C03 §3.5).

    Constructor accepts:
      gaian_id / gaianid     — GAIAN identity
      human_principal_id     — HP identity
      session_id             — session context
      tier                   — PermissionTier (from entities.py)

    Interface:
      .has(capability)       — bool check (no raise)
      .require(capability)   — raises PermissionDeniedError if missing
      .grant(capability)     — add extra capability
      .revoke(capability)    — remove capability
    """

    def __init__(
        self,
        principal: Optional[str] = None,
        tier: Optional[PermissionTier] = None,
        *,
        gaian_id: Optional[str] = None,
        gaianid: Optional[str] = None,
        human_principal_id: Optional[str] = None,
        session_id: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None,
        **kwargs: Any,
    ) -> None:
        resolved_gaian_id = gaian_id or gaianid
        self.gaian_id: Optional[str] = resolved_gaian_id
        self.human_principal_id: Optional[str] = human_principal_id
        self.session_id: Optional[str] = session_id
        self.principal: str = principal or resolved_gaian_id or ""
        self.tier: PermissionTier = tier or PermissionTier.OBSERVER
        self._extra_grants: set = set()
        self._revocations: set = set()
        if capabilities:
            for cap in capabilities:
                self._extra_grants.add(cap)
        self.audit_trail: AuditTrail = AuditTrail(gaian_id=self.gaian_id)

    @property
    def capabilities(self) -> set:
        """Effective capabilities: tier map + grants − revocations."""
        base = PERMISSION_MAP.get(self.tier, set())
        return (base | self._extra_grants) - self._revocations

    def has(self, capability: Capability, resource: Optional[str] = None) -> bool:
        """
        Check if this principal has the given capability.
        Records the check in the audit trail.
        """
        granted = capability in self.capabilities
        self.audit_trail.record(
            action=capability.value,
            human_principal_id=self.human_principal_id,
            session_id=self.session_id,
            result="GRANTED" if granted else "DENIED",
            target_entity_id=resource,
        )
        return granted

    # Backwards-compat alias used by runtime.py and older callers
    def can(self, capability: Capability, resource: Optional[str] = None) -> bool:
        return self.has(capability, resource=resource)

    def require(self, capability: Capability, resource: Optional[str] = None) -> None:
        """
        Assert that this principal has the given capability.
        Raises PermissionDeniedError if not.
        """
        if not self.has(capability, resource=resource):
            raise PermissionDeniedError(
                f"{self.principal!r} lacks {capability.value} (tier={self.tier.name})",
                principal=self.principal,
                capability=capability,
                tier=self.tier,
                context={"resource": resource},
            )

    def grant(self, capability: Capability) -> "PermissionEnvelope":
        """Grant an additional capability beyond the tier baseline."""
        self._extra_grants.add(capability)
        self._revocations.discard(capability)
        return self

    def revoke(self, capability: Capability) -> "PermissionEnvelope":
        """Revoke a capability (overrides both tier and extra grants)."""
        self._revocations.add(capability)
        self._extra_grants.discard(capability)
        return self

    @classmethod
    def for_principal(
        cls,
        principal: str,
        tier: PermissionTier,
    ) -> "PermissionEnvelope":
        """Factory: construct a PermissionEnvelope for a principal at the given tier."""
        return cls(principal=principal, tier=tier)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "principal": self.principal,
            "gaian_id": self.gaian_id,
            "human_principal_id": self.human_principal_id,
            "session_id": self.session_id,
            "tier": self.tier.name,
            "capabilities": sorted([c.value for c in self.capabilities]),
            "extra_grants": [c.value for c in self._extra_grants],
            "revocations": [c.value for c in self._revocations],
        }
