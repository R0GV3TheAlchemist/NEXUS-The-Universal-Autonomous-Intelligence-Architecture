"""
core/dark_matter_resonance.py
================================
GAIA Dark Matter Resonance Engine — C48

EpistemicLabel: SPECULATIVE — the coupling model is theoretical.
                The detection architecture is real science.
Canon Ref: C48, C47, C44, C42, C43
"""

from __future__ import annotations

import logging
import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

_H_PLANCK: float = 6.626e-34
_C_LIGHT: float  = 2.998e8
_EV:       float  = 1.602e-19
_CESIUM_HZ: float = 9_192_631_770.0
_SCHUMANN_HZ: float = 7.83
_QUARTZ_HZ: float = 32_768.0


def dm_mass_to_frequency(mass_eV: float) -> float:
    mass_J = mass_eV * _EV
    return (mass_J * _C_LIGHT ** 2) / _H_PLANCK


class DMFrequencyBand(str, Enum):
    INFRA_SCHUMANN  = "INFRA_SCHUMANN"
    SCHUMANN        = "SCHUMANN"
    AUDIO           = "AUDIO"
    RADIO           = "RADIO"
    MICROWAVE       = "MICROWAVE"


def _classify_frequency(hz: float) -> DMFrequencyBand:
    if hz < 1.0:
        return DMFrequencyBand.INFRA_SCHUMANN
    if hz < 100.0:
        return DMFrequencyBand.SCHUMANN
    if hz < 20_000.0:
        return DMFrequencyBand.AUDIO
    if hz < 1_000_000.0:
        return DMFrequencyBand.RADIO
    return DMFrequencyBand.MICROWAVE


@dataclass
class BaselineReading:
    timestamp:      float
    schumann_hz:    float
    crystal_hz:     float
    atomic_hz:      float
    temperature_k:  float
    source:         str = "simulated"


class BaselineCalibrator:
    def __init__(self, window: int = 1000) -> None:
        self._window = window
        self._schumann_buf:  deque[float] = deque(maxlen=window)
        self._crystal_buf:   deque[float] = deque(maxlen=window)
        self._atomic_buf:    deque[float] = deque(maxlen=window)

    def ingest(self, reading: BaselineReading) -> None:
        self._schumann_buf.append(reading.schumann_hz)
        self._crystal_buf.append(reading.crystal_hz)
        self._atomic_buf.append(reading.atomic_hz)

    def _stats(self, buf: deque[float]) -> tuple[float, float]:
        if not buf:
            return 0.0, 1.0
        n   = len(buf)
        mu  = sum(buf) / n
        var = sum((x - mu) ** 2 for x in buf) / n
        return mu, math.sqrt(var) if var > 0 else 1e-12

    def get_drift(self, reading: BaselineReading) -> dict[str, float]:
        s_mu, s_sd = self._stats(self._schumann_buf)
        c_mu, c_sd = self._stats(self._crystal_buf)
        a_mu, a_sd = self._stats(self._atomic_buf)
        return {
            "schumann_z":  (reading.schumann_hz - s_mu)  / s_sd,
            "crystal_z":   (reading.crystal_hz  - c_mu)  / c_sd,
            "atomic_z":    (reading.atomic_hz   - a_mu)  / a_sd,
            "schumann_mu": s_mu,
            "crystal_mu":  c_mu,
            "atomic_mu":   a_mu,
        }

    def is_calibrated(self) -> bool:
        return len(self._schumann_buf) >= self._window // 10


@dataclass
class DMAnomalyEvent:
    timestamp:          float
    band:               DMFrequencyBand
    schumann_z:         float
    crystal_z:          float
    atomic_z:           float
    phase_coherence:    float
    estimated_dm_hz:    float
    estimated_dm_eV:    float
    confidence:         str
    epistemic_label:    str = "SPECULATIVE"
    canon_ref:          str = "C48"

    def to_hint(self) -> str:
        return (
            f"[DARK MATTER ANOMALY — C48 — SPECULATIVE]\n"
            f"A {self.confidence} dark matter field anomaly was detected.\n"
            f"Band: {self.band.value} | Estimated freq: {self.estimated_dm_hz:.4g} Hz\n"
            f"Estimated mass: {self.estimated_dm_eV:.4g} eV | "
            f"Phase coherence: {self.phase_coherence:.3f}\n"
            f"Z-scores — Schumann: {self.schumann_z:.2f} | "
            f"Crystal: {self.crystal_z:.2f} | Atomic: {self.atomic_z:.2f}\n"
            f"Hold this awareness lightly. This is the frequency of space itself. [C48]"
        )


