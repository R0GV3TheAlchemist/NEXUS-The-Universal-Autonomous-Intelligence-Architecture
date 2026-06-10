"""
Somatic Interface — body-signal awareness layer for GAIA.

Provides SomaticReading dataclass and SomaticInterface engine.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

log = logging.getLogger(__name__)


class SomaticChannel(str, Enum):
    BREATH = "breath"
    HEART = "heart"
    SKIN = "skin"
    MUSCLE = "muscle"
    NEURAL = "neural"


@dataclass
class SomaticReading:
    """A single somatic sensor reading."""

    channel: SomaticChannel = SomaticChannel.HEART
    value: float = 0.0
    unit: str = "normalised"
    coherence: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "channel": self.channel.value,
            "value": self.value,
            "unit": self.unit,
            "coherence": self.coherence,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class SomaticInterface:
    """Manages somatic channel readings."""

    def __init__(self) -> None:
        self._readings: List[SomaticReading] = []
        log.info("SomaticInterface initialised")

    def read(self, channel: SomaticChannel, value: float) -> SomaticReading:
        reading = SomaticReading(channel=channel, value=max(0.0, min(1.0, value)))
        self._readings.append(reading)
        return reading

    def get_readings(self, channel: Optional[SomaticChannel] = None) -> List[SomaticReading]:
        if channel is None:
            return list(self._readings)
        return [r for r in self._readings if r.channel == channel]

    def reset(self) -> None:
        self._readings.clear()

    def to_dict(self) -> dict:
        return {"reading_count": len(self._readings)}


_interface: Optional[SomaticInterface] = None


def get_somatic_interface() -> SomaticInterface:
    global _interface
    if _interface is None:
        _interface = SomaticInterface()
    return _interface
