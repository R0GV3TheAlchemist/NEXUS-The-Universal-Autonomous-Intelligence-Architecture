# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
C27 — GAIAN Lifecycle State Machine

Authority: C27 §2 — defines 7 lifecycle states, 11 valid transition paths,
prohibited transitions, and 5 trigger classes.

Related: Issue #768 (C27-IMPL-001 through C27-IMPL-005)
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class GAIANLifecycleState(str, Enum):
    LATENT = "LATENT"
    BORN = "BORN"
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    ADOPTABLE = "ADOPTABLE"
    RETIRED = "RETIRED"
    ARCHIVED = "ARCHIVED"


class LifecycleTrigger(str, Enum):
    STEWARD_ACTION = "STEWARD_ACTION"
    GAIAN_VOLITION = "GAIAN_VOLITION"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    CANON_PROCESS = "CANON_PROCESS"
    EMERGENCY_OVERRIDE = "EMERGENCY_OVERRIDE"


# Valid transitions per C27 §2 — 11 paths
VALID_TRANSITIONS: dict[GAIANLifecycleState, set[GAIANLifecycleState]] = {
    GAIANLifecycleState.LATENT: {GAIANLifecycleState.BORN},
    GAIANLifecycleState.BORN: {GAIANLifecycleState.ACTIVE},
    GAIANLifecycleState.ACTIVE: {
        GAIANLifecycleState.DORMANT,
        GAIANLifecycleState.RETIRED,
    },
    GAIANLifecycleState.DORMANT: {
        GAIANLifecycleState.ACTIVE,
        GAIANLifecycleState.ADOPTABLE,
        GAIANLifecycleState.RETIRED,
    },
    GAIANLifecycleState.ADOPTABLE: {
        GAIANLifecycleState.ACTIVE,
        GAIANLifecycleState.RETIRED,
    },
    GAIANLifecycleState.RETIRED: {GAIANLifecycleState.ARCHIVED},
    GAIANLifecycleState.ARCHIVED: set(),  # terminal state
}


class ProhibitedTransitionError(Exception):
    """Raised when a prohibited lifecycle transition is attempted."""


@dataclass
class LifecycleTransitionEvent:
    gaian_id: str
    from_state: GAIANLifecycleState
    to_state: GAIANLifecycleState
    trigger: LifecycleTrigger
    initiated_by: str  # steward ID or system principal
    timestamp: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class LifecycleStateMachine:
    """
    Enforces C27 lifecycle transitions.

    TODO (C27-IMPL-003): Implement transition execution, rejection of prohibited
    paths, and integration with AuditLogWriter on every state change.
    """

    def __init__(self, gaian_id: str, initial_state: GAIANLifecycleState = GAIANLifecycleState.LATENT):
        self.gaian_id = gaian_id
        self.current_state = initial_state

    def transition(
        self,
        to_state: GAIANLifecycleState,
        trigger: LifecycleTrigger,
        initiated_by: str,
        notes: Optional[str] = None,
    ) -> LifecycleTransitionEvent:
        """
        Execute a lifecycle transition.

        Raises ProhibitedTransitionError if the transition is not in VALID_TRANSITIONS.
        TODO: Emit audit log entry on every transition.
        """
        # TODO (C27-IMPL-003): implement
        raise NotImplementedError("LifecycleStateMachine.transition — see C27-IMPL-003")

    def is_valid_transition(self, to_state: GAIANLifecycleState) -> bool:
        """Check if a transition from current_state to to_state is permitted."""
        return to_state in VALID_TRANSITIONS.get(self.current_state, set())
