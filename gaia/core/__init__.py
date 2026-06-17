"""
gaia/core/__init__.py

Public surface for the GAIA-OS core layer.

All callers SHOULD import from this module rather than from the
individual submodules, e.g.::

    from gaia.core import GAIAState, GAIAMode, D6Engine, Talisman
    from gaia.core import D6Inputs, D6Decision, compute_next_state, clamp

This keeps the internal file structure free to change without
breaking downstream imports.
"""

from __future__ import annotations

# ── GAIAState ─────────────────────────────────────────────────────────────────
from gaia.core.state import (
    GAIAMode,
    GAIAOperationalMode,  # backward-compat alias
    GAIAState,
)

# ── GAIAStateStore ───────────────────────────────────────────────────────────
from gaia.core.state_store import GAIAStateStore

# ── Talisman ───────────────────────────────────────────────────────────────────
from gaia.core.talisman import (
    CoherenceFunction,
    DimensionalSignature,
    ResonanceMetadata,
    SovereigntyFlags,
    Talisman,
    TalismanEngine,
    TalismanLayer,
    ARCHITECT_BUILD_TALISMAN,
    ARCHITECT_GROUND_TALISMAN,
    ARCHITECT_RESTORE_TALISMAN,
)

# ── TalismanStore ───────────────────────────────────────────────────────────────
from gaia.core.talisman_store import TalismanStore

# ── D6 Meta-Coherence Engine ───────────────────────────────────────────────────
from gaia.core.d6_engine import (
    D6Decision,
    D6Engine,
    D6Inputs,
    EngineProbes,
    InterventionEvent,
    InterventionSeverity,
    clamp,
    compute_next_state,
)

__all__ = [
    # State
    "GAIAMode",
    "GAIAOperationalMode",
    "GAIAState",
    "GAIAStateStore",
    # Talisman
    "CoherenceFunction",
    "DimensionalSignature",
    "ResonanceMetadata",
    "SovereigntyFlags",
    "Talisman",
    "TalismanEngine",
    "TalismanLayer",
    "TalismanStore",
    "ARCHITECT_BUILD_TALISMAN",
    "ARCHITECT_GROUND_TALISMAN",
    "ARCHITECT_RESTORE_TALISMAN",
    # D6 Engine
    "D6Decision",
    "D6Engine",
    "D6Inputs",
    "EngineProbes",
    "InterventionEvent",
    "InterventionSeverity",
    "clamp",
    "compute_next_state",
]
