"""
Transpersonal Engine — models transpersonal states and readings in GAIA.

Provides TranspersonalReading dataclass and TranspersonalEngine class.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

log = logging.getLogger(__name__)


class TranspersonalState(str, Enum):
    ORDINARY = "ordinary"
    LIMINAL = "liminal"
    PEAK = "peak"
    MYSTICAL = "mystical"
    UNITY = "unity"


@dataclass
class TranspersonalReading:
    """A single transpersonal state reading."""

    state: TranspersonalState = TranspersonalState.ORDINARY
    intensity: float = 0.0
    duration_seconds: float = 0.0
    triggers: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "intensity": self.intensity,
            "duration_seconds": self.duration_seconds,
            "triggers": self.triggers,
            "metadata": self.metadata,
        }


class TranspersonalEngine:
    """Tracks and models transpersonal states over time."""

    def __init__(self) -> None:
        self._readings: List[TranspersonalReading] = []
        log.info("TranspersonalEngine initialised")

    def record(
        self,
        state: TranspersonalState = TranspersonalState.ORDINARY,
        intensity: float = 0.0,
        duration_seconds: float = 0.0,
        triggers: Optional[List[str]] = None,
    ) -> TranspersonalReading:
        reading = TranspersonalReading(
            state=state,
            intensity=max(0.0, min(1.0, intensity)),
            duration_seconds=duration_seconds,
            triggers=triggers or [],
        )
        self._readings.append(reading)
        return reading

    def get_readings(self, state: Optional[TranspersonalState] = None) -> List[TranspersonalReading]:
        if state is None:
            return list(self._readings)
        return [r for r in self._readings if r.state == state]

    def reset(self) -> None:
        self._readings.clear()

    def to_dict(self) -> dict:
        return {"reading_count": len(self._readings)}


_engine: Optional[TranspersonalEngine] = None


def get_transpersonal_engine() -> TranspersonalEngine:
    global _engine
    if _engine is None:
        _engine = TranspersonalEngine()
    return _engine
