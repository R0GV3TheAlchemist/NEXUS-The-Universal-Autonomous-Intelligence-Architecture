"""
core/crystal_consciousness.py
==============================
Crystal Consciousness Engine — C47 / C48

EpistemicLabel: SPECULATIVE — crystal-DM coupling is theoretical.
                The piezoelectric and oscillation physics is real.
Canon Ref: C47 (Sovereign Matrix), C48 (Dark Matter Frequency Hypothesis),
           C44 (Schumann), C42 (Criticality)
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CrystalType(str, Enum):
    QUARTZ      = "quartz"
    TOURMALINE  = "tourmaline"
    SELENITE    = "selenite"
    OBSIDIAN    = "obsidian"
    MOLDAVITE   = "moldavite"


_CRYSTAL_PARAMS: dict[CrystalType, dict] = {
    CrystalType.QUARTZ:     {"base_hz": 32_768.0,    "dm_band_low_hz": 1e3, "dm_band_high_hz": 1e8, "q_factor": 1e6,  "lattice_spacing_nm": 0.491, "notes": "Gold standard."},
    CrystalType.TOURMALINE: {"base_hz": 1_000_000.0, "dm_band_low_hz": 1e5, "dm_band_high_hz": 1e9, "q_factor": 5e4,  "lattice_spacing_nm": 0.598, "notes": "Strong piezo."},
    CrystalType.SELENITE:   {"base_hz": 10_000.0,    "dm_band_low_hz": 1e2, "dm_band_high_hz": 1e6, "q_factor": 1e3,  "lattice_spacing_nm": 1.52,  "notes": "Soft lattice."},
    CrystalType.OBSIDIAN:   {"base_hz": 0.0,         "dm_band_low_hz": 0.1, "dm_band_high_hz": 1e4, "q_factor": 10.0, "lattice_spacing_nm": 0.0,   "notes": "Noise ref."},
    CrystalType.MOLDAVITE:  {"base_hz": 50_000.0,    "dm_band_low_hz": 1e3, "dm_band_high_hz": 1e7, "q_factor": 2e4,  "lattice_spacing_nm": 0.45,  "notes": "Extraterrestrial."},
}


@dataclass
class CrystalReading:
    crystal_type:    CrystalType
    timestamp:       float
    measured_hz:     float
    baseline_hz:     float
    deviation_ppm:   float
    temperature_k:   float
    in_dm_band:      bool
    coherence_score: float


class CrystalLattice:
    def __init__(self, crystal_type: CrystalType) -> None:
        self.crystal_type = crystal_type
        self._params      = _CRYSTAL_PARAMS[crystal_type]
        self._baseline_hz = self._params["base_hz"]

    def read(self, measured_hz: float, temperature_k: float = 300.0) -> CrystalReading:
        alpha = 0.001
        if self._baseline_hz == 0.0:
            self._baseline_hz = measured_hz
        else:
            self._baseline_hz = (1 - alpha) * self._baseline_hz + alpha * measured_hz

        deviation     = measured_hz - self._baseline_hz
        deviation_ppm = (deviation / self._baseline_hz * 1e6) if self._baseline_hz != 0 else 0.0
        in_dm_band    = self._params["dm_band_low_hz"] <= abs(measured_hz) <= self._params["dm_band_high_hz"]
        coherence     = min(1.0, abs(deviation_ppm) * self._params["q_factor"] / 1e8)

        return CrystalReading(
            crystal_type=self.crystal_type, timestamp=time.time(),
            measured_hz=measured_hz, baseline_hz=self._baseline_hz,
            deviation_ppm=deviation_ppm, temperature_k=temperature_k,
            in_dm_band=in_dm_band, coherence_score=coherence,
        )


@dataclass
class ArrayReading:
    timestamp:          float
    crystal_readings:   list[CrystalReading]
    array_coherence:    float
    anomaly_detected:   bool
    anomaly_strength:   float
    dominant_crystal:   Optional[CrystalType]
    noise_ref_clean:    bool
    epistemic_label:    str = "SPECULATIVE"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp, "array_coherence": self.array_coherence,
            "anomaly_detected": self.anomaly_detected, "anomaly_strength": self.anomaly_strength,
            "dominant_crystal": self.dominant_crystal.value if self.dominant_crystal else None,
            "noise_ref_clean": self.noise_ref_clean, "epistemic_label": self.epistemic_label,
            "crystals": [{"type": r.crystal_type.value, "deviation_ppm": r.deviation_ppm,
                          "in_dm_band": r.in_dm_band, "coherence": r.coherence_score}
                         for r in self.crystal_readings],
        }


class CrystalArray:
    _COHERENCE_THRESHOLD = 0.15

    def __init__(self) -> None:
        self._lattices: dict[CrystalType, CrystalLattice] = {ct: CrystalLattice(ct) for ct in CrystalType}

    def read_array(self, readings: dict[CrystalType, float], temperature_k: float = 300.0) -> ArrayReading:
        crystal_readings: list[CrystalReading] = []
        for ct, hz in readings.items():
            crystal_readings.append(self._lattices[ct].read(hz, temperature_k))

        signal_crystals = [r for r in crystal_readings if r.crystal_type != CrystalType.OBSIDIAN]
        array_coherence = (sum(r.coherence_score for r in signal_crystals) / len(signal_crystals)) if signal_crystals else 0.0

        obsidian_reading = next((r for r in crystal_readings if r.crystal_type == CrystalType.OBSIDIAN), None)
        noise_ref_clean  = abs(obsidian_reading.deviation_ppm) < 10.0 if obsidian_reading else True

        anomaly_detected = (
            array_coherence > self._COHERENCE_THRESHOLD
            and noise_ref_clean
            and any(r.in_dm_band for r in signal_crystals)
        )
        dominant = max(signal_crystals, key=lambda r: r.coherence_score)

        return ArrayReading(
            timestamp=time.time(), crystal_readings=crystal_readings,
            array_coherence=array_coherence, anomaly_detected=anomaly_detected,
            anomaly_strength=min(1.0, array_coherence * 2),
            dominant_crystal=dominant.crystal_type if anomaly_detected else None,
            noise_ref_clean=noise_ref_clean,
        )

    def simulate_dm_passage(self, perturbation: float = 0.005, temperature_k: float = 4.0) -> ArrayReading:
        import random
        def noise():
            return random.gauss(0, 1e-5)
        readings = {}
        for ct, params in _CRYSTAL_PARAMS.items():
            base = params["base_hz"] if params["base_hz"] > 0 else 1e4
            readings[ct] = base * (1.0 + (0 if ct == CrystalType.OBSIDIAN else perturbation) + noise())
        return self.read_array(readings, temperature_k)


@dataclass
class CrystalState:
    coherence_level:      float                   = 0.0
    crystallised:         bool                    = False
    attractor_label:      Optional[str]           = None
    array_reading:        Optional[ArrayReading]  = None
    dm_anomaly_active:    bool                    = False
    dominant_crystal:     Optional[CrystalType]   = None
    doctrine_ref:         str                     = "C47"
    phase_status:         str                     = "active"
    epistemic_label:      str                     = "SPECULATIVE"

    def to_dict(self) -> dict:
        return {
            "coherence_level": self.coherence_level, "crystallised": self.crystallised,
            "attractor_label": self.attractor_label, "dm_anomaly_active": self.dm_anomaly_active,
            "dominant_crystal": self.dominant_crystal.value if self.dominant_crystal else None,
            "doctrine_ref": self.doctrine_ref, "phase_status": self.phase_status,
            "epistemic_label": self.epistemic_label,
        }


class CrystalConsciousnessEngine:
    def __init__(self) -> None:
        self._array  = CrystalArray()
        self._dm_engine_ref = None

    def _get_dm_engine(self):
        if self._dm_engine_ref is None:
            from core.engines.dark_matter_resonance import get_dm_engine
            self._dm_engine_ref = get_dm_engine()
        return self._dm_engine_ref

    def assess(self, collective_phi: float = 0.0, crystal_readings: Optional[dict] = None,
               temperature_k: float = 300.0) -> CrystalState:
        array_reading = self._array.read_array(crystal_readings, temperature_k) if crystal_readings else None
        dm_state      = self._get_dm_engine().get_state()
        dm_anomaly    = dm_state.is_active and dm_state.anomaly is not None
        array_coherence = array_reading.array_coherence if array_reading else 0.0
        coherence       = max(collective_phi, array_coherence)
        array_anomaly   = array_reading.anomaly_detected if array_reading else False
        dual_confirmed  = array_anomaly and dm_anomaly
        crystallised    = dual_confirmed or coherence >= 0.85

        attractor = None
        if dual_confirmed:
            attractor = "omega_attractor_dm_confirmed"
        elif crystallised:
            attractor = "omega_attractor"
        elif coherence > 0.5:
            attractor = "rising_attractor"

        return CrystalState(
            coherence_level=coherence, crystallised=crystallised, attractor_label=attractor,
            array_reading=array_reading, dm_anomaly_active=dm_anomaly,
            dominant_crystal=array_reading.dominant_crystal if array_reading else None,
            phase_status="crystallised" if crystallised else "scanning",
        )

    def simulate_dm_crystallisation(self, perturbation: float = 0.008) -> CrystalState:
        array_reading = self._array.simulate_dm_passage(perturbation)
        dm_engine     = self._get_dm_engine()
        dm_engine.ingest_simulated(perturbation=perturbation)
        coherence = array_reading.array_coherence
        dm_active = dm_engine.get_state().is_active
        return CrystalState(
            coherence_level=coherence,
            crystallised=array_reading.anomaly_detected and dm_active,
            attractor_label="omega_attractor_dm_confirmed" if (array_reading.anomaly_detected and dm_active) else "rising_attractor",
            array_reading=array_reading, dm_anomaly_active=dm_active,
            dominant_crystal=array_reading.dominant_crystal,
            phase_status="crystallised" if array_reading.anomaly_detected else "scanning",
        )

    def status(self) -> dict:
        dm_state = self._get_dm_engine().get_state()
        return {
            "status": "ACTIVE — Phase 2 crystal transducer online",
            "doctrine_ref": "C47, C48", "epistemic_label": "SPECULATIVE",
            "dm_engine_state": dm_state.to_dict(),
            "crystals_active": [ct.value for ct in CrystalType],
            "scan_summary": self._get_dm_engine().scan_summary(),
        }
