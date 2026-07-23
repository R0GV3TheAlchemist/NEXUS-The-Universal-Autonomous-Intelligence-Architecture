# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/brown/clarity.py
===============================
BROWN — Clarity Layer

Clarity reads what transparency presents and discriminates genuine
Humus (fertile, porous, receptive earth) from compaction (earth
so dense it repels rather than receives) and sediment (settled
layers that have lost the capacity for active composting).

The central question of brown clarity:
  "Is this ground still receiving —
   or has it closed itself against the seed?"

Reference: docs/color/BROWN_CLARITY.md
           Earth Tablet — docs/tablets/EARTH_TABLET.md
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Fertility vs Inertia Discrimination
# ---------------------------------------------------------------------------

def distinguish_fertility_inertia(signal: dict) -> str:
    """
    Discriminate between fertile earth (Humus) and inertia (compaction).

    Fertile earth receives, transforms, and returns.
    Inertia is the earth too compacted to receive the seed.

    Decision logic:
      - 'porosity'    >= 0.55 AND 'decomposition_rate' >= 0.45
        → 'fertility'
      - Otherwise → 'inertia'

    Parameters
    ----------
    signal : dict
        Keys: 'porosity' (float), 'decomposition_rate' (float).

    Returns
    -------
    str
        'fertility' or 'inertia'.
    """
    if not signal:
        return "inertia"

    porosity           = float(signal.get("porosity",           0.0))
    decomposition_rate = float(signal.get("decomposition_rate", 0.0))

    if porosity >= 0.55 and decomposition_rate >= 0.45:
        return "fertility"
    return "inertia"


# ---------------------------------------------------------------------------
# Compaction State Detection
# ---------------------------------------------------------------------------

def detect_compaction_state(signal: dict) -> bool:
    """
    Detect compaction — the state where earth has been compressed
    so thoroughly it can no longer function as ground.

    Compaction markers:
      - 'groundedness' >= 0.85  (the earth is very present)
      - 'porosity'     < 0.25   (but it cannot breathe)
      - 'decomposition_rate' < 0.20  (and nothing is composting)

    All three must be simultaneously true.

    Parameters
    ----------
    signal : dict

    Returns
    -------
    bool
    """
    if not signal:
        return False

    groundedness       = float(signal.get("groundedness",       0.0))
    porosity           = float(signal.get("porosity",           1.0))
    decomposition_rate = float(signal.get("decomposition_rate", 1.0))

    return (
        groundedness >= 0.85
        and porosity < 0.25
        and decomposition_rate < 0.20
    )


# ---------------------------------------------------------------------------
# Brown Fire Classification
# ---------------------------------------------------------------------------

def classify_brown_fire(signal: dict) -> str:
    """
    Classify the quality of the brown fire (earth energy) in the signal.

    Brown fire types (priority order):
      1. 'humus'      — fertile, receptive, composting earth
      2. 'compaction' — earth closed against new input
      3. 'sediment'   — settled layers without active process
      4. 'clay'       — dense but still workable
      5. 'dim_brown'  — brown signal present but barely active

    Parameters
    ----------
    signal : dict

    Returns
    -------
    str
    """
    if not signal:
        return "dim_brown"

    if signal.get("humus"):
        return "humus"
    if signal.get("compaction"):
        return "compaction"
    if signal.get("sediment"):
        return "sediment"
    if signal.get("clay"):
        return "clay"
    return "dim_brown"


# ---------------------------------------------------------------------------
# Humus Level Assessment
# ---------------------------------------------------------------------------

def assess_humus_level(signal: dict) -> float:
    """
    Compute a normalised humus activation level [0.0, 1.0].

    Weighted mean of:
      - fertility_score          (weight 0.40)
      - groundedness_score       (weight 0.35)
      - porosity_score           (weight 0.25)

    Parameters
    ----------
    signal : dict

    Returns
    -------
    float  in [0.0, 1.0]
    """
    if not signal:
        return 0.0

    f = float(signal.get("fertility_score",    0.0))
    g = float(signal.get("groundedness_score", 0.0))
    p = float(signal.get("porosity_score",     0.0))

    level = (f * 0.40) + (g * 0.35) + (p * 0.25)
    return max(0.0, min(1.0, level))


# ---------------------------------------------------------------------------
# Earth Archetype Mapping
# ---------------------------------------------------------------------------

_EARTH_ARCHETYPES: dict[str, str] = {
    "humus":      "Humus — the fertile ground; the earth that receives, composts, and returns",
    "compaction": "Compaction — the earth that has closed; groundedness become impenetrability",
    "sediment":   "Sediment — settled layers; the history of the earth, no longer active",
    "clay":       "Clay — the dense but workable earth; not yet compacted, still responsive",
    "dim_brown":  "Dim Brown — the signal barely present beneath the surface",
}


def map_earth_archetype(fire_type: str) -> str:
    """
    Return the canonical Earth archetype description for a given fire type.

    Uses shared vocabulary: 'earth' as the ruling archetype of the brown domain.
    Pairs with 'hermes' routing in opacity.py.

    Parameters
    ----------
    fire_type : str

    Returns
    -------
    str
    """
    fire_type = str(fire_type).strip() if fire_type else ""
    return _EARTH_ARCHETYPES.get(fire_type, _EARTH_ARCHETYPES["dim_brown"])
