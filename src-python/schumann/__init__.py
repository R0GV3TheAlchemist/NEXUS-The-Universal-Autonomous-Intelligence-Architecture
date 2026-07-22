"""
schumann — Schumann Resonance Engine

Monitors and processes Schumann resonance signals (Earth's ELF electromagnetic
resonances, primary frequency ~7.83 Hz) to provide planetary entrainment
inputs to the NEXUS affect and stage engines.

Architecture reference: NEXUS_UNIVERSAL_OS.md Domain 1.6
HAL dependency:         DeviceCapability.ELF_SENSOR
"""
from __future__ import annotations

from schumann.engine import SchumannEngine, SchumannReading
from schumann.router import schumann_router, init_schumann_engine

__all__ = ["SchumannEngine", "SchumannReading", "schumann_router", "init_schumann_engine"]
