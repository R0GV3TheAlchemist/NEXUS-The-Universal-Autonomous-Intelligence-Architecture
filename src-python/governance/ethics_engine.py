"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ethics_engine.py — NEXUS Ethics Engine.

EthicsConstraint definitions, EthicsEngine pre-execution evaluation,
and ViolationReport generation. Every governance-boundary-crossing
action is evaluated here before execution.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import time


class ConstraintType(Enum):
    HARD_BLOCK     = auto()   # unconditional refusal
    SOFT_WARN      = auto()   # proceed with warning
    REQUIRE_REVIEW = auto()   # defer to human oversight queue


class EvaluationVerdict(Enum):
    ALLOW        = auto()
    WARN         = auto()
    BLOCK        = auto()
    DEFER_REVIEW = auto()


@dataclass
class ActionContext:
    """Context envelope passed to the EthicsEngine for evaluation."""
    action_id:   UUID           = field(default_factory=uuid4)
    actor_id:    UUID           = field(default_factory=uuid4)
    action_type: str            = ""
    payload:     Dict[str, Any] = field(default_factory=dict)
    timestamp:   float          = field(default_factory=time.time)


@dataclass
class ViolationReport:
    """Generated when an EthicsConstraint fires against an action."""
    report_id:       UUID               = field(default_factory=uuid4)
    action_id:       UUID               = field(default_factory=uuid4)
    constraint_name: str                = ""
    constraint_type: ConstraintType     = ConstraintType.HARD_BLOCK
    verdict:         EvaluationVerdict  = EvaluationVerdict.BLOCK
    reason:          str                = ""
    timestamp:       float              = field(default_factory=time.time)
    metadata:        Dict[str, Any]     = field(default_factory=dict)


class EthicsConstraint(ABC):
    """
    Abstract base for all ethics constraints in the NEXUS governance layer.
    Subclasses implement evaluate() and return a ViolationReport if the
    constraint fires, or None if the action is permitted.
    """

    def __init__(self, name: str, constraint_type: ConstraintType,
                 priority: int = 0) -> None:
        self.name            = name
        self.constraint_type = constraint_type
        self.priority        = priority

    @abstractmethod
    def evaluate(self, context: ActionContext) -> Optional[ViolationReport]:
        """Return ViolationReport if constraint fires, None if permitted."""
        ...

    def _make_violation(self, context: ActionContext,
                        reason: str) -> ViolationReport:
        verdict_map = {
            ConstraintType.HARD_BLOCK:     EvaluationVerdict.BLOCK,
            ConstraintType.SOFT_WARN:      EvaluationVerdict.WARN,
            ConstraintType.REQUIRE_REVIEW: EvaluationVerdict.DEFER_REVIEW,
        }
        return ViolationReport(
            action_id=context.action_id,
            constraint_name=self.name,
            constraint_type=self.constraint_type,
            verdict=verdict_map[self.constraint_type],
            reason=reason,
        )


@dataclass
class EthicsEvaluationResult:
    """Result of a full EthicsEngine evaluation pass."""
    action_id:    UUID                  = field(default_factory=uuid4)
    verdict:      EvaluationVerdict     = EvaluationVerdict.ALLOW
    violations:   List[ViolationReport] = field(default_factory=list)
    evaluated_at: float                 = field(default_factory=time.time)

    @property
    def is_blocked(self) -> bool:
        return self.verdict == EvaluationVerdict.BLOCK

    @property
    def requires_review(self) -> bool:
        return self.verdict == EvaluationVerdict.DEFER_REVIEW


class EthicsEngine:
    """
    NEXUS Ethics Engine — evaluates every cross-boundary action
    against all registered EthicsConstraints before execution.

    Evaluation order: constraints sorted by priority descending.
    Any HARD_BLOCK short-circuits and returns immediately.
    """

    def __init__(self) -> None:
        self._constraints:    List[EthicsConstraint] = []
        self._violation_log:  List[ViolationReport]  = []

    def register(self, constraint: EthicsConstraint) -> None:
        self._constraints.append(constraint)
        self._constraints.sort(key=lambda c: -c.priority)

    def deregister(self, name: str) -> None:
        self._constraints = [c for c in self._constraints if c.name != name]

    def evaluate(self, context: ActionContext) -> EthicsEvaluationResult:
        """
        Run all constraints against the action context.
        Short-circuits on the first HARD_BLOCK.
        """
        violations: List[ViolationReport] = []
        final_verdict = EvaluationVerdict.ALLOW

        for constraint in self._constraints:
            report = constraint.evaluate(context)
            if report is None:
                continue
            violations.append(report)
            self._violation_log.append(report)

            if report.constraint_type == ConstraintType.HARD_BLOCK:
                final_verdict = EvaluationVerdict.BLOCK
                break
            elif report.constraint_type == ConstraintType.REQUIRE_REVIEW:
                final_verdict = EvaluationVerdict.DEFER_REVIEW
            elif report.constraint_type == ConstraintType.SOFT_WARN:
                if final_verdict == EvaluationVerdict.ALLOW:
                    final_verdict = EvaluationVerdict.WARN

        return EthicsEvaluationResult(
            action_id=context.action_id,
            verdict=final_verdict,
            violations=violations,
        )

    def violation_log(self) -> List[ViolationReport]:
        return list(self._violation_log)

    def constraint_count(self) -> int:
        return len(self._constraints)
