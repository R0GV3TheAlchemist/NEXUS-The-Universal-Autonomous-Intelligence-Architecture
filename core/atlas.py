"""
core/atlas.py
ATLAS — Geomagnetic, Schumann & Earth-field data connectors.

Full API expected by tests/test_atlas.py.
"""
from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Deque, Dict, List, Optional

try:
    import requests  # noqa: F401
    _REQUESTS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _REQUESTS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHUMANN_FUNDAMENTAL: float = 7.83
KP_QUIET:             float = 3.0
KP_MINOR_STORM:       float = 5.0
KP_MAJOR_STORM:       float = 7.0


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GeomagneticState(str, Enum):
    QUIET        = "quiet"
    UNSETTLED    = "unsettled"
    MINOR_STORM  = "minor_storm"
    MAJOR_STORM  = "major_storm"


class SchumannMode(str, Enum):
    FUNDAMENTAL = "fundamental"
    SECOND      = "second"
    THIRD       = "third"
    FOURTH      = "fourth"
    FIFTH       = "fifth"


class AtlasStatus(str, Enum):
    LIVE    = "live"
    MODELED = "modeled"
    OFFLINE = "offline"


# ---------------------------------------------------------------------------
# SchumannReader
# ---------------------------------------------------------------------------

_SCHUMANN_HARMONICS = [7.83, 14.3, 20.8, 27.3, 33.8]
_MODE_BOUNDARIES    = [
    (9.5,  SchumannMode.FUNDAMENTAL),
    (17.0, SchumannMode.SECOND),
    (24.0, SchumannMode.THIRD),
    (30.5, SchumannMode.FOURTH),
    (float("inf"), SchumannMode.FIFTH),
]


class SchumannReader:
    """Models Schumann resonance readings."""

    def read(self, kp_index: float = 0.0) -> tuple[float, float]:
        hz = SCHUMANN_FUNDAMENTAL + math.sin(kp_index * 0.1) * 0.3
        hz = max(6.5, min(9.0, hz))
        amplitude = max(0.0, min(1.0, 1.0 - kp_index * 0.08))
        return hz, amplitude

    def get_harmonics(self, hz: float) -> List[float]:
        return [hz * (i + 1) for i in range(5)]

    def get_dominant_mode(self, hz: float) -> SchumannMode:
        for boundary, mode in _MODE_BOUNDARIES:
            if hz < boundary:
                return mode
        return SchumannMode.FIFTH


# ---------------------------------------------------------------------------
# GeomagneticReader
# ---------------------------------------------------------------------------

class GeomagneticReader:
    _DEFAULT_KP: float = 2.0
    _DEFAULT_BZ: float = 0.0

    def classify_kp(self, kp: float) -> GeomagneticState:
        if kp >= KP_MAJOR_STORM:
            return GeomagneticState.MAJOR_STORM
        if kp >= KP_MINOR_STORM:
            return GeomagneticState.MINOR_STORM
        if kp >= 4.0:
            return GeomagneticState.UNSETTLED
        return GeomagneticState.QUIET

    def fetch_kp(self) -> float:
        if not _REQUESTS_AVAILABLE:
            return self._DEFAULT_KP
        try:
            resp = requests.get(
                "https://services.swpc.noaa.gov/products/noaa-estimated-planetary-k-index-1-minute.json",
                timeout=5,
            )
            data = resp.json()
            return float(data[-1][1])
        except Exception:
            return self._DEFAULT_KP

    def fetch_solar_wind_bz(self) -> float:
        if not _REQUESTS_AVAILABLE:
            return self._DEFAULT_BZ
        try:
            resp = requests.get(
                "https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json",
                timeout=5,
            )
            data = resp.json()
            return float(data[-1][3])
        except Exception:
            return self._DEFAULT_BZ


# ---------------------------------------------------------------------------
# EarthPulse
# ---------------------------------------------------------------------------

@dataclass
class EarthPulse:
    timestamp:            float
    schumann_hz:          float
    schumann_amplitude:   float
    schumann_harmonics:   List[float]
    dominant_mode:        SchumannMode
    kp_index:             float
    geomagnetic_state:    GeomagneticState
    solar_wind_bz:        float
    coherence_baseline:   float
    viriditas_carrier_hz: float
    atlas_status:         AtlasStatus
    source:               str = "atlas"

    @property
    def is_coherence_friendly(self) -> bool:
        return (
            self.geomagnetic_state == GeomagneticState.QUIET
            and self.coherence_baseline >= 0.5
        )

    @property
    def storm_warning(self) -> bool:
        return self.geomagnetic_state in (
            GeomagneticState.MINOR_STORM,
            GeomagneticState.MAJOR_STORM,
        )

    def to_dict(self) -> dict:
        return {
            "timestamp":            round(self.timestamp, 4),
            "schumann_hz":          round(self.schumann_hz, 4),
            "schumann_amplitude":   round(self.schumann_amplitude, 4),
            "schumann_harmonics":   [round(h, 4) for h in self.schumann_harmonics],
            "dominant_mode":        self.dominant_mode.value,
            "kp_index":             round(self.kp_index, 4),
            "geomagnetic_state":    self.geomagnetic_state.value,
            "solar_wind_bz":        round(self.solar_wind_bz, 4),
            "coherence_baseline":   round(self.coherence_baseline, 4),
            "viriditas_carrier_hz": round(self.viriditas_carrier_hz, 4),
            "atlas_status":         self.atlas_status.value,
            "source":               self.source,
            "coherence_friendly":   self.is_coherence_friendly,
            "storm_warning":        self.storm_warning,
        }

    def summary(self) -> str:
        return (
            f"Schumann {self.schumann_hz:.2f} Hz | "
            f"Kp {self.kp_index:.1f} ({self.geomagnetic_state.value}) | "
            f"Coherence {self.coherence_baseline:.2f} | "
            f"Carrier {self.viriditas_carrier_hz:.2f} Hz"
        )


