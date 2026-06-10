"""
ATLAS — Adaptive Terrain & Location Awareness System.

Provides spatial/environmental awareness to GAIA-OS, including
Schumann resonance readings via SchumannReader.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class SchumannReading:
    """A single Schumann resonance sample."""

    frequency_hz: float = 7.83
    amplitude: float = 1.0
    coherence: float = 0.5
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "frequency_hz": self.frequency_hz,
            "amplitude": self.amplitude,
            "coherence": self.coherence,
            "metadata": self.metadata,
        }


class SchumannReader:
    """Reads and caches Schumann resonance data."""

    DEFAULT_FREQUENCY = 7.83  # Hz — fundamental Schumann resonance

    def __init__(self) -> None:
        self._last_reading: Optional[SchumannReading] = None
        log.info("SchumannReader initialised (stub)")

    def read(self) -> SchumannReading:
        """Return the latest (or synthesised) Schumann reading."""
        reading = SchumannReading(frequency_hz=self.DEFAULT_FREQUENCY)
        self._last_reading = reading
        return reading

    def get_last_reading(self) -> Optional[SchumannReading]:
        return self._last_reading

    def get_coherence(self) -> float:
        if self._last_reading is None:
            self.read()
        return self._last_reading.coherence  # type: ignore[union-attr]


class Atlas:
    """Adaptive Terrain & Location Awareness System."""

    def __init__(self) -> None:
        self.schumann_reader = SchumannReader()
        log.info("Atlas initialised (stub)")

    def get_schumann_coherence(self) -> float:
        return self.schumann_reader.get_coherence()

    def to_dict(self) -> dict:
        return {"schumann_reader": "SchumannReader"}


_atlas: Optional[Atlas] = None


def get_atlas() -> Atlas:
    global _atlas
    if _atlas is None:
        _atlas = Atlas()
    return _atlas
