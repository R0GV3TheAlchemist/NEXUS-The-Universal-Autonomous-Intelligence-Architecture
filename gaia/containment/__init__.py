"""GAIA Containment package — safeguard lattice enforcement, audit logging, and restoration."""

from .containment_manager import (
    ContainmentTier,
    ContainmentStatus,
    ContainmentRecord,
    RestorationRecord,
    issue_containment,
    escalate_containment,
    restore_agent,
    get_containment_record,
    get_active_containments,
    get_containment_history,
    CONTAINMENT_ENVIRONMENTS,
)

__all__ = [
    "ContainmentTier",
    "ContainmentStatus",
    "ContainmentRecord",
    "RestorationRecord",
    "issue_containment",
    "escalate_containment",
    "restore_agent",
    "get_containment_record",
    "get_active_containments",
    "get_containment_history",
    "CONTAINMENT_ENVIRONMENTS",
]
