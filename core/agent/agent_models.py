"""
core/agent/agent_models.py

Data models for the Agentic Loop Architecture.
Every loop iteration is fully inspectable and auditable by the Gaian.

Canon Reference: C01 (GAIA as orchestration layer), C-SENTINEL Article 4
Issue:          #228
Version:        1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
import uuid


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class LoopStatus(Enum):
    """Runtime status of the agentic loop."""
    IDLE      = "idle"       # Not yet started
    RUNNING   = "running"    # Actively executing
    PAUSED    = "paused"     # Gaian-initiated pause
    COMPLETED = "completed"  # Goal achieved
    HALTED    = "halted"     # Hard halt condition triggered
    FAILED    = "failed"     # Unrecoverable error


class ActionStatus(Enum):
    """Result status of a single agent action."""
    SUCCESS  = "success"
    FAILURE  = "failure"
    SKIPPED  = "skipped"
    PENDING  = "pending"


class HaltReason(Enum):
    """Why the loop was hard-halted."""
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    CRITICAL_ACTION_FAILED = "critical_action_failed"
    POLICY_DENIED          = "policy_denied"
    GAIAN_REQUESTED        = "gaian_requested"
    GOAL_ACHIEVED          = "goal_achieved"
    UNHANDLED_EXCEPTION    = "unhandled_exception"


# ---------------------------------------------------------------------------
# Perception
# ---------------------------------------------------------------------------

@dataclass
class Perception:
    """
    Step 1: Perceive.
    A snapshot of everything GAIA knows at the start of a loop iteration.
    """
    goal:           str                         # What the Gaian wants to achieve
    session_id:     str
    gaian_id:       str
    ambient_signals: dict                       = field(default_factory=dict)
    session_state:  dict                        = field(default_factory=dict)
    memory_context: list[dict]                  = field(default_factory=list)
    timestamp:      datetime                    = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

@dataclass
class PlannedAction:
    """
    A single planned action within a Plan.
    Supports branching via on_success and on_failure step names.
    risk_level is an optional declarative hint for ActionGate.
    """
    name:        str
    description: str
    handler:     Callable[..., Any]             # The callable that executes this action
    args:        dict                           = field(default_factory=dict)
    on_success:  Optional[str]                  = None   # Step name to jump to on success
    on_failure:  Optional[str]                  = None   # Step name to jump to on failure
    critical:    bool                           = False  # If True, failure halts the loop
    risk_level:  Optional[str]                  = None   # low / medium / high / irreversible


@dataclass
class Plan:
    """
    Step 2: Reason.
    An ordered sequence of PlannedActions that achieve the Gaian's goal.
    Supports branching and fallback via PlannedAction.on_success / on_failure.
    """
    goal:    str
    steps:   list[PlannedAction]               = field(default_factory=list)
    plan_id: str                               = field(default_factory=lambda: str(uuid.uuid4()))

    def get_step(self, name: str) -> Optional[PlannedAction]:
        for step in self.steps:
            if step.name == name:
                return step
        return None


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------

@dataclass
class AgentAction:
    """
    Step 3: Act.
    The execution record of a single PlannedAction.
    """
    step_name:   str
    description: str
    status:      ActionStatus                  = ActionStatus.PENDING
    result:      Any                           = None
    error:       Optional[str]                 = None
    started_at:  datetime                      = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime]            = None

    def complete(self, result: Any) -> None:
        self.result     = result
        self.status     = ActionStatus.SUCCESS
        self.finished_at = datetime.now(timezone.utc)

    def fail(self, error: str) -> None:
        self.error      = error
        self.status     = ActionStatus.FAILURE
        self.finished_at = datetime.now(timezone.utc)

    def skip(self, reason: str) -> None:
        self.error       = reason
        self.status      = ActionStatus.SKIPPED
        self.finished_at = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------

@dataclass
class Observation:
    """
    Step 4: Observe.
    The result of evaluating an AgentAction's outcome.
    Determines whether the loop should continue, branch, or halt.
    """
    action:       AgentAction
    iteration:    int
    notes:        str                          = ""
    should_halt:  bool                         = False
    halt_reason:  Optional[HaltReason]         = None
    next_step:    Optional[str]                = None   # Override next step if branching
    timestamp:    datetime                     = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Loop State
# ---------------------------------------------------------------------------

@dataclass
class LoopState:
    """
    The full runtime state of an executing agentic loop.
    Always inspectable and resumable by the Gaian.

    Acceptance Criteria:
      - Loop can be paused, inspected, and resumed at any time.
      - Every iteration is logged for observability.
      - Hard halt conditions prevent runaway loops.
    """
    loop_id:       str                         = field(default_factory=lambda: str(uuid.uuid4()))
    status:        LoopStatus                  = LoopStatus.IDLE
    perception:    Optional[Perception]        = None
    plan:          Optional[Plan]              = None
    current_step:  Optional[str]               = None
    iteration:     int                         = 0
    max_iterations: int                        = 50
    observations:  list[Observation]           = field(default_factory=list)
    halt_reason:   Optional[HaltReason]        = None
    started_at:    Optional[datetime]          = None
    completed_at:  Optional[datetime]          = None

    def is_terminal(self) -> bool:
        """Return True if the loop has reached a terminal state."""
        return self.status in (
            LoopStatus.COMPLETED,
            LoopStatus.HALTED,
            LoopStatus.FAILED,
        )

    def log_observation(self, observation: Observation) -> None:
        """Append an observation to the audit trail."""
        self.observations.append(observation)
        self.iteration += 1

    def summary(self) -> dict:
        """Human-readable summary for the Gaian."""
        return {
            "loop_id":      self.loop_id,
            "status":       self.status.value,
            "goal":         self.perception.goal if self.perception else None,
            "iteration":    self.iteration,
            "current_step": self.current_step,
            "halt_reason":  self.halt_reason.value if self.halt_reason else None,
            "started_at":   self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "observations": len(self.observations),
        }
