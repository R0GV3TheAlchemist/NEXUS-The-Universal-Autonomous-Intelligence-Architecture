# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
Meta-Cognition Layer — Capability Domain 17

Intelligence observing itself.

GAIA asks: "Why was I wrong? Which subsystem failed?
            Which assumptions caused error? What should change?"

Pipeline:
  Planner → Reasoner → Meta Observer → Performance Analysis → Architecture Adaptation

Distinct from intelligence itself — this is the Self-Reflection Layer.

Related: Issue #753 Tier 3 Domain 17 (Meta-Cognition Layer)
Partial existing: core/moral/matrix.py, alignment scoring
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class ReflectionTrigger(str, Enum):
    PREDICTION_ERROR = "PREDICTION_ERROR"     # Output differed from reality
    USER_CORRECTION = "USER_CORRECTION"       # User indicated error
    SENTINEL_FINDING = "SENTINEL_FINDING"     # SENTINEL flagged an issue
    SCHEDULED_REVIEW = "SCHEDULED_REVIEW"     # Periodic self-review
    EMERGENCE_SIGNAL = "EMERGENCE_SIGNAL"     # Emergence engine flagged anomaly


@dataclass
class MetaCognitionEvent:
    """
    A self-reflection event — GAIA examining its own performance.
    """
    event_id: str
    trigger: ReflectionTrigger
    subsystem: str            # Which GAIA subsystem is being examined
    error_description: str
    root_cause_hypothesis: Optional[str] = None
    assumption_failures: list[str] = field(default_factory=list)
    recommended_adaptations: list[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False


class MetaCognitionLayer:
    """
    GAIA's self-reflection and architecture adaptation layer.

    TODO (Issue #753 Domain 17):
    - Integrate with core/moral/matrix.py alignment scoring
    - Implement performance analysis across session history
    - Implement architecture adaptation proposal generator
    - Feed findings to Emergence Engine (Domain 16)
    - Cross-reference with Uncertainty Layer (Domain 20)
    """

    def reflect(
        self,
        trigger: ReflectionTrigger,
        subsystem: str,
        error_description: str,
        context: Optional[dict] = None,
    ) -> MetaCognitionEvent:
        """
        Initiate a self-reflection event.
        TODO: implement — Issue #753 Domain 17
        """
        raise NotImplementedError("MetaCognitionLayer.reflect — Issue #753 Domain 17")

    def propose_adaptation(self, event: MetaCognitionEvent) -> list[str]:
        """
        Generate architecture adaptation recommendations from a reflection event.
        TODO: implement
        """
        raise NotImplementedError("MetaCognitionLayer.propose_adaptation — Issue #753 Domain 17")
