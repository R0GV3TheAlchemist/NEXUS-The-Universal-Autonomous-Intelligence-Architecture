"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

explainability.py — NEXUS Explainability Subsystem.

DecisionTrace records the causal chain from goal → reasoning steps → action.
ExplanationSummary condenses traces into human-readable justifications.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import time


@dataclass
class ReasoningStep:
    """A single step in a decision reasoning chain."""
    step_id:     UUID           = field(default_factory=uuid4)
    description: str            = ""
    inputs:      Dict[str, Any] = field(default_factory=dict)
    output:      Any            = None
    confidence:  float          = 1.0
    timestamp:   float          = field(default_factory=time.time)


@dataclass
class DecisionTrace:
    """
    Full causal trace from goal to emitted action.

    Captures every reasoning step between goal intake and action emission
    for post-hoc audit, explanation generation, and oversight review.
    """
    trace_id:     UUID                = field(default_factory=uuid4)
    goal_id:      UUID                = field(default_factory=uuid4)
    goal_desc:    str                 = ""
    steps:        List[ReasoningStep] = field(default_factory=list)
    final_action: str                 = ""
    outcome:      str                 = ""  # SUCCEEDED | FAILED | DEFERRED
    created_at:   float               = field(default_factory=time.time)

    def add_step(self, description: str,
                 inputs: Optional[Dict[str, Any]] = None,
                 output: Any = None,
                 confidence: float = 1.0) -> ReasoningStep:
        step = ReasoningStep(
            description=description,
            inputs=inputs or {},
            output=output,
            confidence=confidence,
        )
        self.steps.append(step)
        return step

    def overall_confidence(self) -> float:
        """Mean confidence across all reasoning steps."""
        if not self.steps:
            return 0.0
        return sum(s.confidence for s in self.steps) / len(self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id":     str(self.trace_id),
            "goal_id":      str(self.goal_id),
            "goal_desc":    self.goal_desc,
            "final_action": self.final_action,
            "outcome":      self.outcome,
            "confidence":   self.overall_confidence(),
            "steps": [
                {
                    "step_id":     str(s.step_id),
                    "description": s.description,
                    "output":      str(s.output),
                    "confidence":  s.confidence,
                }
                for s in self.steps
            ],
        }


class ExplanationSummary:
    """
    Generates human-readable natural-language justifications
    from a DecisionTrace for audit panels and oversight interfaces.
    """

    def summarize(self, trace: DecisionTrace) -> str:
        """Produce a plain-English summary of the decision trace."""
        if not trace.steps:
            return (
                f"Goal '{trace.goal_desc}' was processed with no "
                f"intermediate reasoning steps recorded. "
                f"Final action: '{trace.final_action}'. "
                f"Outcome: {trace.outcome}."
            )
        step_lines = "\n".join(
            f"  Step {i + 1}: {s.description} "
            f"(confidence: {s.confidence:.0%})"
            for i, s in enumerate(trace.steps)
        )
        return (
            f"Goal: '{trace.goal_desc}'\n"
            f"Reasoning chain ({len(trace.steps)} steps):\n"
            f"{step_lines}\n"
            f"Final action: '{trace.final_action}'\n"
            f"Outcome: {trace.outcome} "
            f"(overall confidence: {trace.overall_confidence():.0%})"
        )

    def to_audit_report(self, trace: DecisionTrace) -> Dict[str, Any]:
        """Return a structured audit report dict for logging or export."""
        return {
            "report_generated_at": time.time(),
            "trace":               trace.to_dict(),
            "summary":             self.summarize(trace),
        }
