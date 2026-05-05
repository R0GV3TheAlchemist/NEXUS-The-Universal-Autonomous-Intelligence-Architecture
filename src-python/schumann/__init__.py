"""
Schumann Alignment Layer — Issue #64

Public surface:
  SchumannEngine        — main service, call .tick() to get SchumannState
  SchumannState         — typed output snapshot consumed by Stage Engine
  PlanetarySignalSample — typed raw input sample produced by sources
  DisturbanceLevel      — enum: stable | elevated | disturbed | unavailable

Quick start::

    from schumann import SchumannEngine, EngineConfig
    engine = SchumannEngine(EngineConfig(source="dev"))
    state  = await engine.tick()
"""

from .models import (
    DisturbanceLevel,
    PlanetarySignalSample,
    SchumannState,
)
from .engine import SchumannEngine, EngineConfig

__all__ = [
    "DisturbanceLevel",
    "PlanetarySignalSample",
    "SchumannState",
    "SchumannEngine",
    "EngineConfig",
]