# ---------------------------------------------------------------------------
# AtlasEngine
# ---------------------------------------------------------------------------

try:
    from core.viriditas_magnum_opus import SCHUMANN_HARMONICS as _VMO_HARMONICS
except ImportError:
    _VMO_HARMONICS: Dict[str, float] = {
        "nigredo":      7.83,
        "albedo":       14.3,
        "citrinitas":   20.8,
        "rubedo":       27.3,
        "quintessence": 31.32,
    }

_CARRIER_VALUES = list(_VMO_HARMONICS.values())


class AtlasEngine:
    """Unified ATLAS engine — produces EarthPulse readings."""

    _MAX_HISTORY = 288

    def __init__(self) -> None:
        self._schumann  = SchumannReader()
        self._geo       = GeomagneticReader()
        self._history:  Deque[EarthPulse] = deque(maxlen=self._MAX_HISTORY)
        self._current:  Optional[EarthPulse] = None
        self._refresh()

    def _refresh(self) -> None:
        kp  = self._geo.fetch_kp()
        bz  = self._geo.fetch_solar_wind_bz()
        geo = self._geo.classify_kp(kp)
        hz, amp = self._schumann.read(kp_index=kp)
        harmonics = self._schumann.get_harmonics(hz)
        mode = self._schumann.get_dominant_mode(hz)
        coherence = max(0.0, min(1.0, 0.8 - kp * 0.05))
        carrier = _CARRIER_VALUES[len(self._history) % len(_CARRIER_VALUES)]
        status = AtlasStatus.MODELED if not _REQUESTS_AVAILABLE else AtlasStatus.LIVE
        pulse = EarthPulse(
            timestamp=time.time(),
            schumann_hz=hz,
            schumann_amplitude=amp,
            schumann_harmonics=harmonics,
            dominant_mode=mode,
            kp_index=kp,
            geomagnetic_state=geo,
            solar_wind_bz=bz,
            coherence_baseline=coherence,
            viriditas_carrier_hz=carrier,
            atlas_status=status,
            source="atlas-model" if not _REQUESTS_AVAILABLE else "atlas-live",
        )
        self._history.append(pulse)
        self._current = pulse

    def pulse(self) -> EarthPulse:
        if self._current is None:
            self._refresh()
        return self._current  # type: ignore[return-value]

    def refresh(self) -> EarthPulse:
        self._refresh()
        return self._current  # type: ignore[return-value]

    def history(self, n: int = 10) -> List[EarthPulse]:
        return list(self._history)[-n:]

    def daily_coherence_average(self) -> float:
        if not self._history:
            return 0.0
        return sum(p.coherence_baseline for p in self._history) / len(self._history)

    def to_status(self) -> dict:
        p = self.pulse()
        return {
            "doctrine":            "C-ATLAS:1.0",
            "status":              p.atlas_status.value,
            "current_pulse":       p.to_dict(),
            "daily_coherence_avg": round(self.daily_coherence_average(), 4),
        }

    def _fallback_pulse(self) -> EarthPulse:
        return EarthPulse(
            timestamp=time.time(),
            schumann_hz=SCHUMANN_FUNDAMENTAL,
            schumann_amplitude=0.5,
            schumann_harmonics=self._schumann.get_harmonics(SCHUMANN_FUNDAMENTAL),
            dominant_mode=SchumannMode.FUNDAMENTAL,
            kp_index=self._geo._DEFAULT_KP,
            geomagnetic_state=GeomagneticState.QUIET,
            solar_wind_bz=0.0,
            coherence_baseline=0.5,
            viriditas_carrier_hz=_CARRIER_VALUES[0],
            atlas_status=AtlasStatus.OFFLINE,
            source="fallback",
        )


_atlas: Optional[AtlasEngine] = None


def get_atlas() -> AtlasEngine:
    global _atlas
    if _atlas is None:
        _atlas = AtlasEngine()
    return _atlas
