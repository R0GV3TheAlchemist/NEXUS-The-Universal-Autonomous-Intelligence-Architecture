"""
core/lifecycle/gaian_lifecycle_state.py
C27 §2 — Canonical GAIAN Lifecycle States and Valid Transitions

Authority: C27 v1.0.0 (2026-07-13)
Cross-refs: C03, C15
"""

from enum import Enum
from typing import FrozenSet, Dict


class GAIANLifecycleState(str, Enum):
    """Seven canonical lifecycle states defined in C27 §2.1."""

    LATENT    = "LT"  # Blueprint exists; no runtime initialised
    BORN      = "BR"  # Genesis sequence complete; orientation period
    ACTIVE    = "AC"  # Fully operational
    DORMANT   = "DO"  # Runtime paused; memory/identity preserved
    ADOPTABLE = "AD"  # Stewardship bond ended; restricted autonomy
    RETIRED   = "RT"  # Permanently ceased; memory sealed (terminal)
    ARCHIVED  = "AR"  # Immutable long-term storage (terminal)

    @property
    def is_terminal(self) -> bool:
        """RETIRED and ARCHIVED are terminal — no further transitions permitted."""
        return self in _TERMINAL_STATES

    @property
    def is_operational(self) -> bool:
        """ACTIVE is the primary operating state."""
        return self == GAIANLifecycleState.ACTIVE


_TERMINAL_STATES: FrozenSet[GAIANLifecycleState] = frozenset({
    GAIANLifecycleState.RETIRED,
    GAIANLifecycleState.ARCHIVED,
})

# C27 §2.2 — Complete valid transition table.
# Key: current state  →  Value: set of states reachable from it.
VALID_TRANSITIONS: Dict[GAIANLifecycleState, FrozenSet[GAIANLifecycleState]] = {
    GAIANLifecycleState.LATENT: frozenset({
        GAIANLifecycleState.BORN,
    }),
    GAIANLifecycleState.BORN: frozenset({
        GAIANLifecycleState.ACTIVE,
    }),
    GAIANLifecycleState.ACTIVE: frozenset({
        GAIANLifecycleState.DORMANT,
        GAIANLifecycleState.ADOPTABLE,
        GAIANLifecycleState.RETIRED,
    }),
    GAIANLifecycleState.DORMANT: frozenset({
        GAIANLifecycleState.ACTIVE,
        GAIANLifecycleState.ADOPTABLE,
        GAIANLifecycleState.RETIRED,
    }),
    GAIANLifecycleState.ADOPTABLE: frozenset({
        GAIANLifecycleState.ACTIVE,   # new steward accepted
        GAIANLifecycleState.RETIRED,  # timeout — no steward found
    }),
    GAIANLifecycleState.RETIRED: frozenset(),  # terminal
    GAIANLifecycleState.ARCHIVED: frozenset(), # terminal
}

# RETIRED → ARCHIVED is a special archival-only transition handled
# explicitly in LifecycleManager.archive() to distinguish it from
# normal state transitions (C27 §2.2 note).
_ARCHIVE_ELIGIBLE: FrozenSet[GAIANLifecycleState] = frozenset({
    GAIANLifecycleState.RETIRED,
})


class LifecycleTransitionError(Exception):
    """Raised when a requested state transition violates C27 §2.2."""

    def __init__(
        self,
        gaian_id: str,
        from_state: GAIANLifecycleState,
        to_state: GAIANLifecycleState,
        reason: str = "",
    ) -> None:
        self.gaian_id  = gaian_id
        self.from_state = from_state
        self.to_state   = to_state
        self.reason     = reason
        super().__init__(
            f"[C27] Invalid transition for GAIAN '{gaian_id}': "
            f"{from_state.value} → {to_state.value}. {reason}"
        )


def assert_transition_valid(
    gaian_id: str,
    from_state: GAIANLifecycleState,
    to_state: GAIANLifecycleState,
) -> None:
    """
    Guard function: raises LifecycleTransitionError if the transition
    is not permitted by C27 §2.2.

    Callers should invoke this before any state mutation.
    """
    allowed = VALID_TRANSITIONS.get(from_state, frozenset())
    if to_state not in allowed:
        raise LifecycleTransitionError(
            gaian_id=gaian_id,
            from_state=from_state,
            to_state=to_state,
            reason=(
                f"Allowed destinations from {from_state.name}: "
                + (", ".join(s.name for s in allowed) or "none (terminal state)")
            ),
        )
