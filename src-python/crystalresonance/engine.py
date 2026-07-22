"""crystalresonance.engine

Phonon Mode Resonance Monitor

Detects when crystal lattice phonon modes resonate with external
driving frequencies (e.g., Schumann 7.83 Hz) and emits ResonancePulse
events. Designed to couple with schumann.SyncPulse and
affectengine.AffectTransition in future integration phases.

Research reference:
    pymatgen.phonon  - phonon band structures and DOS
    phonopy          - mode calculation toolkit
    Tier 1 research  - crystal/crystalresonance design patterns
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Sequence, Mapping, Any, Iterable

logger = logging.getLogger("crystalresonance.engine")


@dataclass
class ResonancePulse:
    """A phonon resonance excitation event.

    Represents the excitation of a specific phonon mode when its
    natural frequency is driven by an external field.

    Fields:
        mode_index:    Index of the phonon mode in the spectrum.
        frequency_hz:  Mode frequency in Hz.
        amplitude:     Dimensionless excitation amplitude (normalised).
        phase_rad:     Phase of excitation in radians.
        metadata:      Provenance metadata (driver source, lattice info, etc.).
    """
    mode_index: int
    frequency_hz: float
    amplitude: float
    phase_rad: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class PhononMode:
    """A single phonon normal mode.

    Phase B: wrap pymatgen.phonon / phonopy eigenvector data here.

    Fields:
        mode_index:    Index in the spectrum.
        frequency_hz:  Mode frequency in Hz.
        intensity:     DOS weight or mode strength measure.
    """
    mode_index: int
    frequency_hz: float
    intensity: float = 1.0


@dataclass
class CrystalPhononSpectrum:
    """Phonon spectrum for a crystal structure.

    Phase B: derive from pymatgen.phonon band structure + phonopy.

    Fields:
        modes:     Sequence of PhononMode entries.
        metadata:  Lattice ID, temperature, calculation method, etc.
    """
    modes: Sequence[PhononMode] = field(default_factory=list)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class ResonanceConfig:
    """Configuration for resonance detection.

    Fields:
        target_frequencies_hz: External driving frequencies to watch
                               (e.g., [7.83, 14.3, 20.8] for Schumann).
        tolerance_hz:          Frequency window for declaring resonance.
        min_intensity:         Minimum phonon mode intensity to consider.
    """
    target_frequencies_hz: Sequence[float] = field(default_factory=list)
    tolerance_hz: float = 0.1
    min_intensity: float = 0.0


class CrystalResonanceMonitor:
    """Monitor for crystal lattice resonance conditions.

    Inspects CrystalPhononSpectrum objects and emits ResonancePulse
    events when a phonon mode frequency falls within tolerance of a
    target driving frequency.

    Cross-module coupling (Phase D+):
        schumann.SyncPulse -> CrystalResonanceMonitor -> affectengine.AffectTransition

    Reference:
        pymatgen.phonon, phonopy, Tier 1 crystal resonance research.
    """

    def __init__(self, config: ResonanceConfig | None = None) -> None:
        self.config = config or ResonanceConfig()
        logger.info("CrystalResonanceMonitor initialised with %d target frequencies.",
                    len(self.config.target_frequencies_hz))

    def detect_resonances(self, spectrum: CrystalPhononSpectrum) -> Sequence[ResonancePulse]:
        """Detect resonance conditions in a phonon spectrum.

        Intended algorithm:
            For each PhononMode in spectrum.modes:
                For each target_freq in config.target_frequencies_hz:
                    If |mode.frequency_hz - target_freq| <= tolerance_hz
                    and mode.intensity >= min_intensity:
                        Emit ResonancePulse for that mode.

        Args:
            spectrum: CrystalPhononSpectrum to inspect.

        Returns:
            Sequence of ResonancePulse objects.

        Raises:
            NotImplementedError: Always in Phase C.
        """
        raise NotImplementedError(
            "CrystalResonanceMonitor.detect_resonances() not yet implemented. "
            "Expected: iterate phonon modes, compare to target_frequencies_hz "
            "within tolerance_hz, construct ResonancePulse for each match."
        )

    def handle_external_pulses(self, pulses: Iterable[Any]) -> Sequence[ResonancePulse]:
        """React to external driving pulses (e.g., schumann.SyncPulse).

        Intended integration:
            Accept schumann.SyncPulse events, extract frequency, update
            config.target_frequencies_hz dynamically, re-evaluate resonances.

        Args:
            pulses: Iterable of external pulse objects (schumann.SyncPulse
                    or any object with a .frequency_hz attribute).

        Returns:
            Sequence of newly inferred ResonancePulse events.

        Raises:
            NotImplementedError: Always in Phase C.
        """
        raise NotImplementedError(
            "CrystalResonanceMonitor.handle_external_pulses() not yet implemented. "
            "Expected: accept SyncPulse events, update target frequencies, "
            "and return inferred resonance pulses against current spectrum."
        )