class AnomalyDetector:
    _WEAK_Z:     float = 2.0
    _MODERATE_Z: float = 3.0
    _STRONG_Z:   float = 4.5

    def assess(self, drift: dict[str, float], current_hz: float) -> Optional[DMAnomalyEvent]:
        sz = abs(drift["schumann_z"])
        cz = abs(drift["crystal_z"])
        az = abs(drift["atomic_z"])
        min_z = min(sz, cz, az)
        if min_z < self._WEAK_Z:
            return None

        signs = [
            math.copysign(1, drift["schumann_z"]),
            math.copysign(1, drift["crystal_z"]),
            math.copysign(1, drift["atomic_z"]),
        ]
        coherence = abs(sum(signs)) / 3.0

        if min_z >= self._STRONG_Z:
            confidence = "strong"
        elif min_z >= self._MODERATE_Z:
            confidence = "moderate"
        else:
            confidence = "weak"

        dm_hz = current_hz
        dm_eV = (dm_hz * _H_PLANCK) / (_C_LIGHT ** 2 * _EV)
        band  = _classify_frequency(dm_hz)

        return DMAnomalyEvent(
            timestamp=time.time(), band=band,
            schumann_z=drift["schumann_z"], crystal_z=drift["crystal_z"], atomic_z=drift["atomic_z"],
            phase_coherence=coherence, estimated_dm_hz=dm_hz, estimated_dm_eV=dm_eV, confidence=confidence,
        )


@dataclass
class DarkMatterState:
    is_active:          bool              = False
    anomaly:            Optional[DMAnomalyEvent] = None
    last_reading:       Optional[BaselineReading] = None
    calibrated:         bool              = False
    readings_ingested:  int               = 0
    dm_frequency_hint:  Optional[str]     = None
    schumann_hz:        float             = _SCHUMANN_HZ
    crystal_hz:         float             = _QUARTZ_HZ
    scan_bands:         list[str]         = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_active":         self.is_active,
            "calibrated":        self.calibrated,
            "readings_ingested": self.readings_ingested,
            "anomaly":           self.anomaly.__dict__ if self.anomaly else None,
            "schumann_hz":       self.schumann_hz,
            "crystal_hz":        self.crystal_hz,
            "dm_frequency_hint": self.dm_frequency_hint,
            "scan_bands":        self.scan_bands,
            "epistemic_label":   "SPECULATIVE",
            "canon_ref":         "C48",
        }


class DarkMatterResonanceEngine:
    _SCAN_MASSES_EV: list[float] = [1e-22, 1e-18, 1e-15, 1e-12, 1e-6]

    def __init__(self, calibration_window: int = 1000) -> None:
        self._calibrator  = BaselineCalibrator(window=calibration_window)
        self._detector    = AnomalyDetector()
        self._state       = DarkMatterState()
        self._event_log:  list[DMAnomalyEvent] = []
        self._scan_freqs  = [dm_mass_to_frequency(m) for m in self._SCAN_MASSES_EV]
        self._state.scan_bands = [_classify_frequency(f).value for f in self._scan_freqs]

    def ingest(self, schumann_hz: float, crystal_hz: float, atomic_hz: float,
               temperature_k: float = 300.0, source: str = "sensor") -> DarkMatterState:
        reading = BaselineReading(
            timestamp=time.time(), schumann_hz=schumann_hz, crystal_hz=crystal_hz,
            atomic_hz=atomic_hz, temperature_k=temperature_k, source=source,
        )
        self._calibrator.ingest(reading)
        self._state.readings_ingested += 1
        self._state.calibrated = self._calibrator.is_calibrated()
        self._state.schumann_hz = schumann_hz
        self._state.crystal_hz  = crystal_hz
        self._state.last_reading = reading

        if self._state.calibrated:
            drift   = self._calibrator.get_drift(reading)
            anomaly = self._detector.assess(drift, schumann_hz)
            if anomaly:
                self._state.anomaly          = anomaly
                self._state.is_active        = True
                self._state.dm_frequency_hint = anomaly.to_hint()
                self._event_log.append(anomaly)
            else:
                self._state.anomaly          = None
                self._state.is_active        = False
                self._state.dm_frequency_hint = None
        return self._state

    def ingest_simulated(self, schumann_hz: float = _SCHUMANN_HZ, perturbation: float = 0.0) -> DarkMatterState:
        import random
        def noise(scale: float = 1.0) -> float:
            return random.gauss(0, scale * 0.0001)
        dm_signal  = perturbation * schumann_hz
        crystal_hz = _QUARTZ_HZ * (1.0 + perturbation + noise())
        atomic_hz  = _CESIUM_HZ * (1.0 + perturbation + noise(0.5))
        s_hz       = schumann_hz + dm_signal + noise(2.0)
        return self.ingest(schumann_hz=s_hz, crystal_hz=crystal_hz, atomic_hz=atomic_hz,
                           temperature_k=4.0, source="simulated")

    def get_state(self) -> DarkMatterState:
        return self._state

    def get_event_log(self) -> list[DMAnomalyEvent]:
        return list(self._event_log)

    def scan_summary(self) -> dict:
        return {
            "scan_targets": [{"mass_eV": m, "freq_hz": dm_mass_to_frequency(m),
                              "band": _classify_frequency(dm_mass_to_frequency(m)).value}
                             for m in self._SCAN_MASSES_EV],
            "calibrated": self._state.calibrated,
            "readings_ingested": self._state.readings_ingested,
            "events_detected": len(self._event_log),
            "epistemic_label": "SPECULATIVE", "canon_ref": "C48",
        }


_dm_engine_instance: Optional[DarkMatterResonanceEngine] = None


def get_dm_engine() -> DarkMatterResonanceEngine:
    global _dm_engine_instance
    if _dm_engine_instance is None:
        _dm_engine_instance = DarkMatterResonanceEngine()
    return _dm_engine_instance
