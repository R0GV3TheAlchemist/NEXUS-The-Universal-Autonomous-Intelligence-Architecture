"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

agent.py — NEXUS Agent Framework.

BaseAgent, AgentLifecycle state machine, and AgentCoalition for
collaborative multi-agent problem solving.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional
from uuid import UUID, uuid4
import time


class AgentState(Enum):
    SPAWNED     = auto()
    ACTIVE      = auto()
    HIBERNATING = auto()
    TERMINATED  = auto()


@dataclass
class AgentLifecycle:
    """Tracks lifecycle state transitions of an agent."""
    current_state: AgentState  = AgentState.SPAWNED
    history:       List[tuple] = field(default_factory=list)

    def transition(self, new_state: AgentState) -> None:
        self.history.append((self.current_state, new_state, time.time()))
        self.current_state = new_state


class BaseAgent(ABC):
    """
    Abstract base for all NEXUS agents.

    Concrete agents implement perceive(), decide(), and act().
    Lifecycle transitions are managed by AgentLifecycle.
    """

    def __init__(self, name: str) -> None:
        self.agent_id:  UUID              = uuid4()
        self.name:      str               = name
        self.lifecycle: AgentLifecycle    = AgentLifecycle()
        self._coalition: Optional[AgentCoalition] = None

    @abstractmethod
    def perceive(self, world_state: dict) -> dict:
        """Process incoming world state and return percepts."""
        ...

    @abstractmethod
    def decide(self, percepts: dict) -> str:
        """Select an action given current percepts."""
        ...

    @abstractmethod
    def act(self, action: str) -> None:
        """Execute the selected action."""
        ...

    def run_cycle(self, world_state: dict) -> str:
        """Execute one full perceive → decide → act cycle."""
        self.lifecycle.transition(AgentState.ACTIVE)
        percepts = self.perceive(world_state)
        action   = self.decide(percepts)
        self.act(action)
        return action

    def join_coalition(self, coalition: AgentCoalition) -> None:
        self._coalition = coalition
        coalition._members[self.agent_id] = self

    def leave_coalition(self) -> None:
        if self._coalition:
            self._coalition._members.pop(self.agent_id, None)
            self._coalition = None

    @property
    def state(self) -> AgentState:
        return self.lifecycle.current_state


class AgentCoalition:
    """
    A capability-gated coalition of cooperating agents.
    Coalition formation and dissolution is logged for audit.
    """

    def __init__(self, coalition_id: Optional[UUID] = None,
                 goal: str = "") -> None:
        self.coalition_id: UUID               = coalition_id or uuid4()
        self.goal:         str                = goal
        self._members:     Dict[UUID, BaseAgent] = {}
        self._log:         List[dict]         = []

    def add(self, agent: BaseAgent) -> None:
        self._members[agent.agent_id] = agent
        self._log.append({
            "event": "JOIN", "agent_id": str(agent.agent_id),
            "name": agent.name, "timestamp": time.time()
        })

    def remove(self, agent_id: UUID) -> None:
        agent = self._members.pop(agent_id, None)
        if agent:
            self._log.append({
                "event": "LEAVE", "agent_id": str(agent_id),
                "timestamp": time.time()
            })

    def members(self) -> List[BaseAgent]:
        return list(self._members.values())

    def audit_log(self) -> List[dict]:
        return list(self._log)

    def __len__(self) -> int:
        return len(self._members)
