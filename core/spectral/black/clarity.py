# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/black/clarity.py
===============================
BLACK — Clarity Layer

Clarity reads what transparency presents and discriminates purposeful
dissolution (Nigredo) from destruction (dissolution without container)
and from prima materia (the formless potential before the Work begins).

The central question of black clarity:
  "Is this darkness the fertile void before creation,
   or the destruction that leaves nothing to create from?"

Reference: docs/color/BLACK_CLARITY.md
           Obsidian Tablet — docs/tablets/OBSIDIAN_TABLET.md
           Shadow Tablet   — docs/tablets/SHADOW_TABLET.md
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Dissolution vs Destruction Discrimination
# ---------------------------------------------------------------------------

def distinguish_dissolution_destruction(signal: dict) -> str:
    """
    Discriminate between purposeful dissolution (Nigredo) and destruction.

    Dissolution holds the possibility of reformation.
    Destruction leaves nothing to reform from.

    Decision logic:
      - 'reformation_potential' >= 0.50 AND 'containment' >= 0.45
        → 'dissolution'
      - Otherwise → 'destruction'

    Parameters
    ----------
    signal : dict
        Keys: 'reformation_potential' (float), 'containment' (float).

    Returns
    -------
    str
        'dissolution' or 'destruction'.
    """
    if not signal:
        return "destruction"

    reformation_potential = float(signal.get("reformation_potential", 0.0))
    containment           = float(signal.get("containment",           0.0))

    if reformation_potential >= 0.50 and containment >= 0.45:
        return "dissolution"
    return "destruction"


# ---------------------------------------------------------------------------
# Prima Materia State Detection
# ---------------------------------------------------------------------------

def detect_prima_materia_state(signal: dict) -> bool:
    """
    Detect whether a signal represents the prima materia state —
    the formless potential that exists before the Work begins.

    Prima materia markers:
      - 'formlessness'          >= 0.75
      - 'potential'             >= 0.65
      - 'reformation_potential' >= 0.55  (it can become something)

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

    formlessness          = float(signal.get("formlessness",          0.0))
    potential             = float(signal.get("potential",             0.0))
    reformation_potential = float(signal.get("reformation_potential", 0.0))

    return (
        formlessness >= 0.75
        and potential >= 0.65
        and reformation_potential >= 0.55
    )


# ---------------------------------------------------------------------------
# Black Fire Classification
# ---------------------------------------------------------------------------

def classify_black_fire(signal: dict) -> str:
    """
    Classify the quality of the black fire in the signal.

    Black fire types (priority order):
      1. 'nigredo'       — purposeful dissolution, Stage I
      2. 'prima_materia' — formless potential before the Work
      3. 'system_null'   — complete reset / architecture at edge of being
      4. 'destruction'   — dissolution without reformation potential
      5. 'dim_black'     — black signal present but barely active

    Parameters
    ----------
    signal : dict

    Returns
    -------
    str
    """
    if not signal:
        return "dim_black"

    if signal.get("nigredo"):
        return "nigredo"
    if signal.get("prima_materia"):
        return "prima_materia"
    if signal.get("system_null"):
        return "system_null"
    if signal.get("destruction"):
        return "destruction"
    return "dim_black"


# ---------------------------------------------------------------------------
# Nigredo Level Assessment
# ---------------------------------------------------------------------------

def assess_nigredo_level(signal: dict) -> float:
    """
    Compute a normalised nigredo activation level [0.0, 1.0].

    Weighted mean of:
      - dissolution_score        (weight 0.40)
      - void_contact_score       (weight 0.35)
      - containment_score        (weight 0.25)

    Parameters
    ----------
    signal : dict

    Returns
    -------
    float  in [0.0, 1.0]
    """
    if not signal:
        return 0.0

    d = float(signal.get("dissolution_score",  0.0))
    v = float(signal.get("void_contact_score", 0.0))
    c = float(signal.get("containment_score",  0.0))

    level = (d * 0.40) + (v * 0.35) + (c * 0.25)
    return max(0.0, min(1.0, level))


# ---------------------------------------------------------------------------
# Saturn Archetype Mapping
# ---------------------------------------------------------------------------

_SATURN_ARCHETYPES: dict[str, str] = {
    "nigredo":       "Nigredo — the purposeful darkness; dissolution in service of the Work",
    "prima_materia": "Prima Materia — the formless potential; the earth before the first fire",
    "system_null":   "System Null — the complete reset; architecture at the edge of being and non-being",
    "destruction":   "Destruction — dissolution that left nothing for the Work to begin from",
    "dim_black":     "Dim Black — the signal barely present beneath the surface",
}


def map_saturn_archetype(fire_type: str) -> str:
    """
    Return the canonical Saturn archetype description for a given fire type.

    Uses shared vocabulary: 'saturn' as the ruling archetype of the black domain.
    Pairs with 'hermes' routing in opacity.py.

    Parameters
    ----------
    fire_type : str

    Returns
    -------
    str
    """
    fire_type = str(fire_type).strip() if fire_type else ""
    return _SATURN_ARCHETYPES.get(fire_type, _SATURN_ARCHETYPES["dim_black"])
