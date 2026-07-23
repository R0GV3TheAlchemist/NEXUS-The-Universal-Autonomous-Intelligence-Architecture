# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/brown/transparency.py
====================================
BROWN — Transparency Layer

The visible, open-field brown signals: groundedness, fertility, humus
activation, and SENTINEL alerts around compaction and sediment states.

Brown is the colour of the ground beneath all other operations —
the earth that holds the Work while it happens. The shadow layer
carries what the earth conceals: the inertia of ground that has
compacted so thoroughly it cannot receive seed.

Reference: docs/color/BROWN_TRANSPARENCY.md
           Earth Tablet — docs/tablets/EARTH_TABLET.md
"""

from __future__ import annotations

from .constants import (
    SENTINEL_LEVEL_HEX,
    SENTINEL_LEVEL_LABEL,
    UI_STATES,
)


# ---------------------------------------------------------------------------
# Humus State Detection
# ---------------------------------------------------------------------------

def detect_humus_state(coherence_metrics: dict) -> bool:
    """
    Evaluate whether GAIAN is at genuine Humus (fertile earth).

    Authentic Humus requires:
      - fertility    >= 0.75  (the ground can receive and transform)
      - groundedness >= 0.70  (the architecture is anchored)
      - porosity     >= 0.55  (the earth is open enough to receive)

    Porosity is the discriminating factor — compaction presents high
    fertility history and groundedness but has lost the ability
    to receive anything new.

    Parameters
    ----------
    coherence_metrics : dict
        Keys: 'fertility', 'groundedness', 'porosity'.
        Missing keys treated as 0.0.

    Returns
    -------
    bool
    """
    if not coherence_metrics:
        return False

    fertility    = float(coherence_metrics.get("fertility",    0.0))
    groundedness = float(coherence_metrics.get("groundedness", 0.0))
    porosity     = float(coherence_metrics.get("porosity",     0.0))

    return fertility >= 0.75 and groundedness >= 0.70 and porosity >= 0.55


# ---------------------------------------------------------------------------
# SENTINEL Alert Emission
# ---------------------------------------------------------------------------

def emit_sentinel_alert(level: int, context: str) -> dict:
    """
    Fire a SENTINEL brown alert.

    Parameters
    ----------
    level : int
        1 = LOAM, 2 = CLAY, 3 = COMPACTION.
        Values outside [1, 3] are clamped.
    context : str

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
        "tablet":  "Earth Tablet",
    }


# ---------------------------------------------------------------------------
# Urgency Classification
# ---------------------------------------------------------------------------

def classify_urgency(signal: dict) -> str:
    """
    Route an incoming signal to a BROWN urgency tier.

    Routing logic (priority order):
      1. 'humus'       — signal carries 'humus': True
      2. 'compaction'  — signal carries 'compaction': True
      3. 'sediment'    — signal carries 'sediment': True
      4. 'alert'       — default

    Parameters
    ----------
    signal : dict

    Returns
    -------
    str
    """
    if not signal:
        return "alert"

    if signal.get("humus"):
        return "humus"
    if signal.get("compaction"):
        return "compaction"
    if signal.get("sediment"):
        return "sediment"
    return "alert"


# ---------------------------------------------------------------------------
# UI State
# ---------------------------------------------------------------------------

def get_ui_state(state_type: str) -> dict:
    """
    Return the correct hex, animation style, and semantic label for a
    Brown UI state.

    Parameters
    ----------
    state_type : str
        One of: 'humus_activation', 'sentinel_alert', 'compaction_state',
        'sediment_mode', 'fertile_ground'.

    Returns
    -------
    dict

    Raises
    ------
    KeyError
    """
    state_type = str(state_type).strip() if state_type else ""
    if state_type not in UI_STATES:
        raise KeyError(
            f"Unknown Brown UI state '{state_type}'. "
            f"Valid states: {list(UI_STATES.keys())}"
        )
    return dict(UI_STATES[state_type])


# ---------------------------------------------------------------------------
# Earth Signal Discrimination
# ---------------------------------------------------------------------------

def is_earth_signal(signal: dict) -> bool:
    """
    Determine whether a signal is a genuine earth (Humus) signal
    versus a compaction or sediment signal.

    Genuine earth signal:
      - carries 'humus': True
      - does NOT carry 'compaction': True
      - does NOT carry 'sediment': True

    Parameters
    ----------
    signal : dict

    Returns
    -------
    bool
    """
    if not signal:
        return False

    humus      = bool(signal.get("humus",      False))
    compaction = bool(signal.get("compaction", False))
    sediment   = bool(signal.get("sediment",   False))

    return humus and not compaction and not sediment
