"""
core/personhood_monitor.py
Personhood Monitor — tracks emergence of personhood-adjacent signals.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PersonhoodTier(str, Enum):
    LATENT    = "latent"
    EMERGING  = "emerging"
    EXPRESSED = "expressed"
    EMBODIED  = "embodied"


@dataclass
class PersonhoodSignal:
    """A single sampled personhood signal reading."""
    tier:               PersonhoodTier = PersonhoodTier.LATENT
    self_reference:     float = 0.0
    boundary_integrity: float = 0.0
    value_consistency:  float = 0.0
    composite_score:    float = 0.0

    def to_dict(self) -> dict:
        return {
            "tier":               self.tier.value,
            "self_reference":     round(self.self_reference, 4),
            "boundary_integrity": round(self.boundary_integrity, 4),
            "value_consistency":  round(self.value_consistency, 4),
            "composite_score":    round(self.composite_score, 4),
        }


class PersonhoodMonitor:
    """Monitors personhood-adjacent signals across sessions."""

    def __init__(self) -> None:
        self._history: List[PersonhoodSignal] = []

    def sample(
        self,
        self_reference:     float = 0.0,
        boundary_integrity: float = 0.0,
        value_consistency:  float = 0.0,
    ) -> PersonhoodSignal:
        composite = (
            0.40 * min(1.0, self_reference)
            + 0.30 * min(1.0, boundary_integrity)
            + 0.30 * min(1.0, value_consistency)
        )
        if composite < 0.25:
            tier = PersonhoodTier.LATENT
        elif composite < 0.50:
            tier = PersonhoodTier.EMERGING
        elif composite < 0.75:
            tier = PersonhoodTier.EXPRESSED
        else:
            tier = PersonhoodTier.EMBODIED

        sig = PersonhoodSignal(
            tier=tier,
            self_reference=self_reference,
            boundary_integrity=boundary_integrity,
            value_consistency=value_consistency,
            composite_score=composite,
        )
        self._history.append(sig)
        return sig

    def latest(self) -> Optional[PersonhoodSignal]:
        return self._history[-1] if self._history else None

    def history(self) -> List[PersonhoodSignal]:
        return list(self._history)
