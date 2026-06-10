"""
core/noosphere.py
Noosphere — collective consciousness field modelling.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class NoosphericPulse:
    """A single noospheric health sample."""
    health:    float = 0.70
    coherence: float = 0.50
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "health":    round(self.health, 4),
            "coherence": round(self.coherence, 4),
            "timestamp": self.timestamp,
        }


@dataclass
class CollectiveMemoryPattern:
    """A recurring pattern detected in the collective noospheric field."""
    pattern_id:   str
    description:  str
    frequency:    float = 0.0
    first_seen:   str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_seen:    str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    strength:     float = 0.5

    def to_dict(self) -> dict:
        return {
            "pattern_id":  self.pattern_id,
            "description": self.description,
            "frequency":   round(self.frequency, 4),
            "first_seen":  self.first_seen,
            "last_seen":   self.last_seen,
            "strength":    round(self.strength, 4),
        }


class NoosphereEngine:
    """Models and tracks the collective consciousness field."""

    def __init__(self) -> None:
        self._pulses:   List[NoosphericPulse]        = []
        self._patterns: List[CollectiveMemoryPattern] = []

    def pulse(self, health: float = 0.70, coherence: float = 0.50) -> NoosphericPulse:
        p = NoosphericPulse(health=health, coherence=coherence)
        self._pulses.append(p)
        return p

    def record_pattern(
        self,
        pattern_id:  str,
        description: str,
        frequency:   float = 0.0,
        strength:    float = 0.5,
    ) -> CollectiveMemoryPattern:
        cmp = CollectiveMemoryPattern(
            pattern_id=pattern_id,
            description=description,
            frequency=frequency,
            strength=strength,
        )
        self._patterns.append(cmp)
        return cmp

    def latest_pulse(self) -> Optional[NoosphericPulse]:
        return self._pulses[-1] if self._pulses else None

    def patterns(self) -> List[CollectiveMemoryPattern]:
        return list(self._patterns)
