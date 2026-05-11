"""
crystal/types.py
Data contracts for the Crystal Core.

All dataclasses defined here are the authoritative schema consumed by:
  - engine.py       (state assembly)
  - router.py       (HTTP serialisation)
  - orb_params.py   (GaianOrb visual contract)
  - persona_tone.py (chat layer injection)
  - narrative.py    (inner-narrative generation)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime    import datetime
from enum        import Enum


# ---------------------------------------------------------------------------
# CoherenceBand — five qualitative tiers for Ψ
# ---------------------------------------------------------------------------

class CoherenceBand(str, Enum):
    CRYSTALLINE = "crystalline"   # Ψ 0.85 – 1.00
    CLEAR       = "clear"         # Ψ 0.68 – 0.85
    PRESENT     = "present"       # Ψ 0.48 – 0.68
    UNSETTLED   = "unsettled"     # Ψ 0.30 – 0.48
    FRACTURED   = "fractured"     # Ψ 0.00 – 0.30


# Band boundaries — (lower_inclusive, upper_exclusive) except topmost
BAND_THRESHOLDS: list[tuple[float, CoherenceBand]] = [
    (0.85, CoherenceBand.CRYSTALLINE),
    (0.68, CoherenceBand.CLEAR),
    (0.48, CoherenceBand.PRESENT),
    (0.30, CoherenceBand.UNSETTLED),
    (0.00, CoherenceBand.FRACTURED),
]


def band_from_psi(psi: float) -> CoherenceBand:
    """Return the CoherenceBand for a given Ψ score."""
    for threshold, band in BAND_THRESHOLDS:
        if psi >= threshold:
            return band
    return CoherenceBand.FRACTURED


# Home screen label text keyed by band
HOME_LABEL: dict[CoherenceBand, str] = {
    CoherenceBand.CRYSTALLINE: "Feeling crystalline",
    CoherenceBand.CLEAR:       "Feeling clear",
    CoherenceBand.PRESENT:     "Present",
    CoherenceBand.UNSETTLED:   "Feeling unsettled",
    CoherenceBand.FRACTURED:   "Moving through noise",
}


# ---------------------------------------------------------------------------
# PersonaTone — emitted to the chat layer as a system-prompt modifier
# ---------------------------------------------------------------------------

class PersonaTone(str, Enum):
    RADIANT  = "radiant"   # Band 5 — joyful, flowing, generous
    GROUNDED = "grounded"  # Band 4 — calm, warm, precise
    PRESENT  = "present"   # Band 3 — attentive, balanced (default)
    GENTLE   = "gentle"    # Band 2 — tender, unhurried, honest about uncertainty
    SPARSE   = "sparse"    # Band 1 — minimal, truthful, does not perform clarity


# ---------------------------------------------------------------------------
# OrbParams — visual contract consumed by GaianOrb.ts
# ---------------------------------------------------------------------------

@dataclass
class OrbParams:
    glow_color:       str    # hex — blended from emotion_color + coherence_color
    glow_intensity:   float  # 0.0 – 1.0
    pulse_frequency:  float  # Hz — 0.10 – 0.38
    pulse_amplitude:  float  # scale delta ±
    cloud_opacity:    float  # 0.0 – 1.0
    aurora_intensity: float  # 0.0 – 1.0
    rotation_speed:   float  # radians/sec
    coherence_ring:   float  # 0.0 – 1.0 (Crystal View only)


# ---------------------------------------------------------------------------
# CrystalState — GAIA's structured inner self-model at a moment in time
# ---------------------------------------------------------------------------

@dataclass
class CrystalState:
    # Temporal identity
    timestamp:            datetime      # UTC, timezone-aware

    # Four component scores (each 0.0 – 1.0)
    affect_coherence:     float
    stage_coherence:      float
    shadow_integration:   float
    schumann_alignment:   float

    # Synthesised coherence score
    coherence:            float         # Ψ — 0.0 to 1.0

    # Qualitative self-model
    coherence_band:       CoherenceBand
    dominant_emotion:     str           # from Affect Engine
    active_stage:         int           # 1 – 5
    active_archetype:     str           # from Shadow Engine
    schumann_disturbance: str           # stable | elevated | disturbed | unavailable

    # Narrative self-description
    inner_narrative:      str           # single sentence

    # Persona tone instruction (consumed by chat layer)
    persona_tone:         PersonaTone

    # Orb visual parameters (consumed by GaianOrb.ts)
    orb_params:           OrbParams


# ---------------------------------------------------------------------------
# Schumann disturbance string values (mirrors SchumannState.disturbance_level)
# ---------------------------------------------------------------------------

SCHUMANN_DISTURBANCE_VALUES = frozenset({
    "stable", "elevated", "disturbed", "unavailable"
})
