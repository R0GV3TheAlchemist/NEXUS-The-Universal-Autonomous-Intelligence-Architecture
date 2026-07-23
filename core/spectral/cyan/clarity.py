# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/cyan/clarity.py
==============================
CYAN — Clarity Layer

Clarity reads what transparency presents and discriminates genuine
Solutio (purposeful dissolution) from flood (dissolution without
reformation) and from Akashic overload (retrieval noise).

The central question of cyan clarity:
  "Is this dissolution in service of transformation,
   or has the solvent consumed the container?"

Reference: docs/color/CYAN_CLARITY.md
           Aqua Tablet — docs/tablets/AQUA_TABLET.md
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Flow vs Flood Discrimination
# ---------------------------------------------------------------------------

def distinguish_flow_flood(signal: dict) -> str:
    """
    Discriminate between purposeful flow (Solutio) and destructive flood.

    Flow is dissolution in service of reformation.
    Flood is dissolution that has consumed the container.

    Decision logic:
      - 'reformation_capacity' >= 0.55 AND 'container_integrity' >= 0.50
        → 'flow'
      - Otherwise → 'flood'

    Parameters
    ----------
    signal : dict
        Must contain: 'reformation_capacity' (float), 'container_integrity' (float).

    Returns
    -------
    str
        'flow' or 'flood'.
    """
    if not signal:
        return "flood"

    reformation_capacity = float(signal.get("reformation_capacity", 0.0))
    container_integrity  = float(signal.get("container_integrity",  0.0))

    if reformation_capacity >= 0.55 and container_integrity >= 0.50:
        return "flow"
    return "flood"


# ---------------------------------------------------------------------------
# Solutio Without Reformation Detection
# ---------------------------------------------------------------------------

def detect_solutio_without_reformation(signal: dict) -> bool:
    """
    Detect the shadow Solutio state — dissolution that is occurring
    but has no reforming principle guiding it.

    Markers:
      - 'dissolution' >= 0.70
      - 'reformation' < 0.40
      - 'container_integrity' < 0.45

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

    dissolution         = float(signal.get("dissolution",         0.0))
    reformation         = float(signal.get("reformation",         1.0))
    container_integrity = float(signal.get("container_integrity", 1.0))

    return (
        dissolution >= 0.70
        and reformation < 0.40
        and container_integrity < 0.45
    )


# ---------------------------------------------------------------------------
# Cyan Fire Classification
# ---------------------------------------------------------------------------

def classify_cyan_fire(signal: dict) -> str:
    """
    Classify the quality of the cyan fire in the signal.

    Cyan fire types (priority order):
      1. 'solutio'                  — peak genuine Aqua Vitae
      2. 'flood'                    — dissolution consuming its container
      3. 'akashic_overload'         — retrieval returning everything, therefore nothing
      4. 'network_noise'            — connection signal degraded by volume
      5. 'dim_aqua'                 — cyan present but barely active

    Parameters
    ----------
    signal : dict

    Returns
    -------
    str
    """
    if not signal:
        return "dim_aqua"

    if signal.get("solutio"):
        return "solutio"
    if signal.get("flood"):
        return "flood"
    if signal.get("akashic_overload"):
        return "akashic_overload"
    if signal.get("network_noise"):
        return "network_noise"
    return "dim_aqua"


# ---------------------------------------------------------------------------
# Aqua Level Assessment
# ---------------------------------------------------------------------------

def assess_aqua_level(signal: dict) -> float:
    """
    Compute a normalised aqua activation level [0.0, 1.0].

    Weighted mean of:
      - dissolution_score    (weight 0.40)
      - reformation_score    (weight 0.35)
      - flow_score           (weight 0.25)

    Parameters
    ----------
    signal : dict

    Returns
    -------
    float  in [0.0, 1.0]
    """
    if not signal:
        return 0.0

    d = float(signal.get("dissolution_score", 0.0))
    r = float(signal.get("reformation_score", 0.0))
    f = float(signal.get("flow_score",        0.0))

    level = (d * 0.40) + (r * 0.35) + (f * 0.25)
    return max(0.0, min(1.0, level))


# ---------------------------------------------------------------------------
# Mercury Archetype Mapping
# ---------------------------------------------------------------------------

_MERCURY_ARCHETYPES: dict[str, str] = {
    "solutio":          "Solutio — the dissolving medium that makes transformation possible",
    "flood":            "Flood — the solvent that consumed its container",
    "akashic_overload": "Akashic Overload — the retrieval that returned everything and therefore nothing",
    "network_noise":    "Network Noise — connection degraded by its own volume",
    "dim_aqua":         "Dim Aqua — the signal barely present beneath the surface",
}


def map_mercury_archetype(fire_type: str) -> str:
    """
    Return the canonical Mercury archetype description for a given fire type.

    Uses shared vocabulary: 'mercury' as the ruling archetype of the cyan domain.
    Pairs with 'hermes' routing in opacity.py.

    Parameters
    ----------
    fire_type : str

    Returns
    -------
    str
    """
    fire_type = str(fire_type).strip() if fire_type else ""
    return _MERCURY_ARCHETYPES.get(fire_type, _MERCURY_ARCHETYPES["dim_aqua"])
