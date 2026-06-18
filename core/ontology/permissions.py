# core/ontology/permissions.py
# C416 fix: set comprehension `{c for c in Capability}` → `set(Capability)`
# Additions: PermissionEnvelope, AuditEntry, AuditTrail, PermissionDeniedError
# These were referenced by core/ontology/__init__.py and 7 test modules
# but were never defined here during the ontology refactor.
#
# FIX (2026-06-17): PermissionEnvelope now accepts both `gaianid` AND `gaian_id`
# keyword arguments (stored as self.gaian_id) to match callers in
# core/ontology/runtime.py L150, test fixtures using gaian_id=..., and all
# downstream session integration tests. AuditTrail likewise accepts both forms.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class Capability(Enum):
    """All capabilities a GAIA agent may be granted."""
    READ_CANON            = auto()
    WRITE_MEMORY          = auto()
    DELETE_MEMORY         = auto()
    EXPORT_DATA           = auto()
    INVOKE_SENTINEL       = auto()
    ISSUE_HALT            = auto()
    MODIFY_STATE          = auto()
    DEGRADE_ATLAS_NODE    = auto()
    BROADCAST_COLLECTIVE  = auto()
    OVERRIDE_CANON        = auto()


class PermissionTier(Enum):
    """Trust tiers governing permission grants."""
    GUEST     = 0
    GAIAN     = 1
    GUARDIAN  = 2
    SOVEREIGN = 3


PERMISSION_MAP: dict[PermissionTier, set[Capability]] = {
    PermissionTier.GUEST: {
        Capability.READ_CANON,
    },
    PermissionTier.GAIAN: {
        Capability.READ_CANON,
        Capability.WRITE_MEMORY,
        Capability.EXPORT_DATA,
    },
    PermissionTier.GUARDIAN: {
        Capability.READ_CANON,
        Capability.WRITE_MEMORY,
        Capability.DELETE_MEMORY,
        Capability.EXPORT_DATA,
        Capability.INVOKE_SENTINEL,
        Capability.ISSUE_HALT,
        Capability.MODIFY_STATE,
        Capability.DEGRADE_ATLAS_NODE,
    },
    # C416 fix: `set(Capability)` replaces `{c for c in Capability}`
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
# AuditEntry — a single auditable event
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    """
    One auditable event in the GAIA permission system.
    """
    principal: str
    capability: Capability
    tier: PermissionTier
    granted: bool
    resource: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "principal": self.principal,
            "capability": self.capability.name,
            "tier": self.tier.name,
            "granted": self.granted,
            "resource": self.resource,
            "context": self.context,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# AuditTrail — an ordered sequence of AuditEntry records
# ---------------------------------------------------------------------------

class AuditTrail:
    """
    An ordered, append-only trail of AuditEntry records.

    Accepts `gaianid` or `gaian_id` keyword argument so that callers may
    tag the trail to a specific GAIAN identity using either form.
    """

    def __init__(self, *, gaianid: Optional[str] = None, gaian_id: Optional[str] = None, **kwargs: Any) -> None:
        # Accept both gaianid and gaian_id; gaian_id takes precedence if both supplied
        self.gaian_id: Optional[str] = gaian_id or gaianid
        self.entries: List[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        """Append a new AuditEntry to the trail."""
        self.entries.append(entry)

    def record(
        self,
        principal: str,
        capability: Capability,
        tier: PermissionTier,
        granted: bool,
        resource: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """
        Convenience method: construct and append an AuditEntry in one call.
        Returns the new entry.
        """
        entry = AuditEntry(
            principal=principal,
            capability=capability,
            tier=tier,
            granted=granted,
            resource=resource,
            context=context or {},
        )
        self.entries.append(entry)
        return entry

    def filter(
        self,
        *,
        principal: Optional[str] = None,
        capability: Optional[Capability] = None,
        granted: Optional[bool] = None,
        result: Optional[bool] = None,
        target: Optional[str] = None,
    ) -> List[AuditEntry]:
        """Return entries matching all supplied criteria."""
        # `result` and `target` are test-facing aliases for `granted` and `resource`
        effective_granted = granted if granted is not None else result
        effective_target = target

        res = self.entries
        if principal is not None:
            res = [e for e in res if e.principal == principal]
        if capability is not None:
            res = [e for e in res if e.capability == capability]
        if effective_granted is not None:
            res = [e for e in res if e.granted == effective_granted]
        if effective_target is not None:
            res = [e for e in res if e.resource == effective_target]
        return res

    def all(self) -> List[AuditEntry]:
        """Return a shallow copy of all entries."""
        return list(self.entries)

    def denied(self) -> List[AuditEntry]:
        """Return all denied entries."""
        return self.filter(granted=False)

    def to_list(self) -> List[Dict[str, Any]]:
        """Serialise all entries to a list of dicts."""
        return [e.to_dict() for e in self.entries]

    def __len__(self) -> int:
        return len(self.entries)


# ---------------------------------------------------------------------------
# PermissionEnvelope — a principal's complete permission context
# ---------------------------------------------------------------------------

class PermissionEnvelope:
    """
    The complete permission context for a single principal.

    Accepts both `gaianid` and `gaian_id` keyword arguments (stored as
    self.gaian_id) so that all callers work without TypeError:

        PermissionEnvelope(gaianid=..., tier=..., capabilities=[...])
        PermissionEnvelope(gaian_id=..., tier=..., capabilities=[...])
    """

    def __init__(
        self,
        principal: Optional[str] = None,
        tier: Optional[PermissionTier] = None,
        *,
        gaianid: Optional[str] = None,
        gaian_id: Optional[str] = None,
        capabilities: Optional[List[Capability]] = None,
        **kwargs: Any,
    ) -> None:
        # gaian_id (underscore) takes precedence over gaianid if both provided
        resolved_gaian_id = gaian_id or gaianid
        self.gaian_id: Optional[str] = resolved_gaian_id
        self.principal: str = principal or resolved_gaian_id or ""
        self.tier: PermissionTier = tier or PermissionTier.GAIAN
        self._extra_grants: set[Capability] = set()
        self._revocations: set[Capability] = set()
        # Allow caller to seed explicit capability list
        if capabilities:
            for cap in capabilities:
                self._extra_grants.add(cap)
        self.audit_trail: AuditTrail = AuditTrail(gaian_id=self.gaian_id)

    @property
    def capabilities(self) -> set[Capability]:
        """Effective capabilities: tier map + grants − revocations."""
        base = PERMISSION_MAP.get(self.tier, set())
        return (base | self._extra_grants) - self._revocations

    def can(self, capability: Capability, resource: Optional[str] = None) -> bool:
        """
        Check if this principal has the given capability.
        Records the check in the audit trail.
        """
        granted = capability in self.capabilities
        self.audit_trail.record(
            principal=self.principal,
            capability=capability,
            tier=self.tier,
            granted=granted,
            resource=resource,
        )
        return granted

    def require(self, capability: Capability, resource: Optional[str] = None) -> None:
        """
        Assert that this principal has the given capability.
        Raises PermissionDeniedError if not.
        """
        if not self.can(capability, resource=resource):
            raise PermissionDeniedError(
                f"{self.principal!r} lacks {capability.name} (tier={self.tier.name})",
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
            "tier": self.tier.name,
            "capabilities": [c.name for c in sorted(self.capabilities, key=lambda c: c.name)],
            "extra_grants": [c.name for c in self._extra_grants],
            "revocations": [c.name for c in self._revocations],
        }
