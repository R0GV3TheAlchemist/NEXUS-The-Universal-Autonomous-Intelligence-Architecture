"""crystalresonance

NEXUS Crystal Lattice Resonance Monitoring

Monitors phonon modes in crystal lattices for resonance conditions
driven by external frequencies (e.g., Schumann 7.83 Hz). Emits
ResonancePulse events when a phonon mode matches a target frequency.

Architecture reference:
    NEXUS_UNIVERSAL_OS.md  Domain 4.3 - Crystal Resonance
Research reference:
    pymatgen.phonon        - phonon band structures and DOS
    ASE                    - Atomic Simulation Environment
    phonopy                - phonon mode calculations
    schumann.SyncPulse     - external driving frequency source
"""
from __future__ import annotations

from crystalresonance.engine import (
    ResonancePulse,
    PhononMode,
    CrystalPhononSpectrum,
    ResonanceConfig,
    CrystalResonanceMonitor,
)

__all__ = [
    "ResonancePulse",
    "PhononMode",
    "CrystalPhononSpectrum",
    "ResonanceConfig",
    "CrystalResonanceMonitor",
]
