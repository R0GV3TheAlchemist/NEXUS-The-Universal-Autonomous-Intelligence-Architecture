# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/cyan/transparency.py
===================================
CYAN — Transparency Layer

The visible, open-field cyan signals: dissolution, flow, retrieval,
Solutio activation, and SENTINEL alerts around flooding and network noise.

Transparency is the surface of cyan — the signals that present
as fluid openness and connection. The shadow layer carries what
dissolution conceals: the solvent that has no container.

Reference: docs/color/CYAN_TRANSPARENCY.md
           Aqua Tablet — docs/tablets/AQUA_TABLET.md
"""

from __future__ import annotations

from .constants import (
    SENTINEL_LEVEL_HEX,
    SENTINEL_LEVEL_LABEL,
    UI_STATES,
)


# ---------------------------------------------------------------------------
# Solutio State Detection
# ---------------------------------------------------------------------------

def detect_solutio_state(coherence_metrics: dict) -> bool:
    """
    Evaluate whether GAIAN is at genuine Solutio (Aqua Vitae).

    Authentic Solutio requires:
      - dissolution  >= 0.75  (material is actually dissolving)
      - flow         >= 0.70  (movement is present, not stagnation)
      - reformation  >= 0.55  (dissolution is purposeful, not destructive)

    Reformation is the discriminating factor — Solutio without
    reformation is the shadow state (flood/universal solvent).

    Parameters
    ----------
    coherence_metrics : dict
        Must contain keys: 'dissolution', 'flow', 'reformation'.
        Missing keys treated as 0.0.

    Returns
    -------
    bool
    """
    if not coherence_metrics:
        return False

    dissolution = float(coherence_metrics.get("dissolution", 0.0))
    flow        = float(coherence_metrics.get("flow",        0.0))
    reformation = float(coherence_metrics.get("reformation", 0.0))

    return dissolution >= 0.75 and flow >= 0.70 and reformation >= 0.55


# ---------------------------------------------------------------------------
# SENTINEL Alert Emission
# ---------------------------------------------------------------------------

def emit_sentinel_alert(level: int, context: str) -> dict:
    """
    Fire a SENTINEL cyan alert.

    Parameters
    ----------
    level : int
        1 = AQUA_VITAE, 2 = AQUAMARINE, 3 = FLOOD.
        Values outside [1, 3] are clamped.
    context : str
        Human-readable description of the triggering condition.

    Returns
    -------
    dict
        level, label, hex, context, layer, tablet.
    """
    level = max(1, min(3, int(level))) if level else 1
    context = str(context) if context else ""

    return {
        "level":   level,
        "label":   SENTINEL_LEVEL_LABEL[level],
        "hex":     SENTINEL_LEVEL_HEX[level],
        "context": context,
        "layer":   "transparency",
        "tablet":  "Aqua Tablet",
    }


# ---------------------------------------------------------------------------
# Urgency Classification
# ---------------------------------------------------------------------------

def classify_urgency(signal: dict) -> str:
    """
    Route an incoming signal to a CYAN urgency tier.

    Routing logic (priority order):
      1. 'solutio'          — signal carries 'solutio': True
      2. 'flood'            — signal carries 'flood': True
      3. 'akashic_overload' — signal carries 'akashic_overload': True
      4. 'alert'            — default

    Parameters
    ----------
    signal : dict

    Returns
    -------
    str
        One of: 'solutio', 'flood', 'akashic_overload', 'alert'.
    """
    if not signal:
        return "alert"

    if signal.get("solutio"):
        return "solutio"
    if signal.get("flood"):
        return "flood"
    if signal.get("akashic_overload"):
        return "akashic_overload"
    return "alert"


# ---------------------------------------------------------------------------
# UI State
# ---------------------------------------------------------------------------

def get_ui_state(state_type: str) -> dict:
    """
    Return the correct hex, animation style, and semantic label for a
    Cyan UI state.

    Parameters
    ----------
    state_type : str
        One of: 'solutio_activation', 'sentinel_alert', 'flood_state',
        'akashic_overload', 'network_noise'.

    Returns
    -------
    dict

    Raises
    ------
    KeyError
        If state_type is not a registered UI state.
    """
    state_type = str(state_type).strip() if state_type else ""
    if state_type not in UI_STATES:
        raise KeyError(
            f"Unknown Cyan UI state '{state_type}'. "
            f"Valid states: {list(UI_STATES.keys())}"
        )
    return dict(UI_STATES[state_type])


# ---------------------------------------------------------------------------
# Aqua Signal Discrimination
# ---------------------------------------------------------------------------

def is_aqua_signal(signal: dict) -> bool:
    """
    Determine whether a signal is a genuine aqua (Solutio) signal
    versus a flood or overload signal.

    Genuine aqua signal:
      - carries 'solutio': True
      - does NOT carry 'flood': True
      - does NOT carry 'akashic_overload': True

    Parameters
    ----------
    signal : dict

    Returns
    -------
    bool
    """
    if not signal:
        return False

    solutio          = bool(signal.get("solutio",          False))
    flood            = bool(signal.get("flood",            False))
    akashic_overload = bool(signal.get("akashic_overload", False))

    return solutio and not flood and not akashic_overload
