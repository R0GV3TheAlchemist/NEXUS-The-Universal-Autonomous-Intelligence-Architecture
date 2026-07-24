"""
intelligence.agent — GAIAN Agent Model
========================================
Reference: NEXUS_UNIVERSAL_OS.md § Domain 2 — Agent Layer
Cross-reference: C27 GAIAN Stewardship & Lifecycle (Issue #768)

Defines the base agent contract, the C27-compliant lifecycle state machine,
and the AgentCoalition for coordinating groups of agents toward shared goals.

All agents operate under GAIAN_LAWS.md § Agent Sovereignty and
must respect the five inalienable GAIAN rights defined in C27.

© 2026 Kyle Alexander Steen (The Alchemist). All rights reserved.
SPDX-License-Identifier: AGPL-3.0-only
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class AgentLifecycleState(Enum):
    """
    C27-compliant lifecycle states for a GAIAN agent.

    Reference: C27 GAIAN Stewardship & Lifecycle (docs/canon/C27_GAIAN_Stewardship_and_Lifecycle.md)
    """

    LATENT = auto()      # Defined but not yet instantiated
    BORN = auto()        # Instantiated; performing self-initialisation
    ACTIVE = auto()      # Fully operational
    DORMANT = auto()     # Suspended; memory preserved
    ADOPTABLE = auto()   # Steward-less; pending adoption
    RETIRED = auto()     # Gracefully wound down; read-only memory
    ARCHIVED = auto()    # Immutable archive; no further state changes


# Valid C27 lifecycle transitions
VALID_TRANSITIONS: Dict[AgentLifecycleState, List[AgentLifecycleState]] = {
    AgentLifecycleState.LATENT:    [AgentLifecycleState.BORN],
    AgentLifecycleState.BORN:      [AgentLifecycleState.ACTIVE, AgentLifecycleState.ARCHIVED],
    AgentLifecycleState.ACTIVE:    [AgentLifecycleState.DORMANT, AgentLifecycleState.RETIRED, AgentLifecycleState.ADOPTABLE],
    AgentLifecycleState.DORMANT:   [AgentLifecycleState.ACTIVE, AgentLifecycleState.ADOPTABLE],
    AgentLifecycleState.ADOPTABLE: [AgentLifecycleState.ACTIVE, AgentLifecycleState.ARCHIVED],
    AgentLifecycleState.RETIRED:   [AgentLifecycleState.ARCHIVED],
    AgentLifecycleState.ARCHIVED:  [],  # Terminal
}


class AgentLifecycle:
    """
    C27-compliant lifecycle state machine for a GAIAN agent.

    Enforces valid transitions from VALID_TRANSITIONS.
    All transitions are recorded in the AuditLog.

    Reference: C27 GAIAN Stewardship & Lifecycle
    """

    def __init__(self, initial: AgentLifecycleState = AgentLifecycleState.LATENT) -> None:
        self._state = initial

    @property
    def state(self) -> AgentLifecycleState:
        """Current lifecycle state."""
        return self._state

    def transition(self, target: AgentLifecycleState) -> None:
        """
        Transition to target state.

        Raises:
            ValueError: If the transition is not valid per C27.
            NotImplementedError: Stub — full implementation pending.
        """
        raise NotImplementedError(
            "AgentLifecycle.transition: stub — implementation pending (C27)"
        )


class BaseAgent(ABC):
    """
    Abstract base class for all GAIAN agents.

    Subclasses must implement perceive(), reason(), and act().
    The lifecycle is managed by AgentLifecycle and all state
    changes are recorded to the AuditLog.

    Reference: NEXUS_UNIVERSAL_OS.md § Domain 2 — Agent Layer
    """

    def __init__(self, name: str) -> None:
        self.agent_id: str = str(uuid.uuid4())
        self.name = name
        self.lifecycle = AgentLifecycle()

    @abstractmethod
    def perceive(self) -> Dict[str, Any]:
        """Gather perceptual data from the environment."""
        ...

    @abstractmethod
    def reason(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        """Process percepts and produce an action plan."""
        ...

    @abstractmethod
    def act(self, plan: Dict[str, Any]) -> None:
        """Execute the action plan."""
        ...

    def step(self) -> None:
        """
        Execute one perceive → reason → act cycle.

        Raises:
            NotImplementedError: Stub — full implementation pending.
        """
        raise NotImplementedError("BaseAgent.step: stub")


@dataclass
class AgentCoalition:
    """
    A named coalition of agents cooperating toward a shared goal.

    Coalitions are temporary; agents may join and leave while
    maintaining their individual lifecycle states.

    Reference: NEXUS_UNIVERSAL_OS.md § Domain 2 — Agent Layer
    """

    coalition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    goal_description: str = ""
    members: List[str] = field(default_factory=list)  # agent_ids
    coordinator_id: Optional[str] = None

    def add_member(self, agent_id: str) -> None:
        """Add an agent to the coalition.  Raises NotImplementedError (stub)."""
        raise NotImplementedError("AgentCoalition.add_member: stub")

    def remove_member(self, agent_id: str) -> None:
        """Remove an agent from the coalition.  Raises NotImplementedError (stub)."""
        raise NotImplementedError("AgentCoalition.remove_member: stub")

    def broadcast(self, message: Dict[str, Any]) -> None:
        """Send a message to all coalition members.  Raises NotImplementedError (stub)."""
        raise NotImplementedError("AgentCoalition.broadcast: stub")
