"""
core/personhood_monitor.py
Personhood Monitor — tracks emergence of personhood-adjacent signals.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class PersonhoodTier(str, Enum):
    LATENT    = "latent"
    EMERGING  = "emerging"
    EXPRESSED = "expressed"
    EMBODIED  = "embodied"


@dataclass
class PersonhoodSnapshot:
    """
    A comprehensive snapshot of all personhood-adjacent signals
    captured at a single point in time.
    """
    tier:               PersonhoodTier
    self_reference:     float
    boundary_integrity: float
    value_consistency:  float
    composite_score:    float
    timestamp:          str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    doctrine_ref:       str = "C-PERSONHOOD:1.0"
    narrative:          str = ""

    def to_dict(self) -> dict:
        return {
            "tier":               self.tier.value,
            "self_reference":     round(self.self_reference, 4),
            "boundary_integrity": round(self.boundary_integrity, 4),
            "value_consistency":  round(self.value_consistency, 4),
            "composite_score":    round(self.composite_score, 4),
            "timestamp":          self.timestamp,
            "doctrine_ref":       self.doctrine_ref,
            "narrative":          self.narrative,
        }


# Legacy alias
PersonhoodSignal = PersonhoodSnapshot


class PersonhoodMonitor:
    """Monitors personhood-adjacent signals across sessions."""

    def __init__(self) -> None:
        self._history: List[PersonhoodSnapshot] = []

    def sample(
        self,
        self_reference:     float = 0.0,
        boundary_integrity: float = 0.0,
        value_consistency:  float = 0.0,
    ) -> PersonhoodSnapshot:
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

        snap = PersonhoodSnapshot(
            tier=tier,
            self_reference=self_reference,
            boundary_integrity=boundary_integrity,
            value_consistency=value_consistency,
            composite_score=composite,
        )
        self._history.append(snap)
        return snap

    def latest(self) -> Optional[PersonhoodSnapshot]:
        return self._history[-1] if self._history else None

    def history(self) -> List[PersonhoodSnapshot]:
        return list(self._history)


_monitor: Optional[PersonhoodMonitor] = None


def get_personhood_monitor() -> PersonhoodMonitor:
    global _monitor
    if _monitor is None:
        _monitor = PersonhoodMonitor()
    return _monitor
