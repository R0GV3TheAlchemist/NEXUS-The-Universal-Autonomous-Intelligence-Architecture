"""
intelligence.explainability — Decision Tracing & Explanation
=============================================================
Reference: NEXUS_UNIVERSAL_OS.md § Domain 2 — Explainability Layer

Every decision made by a GAIAN entity must be traceable and explainable.
DecisionTrace records the full reasoning chain; ExplanationSummary
produces human-readable output at configurable detail levels.

This is a constitutional requirement per GAIAN_LAWS.md § Transparency
and ETHICS.md § Explainability.

© 2026 Kyle Alexander Steen (The Alchemist). All rights reserved.
SPDX-License-Identifier: AGPL-3.0-only
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ExplanationLevel(Enum):
    """Detail level for an ExplanationSummary."""

    BRIEF = auto()      # One sentence
    STANDARD = auto()   # Paragraph — suitable for most users
    TECHNICAL = auto()  # Full reasoning chain with confidence values
    AUDIT = auto()      # Machine-readable, includes all metadata


@dataclass
class TraceStep:
    """A single step in a DecisionTrace."""

    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    rule_applied: Optional[str] = None    # Name of the rule or heuristic applied
    ethical_check_passed: bool = True
    timestamp_ns: int = field(default_factory=time.monotonic_ns)


class DecisionTrace:
    """
    Immutable record of the full reasoning chain for a single decision.

    Traces are created by ReasoningEngine and stored in the AuditLog.
    They are the primary mechanism for post-hoc explainability audits.

    Reference: NEXUS_UNIVERSAL_OS.md § Domain 2 — Explainability Layer
    """

    def __init__(self, decision_id: Optional[str] = None) -> None:
        self.trace_id: str = str(uuid.uuid4())
        self.decision_id: str = decision_id or str(uuid.uuid4())
        self._steps: List[TraceStep] = []
        self.final_action: Optional[Dict[str, Any]] = None
        self.overall_confidence: float = 1.0
        self.created_at_ns: int = time.monotonic_ns()

    def record_step(self, step: TraceStep) -> None:
        """
        Append a step to the trace.

        Raises:
            NotImplementedError: Stub — full implementation pending.
        """
        raise NotImplementedError("DecisionTrace.record_step: stub")

    def steps(self) -> List[TraceStep]:
        """Return all recorded steps in order."""
        return list(self._steps)

    def finalise(self, action: Dict[str, Any], confidence: float) -> None:
        """
        Seal the trace with the final action and overall confidence.

        Raises:
            NotImplementedError: Stub — full implementation pending.
        """
        raise NotImplementedError("DecisionTrace.finalise: stub")


class ExplanationSummary:
    """
    Generates human-readable explanations from a DecisionTrace.

    Output detail is controlled by ExplanationLevel.  The BRIEF level
    is safe for end-user display; AUDIT level is for system operators.

    Reference: NEXUS_UNIVERSAL_OS.md § Domain 2 — Explainability Layer
    """

    def generate(
        self,
        trace: DecisionTrace,
        level: ExplanationLevel = ExplanationLevel.STANDARD,
    ) -> str:
        """
        Generate an explanation string at the requested detail level.

        Args:
            trace: The DecisionTrace to explain.
            level: The desired ExplanationLevel.

        Returns:
            A string explanation suitable for the given level.

        Raises:
            NotImplementedError: Stub — full implementation pending.
        """
        raise NotImplementedError(
            "ExplanationSummary.generate: stub — implementation pending (NEXUS_UNIVERSAL_OS.md § Domain 2)"
        )

    def to_dict(self, trace: DecisionTrace) -> Dict[str, Any]:
        """
        Return a machine-readable dict representation of the trace.

        Raises:
            NotImplementedError: Stub — full implementation pending.
        """
        raise NotImplementedError("ExplanationSummary.to_dict: stub")
