# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/black/transparency.py
====================================
BLACK — Transparency Layer

The visible, open-field black signals: dissolution, void, prima materia,
Nigredo activation, and SENTINEL alerts around system null and void absolute.

Transparency in black is paradoxical — black conceals by nature.
What is visible here is the signal of dissolution itself: the presence
of the absence, the form that announces formlessness.

Reference: docs/color/BLACK_TRANSPARENCY.md
           Obsidian Tablet — docs/tablets/OBSIDIAN_TABLET.md
           Shadow Tablet   — docs/tablets/SHADOW_TABLET.md
"""

from __future__ import annotations

from .constants import (
    SENTINEL_LEVEL_HEX,
    SENTINEL_LEVEL_LABEL,
    UI_STATES,
)


# ---------------------------------------------------------------------------
# Nigredo State Detection
# ---------------------------------------------------------------------------

def detect_nigredo_state(coherence_metrics: dict) -> bool:
    """
    Evaluate whether GAIAN is at genuine Nigredo (Stage I).

    Authentic Nigredo requires:
      - dissolution  >= 0.80  (the material is genuinely dissolving)
      - void_contact >= 0.70  (contact with the formless has been made)
      - containment  >= 0.55  (the dissolution is held, not chaotic)

    Containment is the discriminating factor — void absolute presents
    dissolution and void contact but has no containing structure.

    Parameters
    ----------
    coherence_metrics : dict
        Keys: 'dissolution', 'void_contact', 'containment'.
        Missing keys treated as 0.0.

    Returns
    -------
    bool
    """
    if not coherence_metrics:
        return False

    dissolution  = float(coherence_metrics.get("dissolution",  0.0))
    void_contact = float(coherence_metrics.get("void_contact", 0.0))
    containment  = float(coherence_metrics.get("containment",  0.0))

    return dissolution >= 0.80 and void_contact >= 0.70 and containment >= 0.55


# ---------------------------------------------------------------------------
# SENTINEL Alert Emission
# ---------------------------------------------------------------------------

def emit_sentinel_alert(level: int, context: str) -> dict:
    """
    Fire a SENTINEL black alert.

    Parameters
    ----------
    level : int
        1 = DEEP_VOID, 2 = SHADOW_EDGE, 3 = SYSTEM_NULL.
        Values outside [1, 3] are clamped.
    context : str

    Returns
    -------
    dict
        level, label, hex, context, layer, tablets.
    """
    level = max(1, min(3, int(level))) if level else 1
    context = str(context) if context else ""

    return {
        "level":   level,
        "label":   SENTINEL_LEVEL_LABEL[level],
        "hex":     SENTINEL_LEVEL_HEX[level],
        "context": context,
        "layer":   "transparency",
        "tablets": ["Obsidian Tablet", "Shadow Tablet"],
    }


# ---------------------------------------------------------------------------
# Urgency Classification
# ---------------------------------------------------------------------------

def classify_urgency(signal: dict) -> str:
    """
    Route an incoming signal to a BLACK urgency tier.

    Routing logic (priority order):
      1. 'nigredo'      — signal carries 'nigredo': True
      2. 'system_null'  — signal carries 'system_null': True
      3. 'void'         — signal carries 'void': True
      4. 'alert'        — default

    Parameters
    ----------
    signal : dict

    Returns
    -------
    str
    """
    if not signal:
        return "alert"

    if signal.get("nigredo"):
        return "nigredo"
    if signal.get("system_null"):
        return "system_null"
    if signal.get("void"):
        return "void"
    return "alert"


# ---------------------------------------------------------------------------
# UI State
# ---------------------------------------------------------------------------

def get_ui_state(state_type: str) -> dict:
    """
    Return the correct hex, animation style, and semantic label for a
    Black UI state.

    Parameters
    ----------
    state_type : str
        One of: 'nigredo_activation', 'sentinel_alert', 'system_null_state',
        'prima_materia_mode', 'void_absolute'.

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
            f"Unknown Black UI state '{state_type}'. "
            f"Valid states: {list(UI_STATES.keys())}"
        )
    return dict(UI_STATES[state_type])


# ---------------------------------------------------------------------------
# Void Signal Discrimination
# ---------------------------------------------------------------------------

def is_void_signal(signal: dict) -> bool:
    """
    Determine whether a signal is a genuine void (Nigredo) signal
    versus a system_null or destruction signal.

    Genuine void signal:
      - carries 'nigredo': True
      - does NOT carry 'system_null': True
      - does NOT carry 'destruction': True

    Parameters
    ----------
    signal : dict

    Returns
    -------
    bool
    """
    if not signal:
        return False

    nigredo     = bool(signal.get("nigredo",     False))
    system_null = bool(signal.get("system_null", False))
    destruction = bool(signal.get("destruction", False))

    return nigredo and not system_null and not destruction
