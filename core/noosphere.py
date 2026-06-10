"""
core/noosphere.py
Noosphere — collective consciousness field modelling.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class CoherenceEventType(str, Enum):
    SPIKE     = "spike"
    DIP       = "dip"
    SUSTAINED = "sustained"
    BASELINE  = "baseline"


@dataclass
class CoherenceEvent:
    """A notable coherence change in the noospheric field."""
    event_type:  CoherenceEventType = CoherenceEventType.BASELINE
    delta:       float = 0.0
    coherence:   float = 0.5
    description: str   = ""
    timestamp:   str   = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "event_type":  self.event_type.value,
            "delta":       round(self.delta, 4),
            "coherence":   round(self.coherence, 4),
            "description": self.description,
            "timestamp":   self.timestamp,
        }


@dataclass
class NoosphericPulse:
    """A single noospheric health sample."""
    health:    float = 0.70
    coherence: float = 0.50
    timestamp: str   = field(
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
    pattern_id:  str
    description: str
    frequency:   float = 0.0
    first_seen:  str   = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_seen:   str   = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    strength:    float = 0.5

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

    _COHERENCE_SPIKE_THRESHOLD = 0.10

    def __init__(self) -> None:
        self._pulses:   List[NoosphericPulse]         = []
        self._patterns: List[CollectiveMemoryPattern] = []
        self._events:   List[CoherenceEvent]          = []

    def pulse(
        self,
        health:    float = 0.70,
        coherence: float = 0.50,
    ) -> NoosphericPulse:
        prev_coherence = self._pulses[-1].coherence if self._pulses else coherence
        p = NoosphericPulse(health=health, coherence=coherence)
        self._pulses.append(p)

        delta = coherence - prev_coherence
        if abs(delta) >= self._COHERENCE_SPIKE_THRESHOLD:
            evt_type = CoherenceEventType.SPIKE if delta > 0 else CoherenceEventType.DIP
            self._events.append(CoherenceEvent(
                event_type=evt_type,
                delta=delta,
                coherence=coherence,
                description=f"Coherence {'rose' if delta > 0 else 'fell'} by {abs(delta):.2f}",
            ))
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

    def coherence_events(self) -> List[CoherenceEvent]:
        return list(self._events)


_noosphere: Optional[NoosphereEngine] = None


def get_noosphere() -> NoosphereEngine:
    global _noosphere
    if _noosphere is None:
        _noosphere = NoosphereEngine()
    return _noosphere
