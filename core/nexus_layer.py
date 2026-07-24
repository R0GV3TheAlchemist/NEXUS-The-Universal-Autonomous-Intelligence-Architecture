# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
The Nexus Layer — Task Mode Router (Capability Domain 15)

🔴 CRITICAL — Most architecturally foundational new component per Issue #753.

Routes tasks based on execution philosophy:
  DC Mode  — Deterministic, mission-critical, tightly aligned, monolithic power
             (climate defense, structural engineering, safety systems)
  Marvel Mode — Emergent, multi-agent chaotic brainstorming, evolutionary algorithms
               (drug discovery, material synthesis, creative generation)

DC Mode and Marvel Mode can run simultaneously on the same hardware.
Sits above core/planner/scheduler.py as task classifier and mode router.

Related: Issue #753 Tier 2 Domain 15 (Nexus Layer — Task Mode Router)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum


class TaskMode(str, Enum):
    DC = "DC"         # Deterministic — safety, infrastructure, mission-critical
    MARVEL = "MARVEL" # Emergent — creative, exploratory, evolutionary
    HYBRID = "HYBRID" # Both modes simultaneously (different subsystems)


@dataclass
class NexusRoutingDecision:
    """
    Result of classifying a task through the Nexus Layer.
    Determines which execution philosophy and hardware allocation apply.
    """
    task_id: str
    assigned_mode: TaskMode
    confidence: float      # 0.0–1.0 — how certain the classifier is
    dc_subsystems: list[str] = None   # Which parts run in DC mode (HYBRID)
    marvel_subsystems: list[str] = None  # Which parts run in Marvel mode (HYBRID)
    reasoning: Optional[str] = None

    def __post_init__(self):
        if self.dc_subsystems is None:
            self.dc_subsystems = []
        if self.marvel_subsystems is None:
            self.marvel_subsystems = []


class NexusTaskClassifier:
    """
    Classifies an incoming task as DC, Marvel, or Hybrid.

    DC Mode signals:
    - Safety-critical flag
    - Infrastructure domain
    - Regulatory compliance requirement
    - Deterministic output required

    Marvel Mode signals:
    - Creative generation request
    - Drug/material discovery
    - Hypothesis exploration
    - Evolutionary optimization

    TODO (Issue #753 Domain 15): Implement classifier.
    Extend core/planner/scheduler.py to consume NexusRoutingDecision.
    """

    def classify(self, task: dict[str, Any]) -> NexusRoutingDecision:
        """
        Classify a task and return routing decision.
        TODO: implement — Issue #753 Domain 15
        """
        raise NotImplementedError("NexusTaskClassifier.classify — Issue #753 Domain 15")


class NexusRouter:
    """
    Routes classified tasks to appropriate execution pipelines.

    DC pipeline → deterministic, audited, safety-gated execution
    Marvel pipeline → multi-agent, evolutionary, emergent execution
    Hybrid → both pipelines simultaneously, results synthesized at completion

    TODO (Issue #753 Domain 15): Implement routing and pipeline dispatch.
    """

    def __init__(self):
        self.classifier = NexusTaskClassifier()

    def route(self, task: dict[str, Any]) -> NexusRoutingDecision:
        """Classify and route a task. TODO: implement"""
        return self.classifier.classify(task)
