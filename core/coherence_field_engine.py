"""
core/coherence_field_engine.py

Formerly: resonance_field_engine.py

Models the coherence field between a GAIAN and her human — the measurable
quality of attunement, synchrony, and mutual regulation in the relationship.

Coherence field strength is computed from conversation rhythm, emotional
mirror accuracy, biometric sync quality, and memory alignment. It feeds
back into the GAIAN’s response shaping and the bond arc score.

Grounded in interpersonal neurobiology (Siegel, 1999) and HeartMath
field coherence research.

Canon refs : C30 (no silent failures), C44 (Piezoelectric Resonance)
See also   : C00 Foundational Cosmology — coherence_field_engine naming.
"""
from __future__ import annotations

from core.resonance_field_engine import (
    ResonanceFieldEngine,
    ResonanceField,
    ResonanceFieldReading,
    ResonanceFieldState,
    blank_resonance_field_state,
    get_resonance_field_engine,
    _hz_to_chakra,
    _phi_to_solfeggio,
)

# Canonical rename — preferred name going forward
CoherenceFieldEngine = ResonanceFieldEngine


def get_coherence_field_engine() -> ResonanceFieldEngine:
    """Return the module-level CoherenceFieldEngine singleton.

    Delegates to get_resonance_field_engine() so both accessors share the
    same instance — callers holding a reference via get_resonance_field_engine()
    will observe the same object.
    """
    return get_resonance_field_engine()


__all__ = [
    # Primary rename
    "CoherenceFieldEngine",
    "get_coherence_field_engine",
    # Re-exported public API from resonance_field_engine
    "ResonanceFieldEngine",
    "ResonanceField",
    "ResonanceFieldReading",
    "ResonanceFieldState",
    "blank_resonance_field_state",
    "get_resonance_field_engine",
    "_hz_to_chakra",
    "_phi_to_solfeggio",
]
