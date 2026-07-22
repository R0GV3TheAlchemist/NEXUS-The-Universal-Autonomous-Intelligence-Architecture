"""
crisis_engine — Crisis Detection Engine

Detects and escalates system-wide crisis conditions triggered by affect
overload, shadow criticality, or persona instability breach.

Architecture reference: NEXUS_UNIVERSAL_OS.md Domain 2.10
GAIAN law:              GAIAN_LAWS.md Law VI — Crisis Precedes Override
"""
from __future__ import annotations

from crisis_engine.engine import CrisisEngine, EngineConfig, CrisisLevel

__all__ = ["CrisisEngine", "EngineConfig", "CrisisLevel"]
