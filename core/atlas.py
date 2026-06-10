"""
core/atlas.py
ATLAS — Geomagnetic & Earth-field data connectors.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class GeomagneticReading:
    kp_index:    float = 0.0
    ap_index:    float = 0.0
    storm_level: str   = "quiet"   # quiet | active | storm | severe
    timestamp:   str   = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "kp_index":    self.kp_index,
            "ap_index":    self.ap_index,
            "storm_level": self.storm_level,
            "timestamp":   self.timestamp,
        }


class GeomagneticReader:
    """Provides geomagnetic field readings for the GAIA pipeline."""

    _STORM_THRESHOLDS = [
        (0.0, "quiet"),
        (4.0, "active"),
        (6.0, "storm"),
        (8.0, "severe"),
    ]

    def __init__(self) -> None:
        self._history: List[GeomagneticReading] = []

    def read(self, kp: float = 0.0, ap: float = 0.0) -> GeomagneticReading:
        level = "quiet"
        for threshold, label in self._STORM_THRESHOLDS:
            if kp >= threshold:
                level = label
        reading = GeomagneticReading(kp_index=kp, ap_index=ap, storm_level=level)
        self._history.append(reading)
        return reading

    def latest(self) -> Optional[GeomagneticReading]:
        return self._history[-1] if self._history else None

    def history(self) -> List[GeomagneticReading]:
        return list(self._history)


# --------------------------------------------------------------------------- #
#  Schumann resonance helpers (used by test_atlas.py)                         #
# --------------------------------------------------------------------------- #

SCHUMANN_FUNDAMENTAL_HZ = 7.83


@dataclass
class SchumannReading:
    hz:        float = SCHUMANN_FUNDAMENTAL_HZ
    intensity: float = 1.0
    aligned:   bool  = False
    timestamp: str   = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "hz":        self.hz,
            "intensity": self.intensity,
            "aligned":   self.aligned,
            "timestamp": self.timestamp,
        }


class SchumannReader:
    """Simulates Schumann resonance readings."""

    ALIGNMENT_BAND_HZ = 0.5

    def __init__(self) -> None:
        self._history: List[SchumannReading] = []

    def read(self, hz: float = SCHUMANN_FUNDAMENTAL_HZ, intensity: float = 1.0) -> SchumannReading:
        aligned = abs(hz - SCHUMANN_FUNDAMENTAL_HZ) <= self.ALIGNMENT_BAND_HZ
        r = SchumannReading(hz=hz, intensity=intensity, aligned=aligned)
        self._history.append(r)
        return r

    def latest(self) -> Optional[SchumannReading]:
        return self._history[-1] if self._history else None
