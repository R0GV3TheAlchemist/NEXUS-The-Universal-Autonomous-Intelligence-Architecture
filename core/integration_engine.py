"""
core/integration_engine.py

Formerly: synergy_engine.py

Orchestrates the integration of all GAIAN core modules into a unified
response pipeline. The integration engine is the final assembly point
before the GAIAN's response is dispatched — it combines signals from
all twelve core modules into a coherent, contextually appropriate output.

Canon refs : C30 (no silent failures), C32 (synergy doctrine)
See also   : C00 Foundational Cosmology — integration_engine naming.
"""
from __future__ import annotations

from core.synergy_engine import (
    SynergyEngine,
    SynergyReading,
    SynergyState,
    SynergyResult,
    DimensionScore,
    CanonPlanHint,
    ELEMENTAL_STAGES,
    blank_synergy_state,
    get_synergy_engine,
    _classify_stage,
    _resolve_keyword_conflicts,
    _analyse_canon_context,
)

# Canonical rename — preferred name going forward
IntegrationEngine = SynergyEngine


def get_integration_engine() -> SynergyEngine:
    """Return the module-level IntegrationEngine singleton.

    Delegates to get_synergy_engine() so both accessors share the same
    singleton instance — callers that already hold a reference via
    get_synergy_engine() will observe the same object.
    """
    return get_synergy_engine()


__all__ = [
    # Primary rename
    "IntegrationEngine",
    "get_integration_engine",
    # Re-exported public API from synergy_engine
    "SynergyEngine",
    "SynergyReading",
    "SynergyState",
    "SynergyResult",
    "DimensionScore",
    "CanonPlanHint",
    "ELEMENTAL_STAGES",
    "blank_synergy_state",
    "get_synergy_engine",
    "_classify_stage",
    "_resolve_keyword_conflicts",
    "_analyse_canon_context",
]
