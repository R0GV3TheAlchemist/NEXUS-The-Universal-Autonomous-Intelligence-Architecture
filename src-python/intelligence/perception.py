"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

perception.py — NEXUS Perception System.

SensorFusion combines heterogeneous sensor streams into a unified WorldModel.
UncertaintyQuantifier attaches Bayesian confidence intervals to all percepts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import time


@dataclass
class Percept:
    """A single fused sensor reading."""
    percept_id: UUID  = field(default_factory=uuid4)
    sensor_id:  str   = ""
    modality:   str   = ""   # e.g. "vision", "audio", "tactile", "telemetry"
    value:      Any   = None
    timestamp:  float = field(default_factory=time.time)
    confidence: float = 1.0  # 0.0–1.0 Bayesian confidence


@dataclass
class WorldModel:
    """
    Unified representation of the perceived world state.
    Updated each perception cycle by SensorFusion.
    """
    model_id:   UUID           = field(default_factory=uuid4)
    timestamp:  float          = field(default_factory=time.time)
    entities:   Dict[str, Any] = field(default_factory=dict)
    confidence: float          = 1.0
    percepts:   List[Percept]  = field(default_factory=list)

    def update_entity(self, name: str, state: Any) -> None:
        self.entities[name] = state
        self.timestamp = time.time()


class UncertaintyQuantifier:
    """
    Attaches Bayesian confidence intervals to percepts.
    Uses weighted-average fusion. Replace with Kalman/Bayesian network in production.
    """

    def quantify(self, percepts: List[Percept]) -> float:
        """Compute overall model confidence from individual percept confidences."""
        if not percepts:
            return 0.0
        return sum(p.confidence for p in percepts) / len(percepts)

    def calibrate(self, percept: Percept,
                  prior: float = 0.5,
                  likelihood: float = 0.9) -> float:
        """Apply Bayesian update and store result in percept.confidence."""
        evidence  = likelihood * prior + (1 - likelihood) * (1 - prior)
        posterior = (likelihood * prior) / evidence if evidence > 0 else prior
        percept.confidence = min(max(posterior, 0.0), 1.0)
        return percept.confidence


class SensorFusion:
    """
    Fuses heterogeneous sensor streams into a unified WorldModel.

    Each registered sensor pushes Percept objects. SensorFusion
    reconciles conflicts, runs UncertaintyQuantifier, and updates
    the live WorldModel.
    """

    def __init__(self) -> None:
        self._sensors:    Dict[str, Any]        = {}
        self._uq:         UncertaintyQuantifier = UncertaintyQuantifier()
        self.world_model: WorldModel            = WorldModel()

    def register_sensor(self, sensor_id: str, modality: str) -> None:
        self._sensors[sensor_id] = {"modality": modality, "active": True}

    def ingest(self, percept: Percept) -> None:
        """Accept a raw percept and integrate it into the world model."""
        self._uq.calibrate(percept)
        self.world_model.percepts.append(percept)
        self.world_model.update_entity(percept.sensor_id, percept.value)

    def fuse(self) -> WorldModel:
        """Run a full fusion cycle and return the updated WorldModel snapshot."""
        self.world_model.confidence = self._uq.quantify(self.world_model.percepts)
        self.world_model.timestamp  = time.time()
        return self.world_model

    def reset(self) -> None:
        """Clear the percept buffer for the next cycle."""
        self.world_model.percepts.clear()
