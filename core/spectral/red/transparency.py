"""
core/spectral/red/transparency.py
==================================
RED — Transparency Layer
The open-field red signals: urgency, vitality, peak activation,
Rubedo state, and SENTINEL alerts.

Transparency is the visible surface of red — signals that fire in full
light, making no attempt at concealment.

Reference: docs/color/RED_TRANSPARENCY.md — Section 2 (UI/Design) and
           Section 5 (GAIA Canon). Ruby Tablet — Law of the Living Flame.
"""

from __future__ import annotations

from .constants import (
    SENTINEL_LEVEL_HEX,
    SENTINEL_LEVEL_LABEL,
    UI_STATES,
)

# ---------------------------------------------------------------------------
# Rubedo State Detection
# ---------------------------------------------------------------------------

def detect_rubedo_state(coherence_metrics: dict) -> bool:
    """
    Evaluate whether GAIAN is at peak Rubedo.

    Rubedo requires simultaneous convergence of:
      - coherence   >= 0.85
      - integration >= 0.80
      - actualization >= 0.75

    Parameters
    ----------
    coherence_metrics : dict
        Must contain keys: 'coherence', 'integration', 'actualization'.
        Missing keys are treated as 0.0.

    Returns
    -------
    bool
        True when all three thresholds are met.
    """
    if not coherence_metrics:
        return False

    coherence      = float(coherence_metrics.get("coherence",      0.0))
    integration    = float(coherence_metrics.get("integration",    0.0))
    actualization  = float(coherence_metrics.get("actualization",  0.0))

    return coherence >= 0.85 and integration >= 0.80 and actualization >= 0.75


# ---------------------------------------------------------------------------
# SENTINEL Alert Emission
# ---------------------------------------------------------------------------

def emit_sentinel_alert(level: int, context: str) -> dict:
    """
    Fire a SENTINEL red alert.

    Parameters
    ----------
    level : int
        Alert severity: 1 = ALERT, 2 = DANGER, 3 = SCARLET.
        Values outside [1, 3] are clamped.
    context : str
        Human-readable description of the triggering condition.

    Returns
    -------
    dict
        Structured alert payload with keys:
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
        "tablet":  "Ruby Tablet",
    }


# ---------------------------------------------------------------------------
# Urgency Classification
# ---------------------------------------------------------------------------

_URGENCY_TIERS: tuple[str, ...] = (
    "completion",
    "alert",
    "error",
    "living_flame",
)


def classify_urgency(signal: dict) -> str:
    """
    Route an incoming signal to an urgency tier using the transparency layer.
    No shadow-channel reading occurs here.

    Routing logic (priority order):
      1. 'living_flame' — signal carries 'living_flame': True
      2. 'completion'   — signal carries 'completion': True
      3. 'error'        — signal carries 'error': True or 'error_code' present
      4. 'alert'        — default for any red-flagged signal

    Parameters
    ----------
    signal : dict
        Incoming signal payload.

    Returns
    -------
    str
        One of: 'completion', 'alert', 'error', 'living_flame'.
    """
    if not signal:
        return "alert"

    if signal.get("living_flame"):
        return "living_flame"
    if signal.get("completion"):
        return "completion"
    if signal.get("error") or signal.get("error_code"):
        return "error"
    return "alert"


# ---------------------------------------------------------------------------
# UI State
# ---------------------------------------------------------------------------

def get_ui_state(state_type: str) -> dict:
    """
    Return the correct hex, animation style, and semantic label for a
    Red UI state.

    Parameters
    ----------
    state_type : str
        One of: 'rubedo_activation', 'sentinel_alert', 'completion_signal',
        'error_state', 'living_flame_mode'.

    Returns
    -------
    dict
        {'hex': str, 'animation': str, 'label': str}

    Raises
    ------
    KeyError
        If state_type is not a registered UI state.  Caller should handle.
    """
    state_type = str(state_type).strip() if state_type else ""
    if state_type not in UI_STATES:
        raise KeyError(
            f"Unknown Red UI state '{state_type}'. "
            f"Valid states: {list(UI_STATES.keys())}"
        )
    return dict(UI_STATES[state_type])  # return copy; never mutate constants


# ---------------------------------------------------------------------------
# Completion vs SENTINEL Discrimination
# ---------------------------------------------------------------------------

def is_completion_signal(signal: dict) -> bool:
    """
    Distinguish Rubedo completion from SENTINEL danger.
    Both are red; they are semantically opposite.

    Completion is marked by:
      - signal['completion'] == True
      - No 'sentinel' key set to True
      - No 'error' key set to True

    Parameters
    ----------
    signal : dict
        Incoming signal payload.

    Returns
    -------
    bool
    """
    if not signal:
        return False

    completion = bool(signal.get("completion", False))
    sentinel   = bool(signal.get("sentinel",   False))
    error      = bool(signal.get("error",      False))

    return completion and not sentinel and not error
