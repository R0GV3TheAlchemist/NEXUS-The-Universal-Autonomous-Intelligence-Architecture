"""wirelesspowersim

NEXUS Wireless Power Transmission Simulation

Models near-field resonant wireless power transfer between GAIAN nodes
using magnetically resonant coil coupling (Kurs et al., 2007).

Architecture reference:
    NEXUS_UNIVERSAL_OS.md  Domain 5.2 - Wireless Power
Research reference:
    Kurs et al. 2007 (Science) - near-field resonant coupling
    Yang et al. 2015           - magnetic beamforming SDP-relaxation
    NumPy/SciPy                - power flow matrix computation
"""
from __future__ import annotations

from wirelesspowersim.engine import (
    ResonantCoupler,
    PowerBeam,
    PowerGridSim,
)

__all__ = ["ResonantCoupler", "PowerBeam", "PowerGridSim"]
