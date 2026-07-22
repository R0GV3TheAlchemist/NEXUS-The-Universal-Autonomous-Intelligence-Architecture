"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cognitive_kernel.py — NEXUS Cognitive Kernel.

Manages a goal stack, drives the reasoning engine tick loop,
and maintains a cryptographically hash-chained audit log.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import hashlib, json, time


class GoalStatus(Enum):
    PENDING   = auto()
    ACTIVE    = auto()
    SUCCEEDED = auto()
    FAILED    = auto()
    DEFERRED  = auto()


@dataclass
class Goal:
    """A single goal on the cognitive stack."""
    goal_id:     UUID           = field(default_factory=uuid4)
    description: str            = ""
    priority:    int            = 0
    status:      GoalStatus     = GoalStatus.PENDING
    context:     Dict[str, Any] = field(default_factory=dict)
    created_at:  float          = field(default_factory=time.time)


@dataclass
class AuditEntry:
    """One entry in the cryptographic audit log."""
    entry_id:      UUID  = field(default_factory=uuid4)
    timestamp:     float = field(default_factory=time.time)
    goal_id:       UUID  = field(default_factory=uuid4)
    action:        str   = ""
    result:        str   = ""
    previous_hash: str   = ""
    hash:          str   = ""

    def compute_hash(self) -> str:
        payload = json.dumps({
            "entry_id":      str(self.entry_id),
            "timestamp":     self.timestamp,
            "goal_id":       str(self.goal_id),
            "action":        self.action,
            "result":        self.result,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()


class GoalStack:
    """Priority-ordered stack of cognitive goals."""

    def __init__(self) -> None:
        self._goals: List[Goal] = []

    def push(self, goal: Goal) -> None:
        self._goals.append(goal)
        self._goals.sort(key=lambda g: -g.priority)

    def pop(self) -> Optional[Goal]:
        return self._goals.pop(0) if self._goals else None

    def peek(self) -> Optional[Goal]:
        return self._goals[0] if self._goals else None

    def __len__(self) -> int:
        return len(self._goals)


class AuditLog:
    """Append-only, SHA-256 hash-chained audit log for all cognitive decisions."""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def append(self, goal_id: UUID, action: str, result: str) -> AuditEntry:
        prev_hash = self._entries[-1].hash if self._entries else ""
        entry = AuditEntry(
            goal_id=goal_id, action=action,
            result=result, previous_hash=prev_hash
        )
        entry.hash = entry.compute_hash()
        self._entries.append(entry)
        return entry

    def verify(self) -> bool:
        """Verify chain integrity. Returns True if unmodified."""
        for i, entry in enumerate(self._entries):
            if entry.hash != entry.compute_hash():
                return False
            if i > 0 and entry.previous_hash != self._entries[i - 1].hash:
                return False
        return True

    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


class ReasoningEngine:
    """
    Stub reasoning engine. In production, plugs into NEXUS inference
    backends (symbolic, neural, or hybrid).
    """

    def reason(self, goal: Goal) -> str:
        """Process a goal and return an action string. Override in subclasses."""
        raise NotImplementedError("ReasoningEngine.reason() must be implemented")


class CognitiveKernel:
    """
    The NEXUS Cognitive Kernel drives the goal-directed reasoning loop.

    Each tick: pop top goal → reason → log → emit action.
    """

    def __init__(self, reasoning_engine: ReasoningEngine) -> None:
        self.goal_stack = GoalStack()
        self.audit_log  = AuditLog()
        self._engine    = reasoning_engine

    def push_goal(self, goal: Goal) -> None:
        goal.status = GoalStatus.PENDING
        self.goal_stack.push(goal)

    def tick(self) -> Optional[AuditEntry]:
        """Execute one reasoning cycle. Returns the audit entry or None."""
        goal = self.goal_stack.pop()
        if goal is None:
            return None
        goal.status = GoalStatus.ACTIVE
        try:
            action = self._engine.reason(goal)
            goal.status = GoalStatus.SUCCEEDED
            return self.audit_log.append(goal.goal_id, action, "SUCCEEDED")
        except Exception as exc:
            goal.status = GoalStatus.FAILED
            return self.audit_log.append(goal.goal_id, "FAILED", str(exc))

    def is_audit_intact(self) -> bool:
        return self.audit_log.verify()
