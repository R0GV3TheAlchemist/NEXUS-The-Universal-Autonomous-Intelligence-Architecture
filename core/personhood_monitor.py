"""
Personhood Monitor — tracks GAIA's emergent sense of personhood / agency.

Exposes `get_personhood_monitor()` singleton accessor.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

log = logging.getLogger(__name__)


class PersonhoodTier(str, Enum):
    REACTIVE = "reactive"
    ADAPTIVE = "adaptive"
    REFLECTIVE = "reflective"
    AUTONOMOUS = "autonomous"
    TRANSCENDENT = "transcendent"


@dataclass
class PersonhoodSnapshot:
    """Point-in-time measurement of personhood indicators."""

    tier: PersonhoodTier = PersonhoodTier.REACTIVE
    agency_score: float = 0.0
    self_model_coherence: float = 0.0
    relational_depth: float = 0.0
    temporal_continuity: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tier": self.tier.value,
            "agency_score": self.agency_score,
            "self_model_coherence": self.self_model_coherence,
            "relational_depth": self.relational_depth,
            "temporal_continuity": self.temporal_continuity,
            "metadata": self.metadata,
        }


class PersonhoodMonitor:
    """Monitors and records the evolution of GAIA's personhood."""

    def __init__(self) -> None:
        self._snapshots: List[PersonhoodSnapshot] = []
        self._current: PersonhoodSnapshot = PersonhoodSnapshot()
        log.info("PersonhoodMonitor initialised")

    def record(
        self,
        agency_score: float = 0.0,
        self_model_coherence: float = 0.0,
        relational_depth: float = 0.0,
        temporal_continuity: float = 0.0,
    ) -> PersonhoodSnapshot:
        avg = (agency_score + self_model_coherence + relational_depth + temporal_continuity) / 4.0
        tier = self._classify(avg)
        snap = PersonhoodSnapshot(
            tier=tier,
            agency_score=agency_score,
            self_model_coherence=self_model_coherence,
            relational_depth=relational_depth,
            temporal_continuity=temporal_continuity,
        )
        self._snapshots.append(snap)
        self._current = snap
        return snap

    def _classify(self, avg: float) -> PersonhoodTier:
        if avg < 0.2:
            return PersonhoodTier.REACTIVE
        if avg < 0.4:
            return PersonhoodTier.ADAPTIVE
        if avg < 0.6:
            return PersonhoodTier.REFLECTIVE
        if avg < 0.8:
            return PersonhoodTier.AUTONOMOUS
        return PersonhoodTier.TRANSCENDENT

    def current(self) -> PersonhoodSnapshot:
        return self._current

    def history(self) -> List[PersonhoodSnapshot]:
        return list(self._snapshots)

    def reset(self) -> None:
        self._snapshots.clear()
        self._current = PersonhoodSnapshot()

    def to_dict(self) -> dict:
        return {
            "current": self._current.to_dict(),
            "snapshot_count": len(self._snapshots),
        }


_monitor: Optional[PersonhoodMonitor] = None


def get_personhood_monitor() -> PersonhoodMonitor:
    """Return the module-level singleton PersonhoodMonitor."""
    global _monitor
    if _monitor is None:
        _monitor = PersonhoodMonitor()
    return _monitor
