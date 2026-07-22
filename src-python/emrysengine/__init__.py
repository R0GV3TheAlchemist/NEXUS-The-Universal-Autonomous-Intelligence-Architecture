"""emrysengine

NEXUS Emrys Resilience & Intervention Engine

Orchestrates system-wide resilience by ingesting health signals from
all NEXUS modules, evaluating degradation patterns, and planning
interventions (graceful degradation, restart, crisis escalation).

Architecture reference:
    NEXUS_UNIVERSAL_OS.md  Domain 2.10 - EmrysEngine
Research reference:
    MINIX 3 reincarnation server - auto-restart for crashed processes
    CrisisEngine                - CRITICAL escalation partner
    GAIAN_LAWS.md Law VI        - Crisis Precedes Override
"""
from __future__ import annotations

from emrysengine.engine import EmrysEngine, EmrysConfig, HealthSignal, HealthSeverity
from emrysengine.router import init_emrys_engine

__all__ = ["EmrysEngine", "EmrysConfig", "HealthSignal", "HealthSeverity", "init_emrys_engine"]
