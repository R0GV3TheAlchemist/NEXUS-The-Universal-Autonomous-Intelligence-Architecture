"""resilience

NEXUS Resilience & Health Monitoring

Provides health monitoring, watchdog timers, and auto-restart
capabilities for NEXUS modules. Modelled after the MINIX 3
reincarnation server pattern.

Architecture reference:
    NEXUS_UNIVERSAL_OS.md  Domain 2.11 - Resilience
Research reference:
    MINIX 3 reincarnation server - auto-restart for crashed processes
    EmrysEngine                  - high-level intervention orchestrator
    GAIAN_LAWS.md Law VI         - Crisis Precedes Override
"""
from __future__ import annotations

from resilience.engine import ResilienceEngine, HealthMonitor, RestartPolicy, ModuleHealth

__all__ = ["ResilienceEngine", "HealthMonitor", "RestartPolicy", "ModuleHealth"]
