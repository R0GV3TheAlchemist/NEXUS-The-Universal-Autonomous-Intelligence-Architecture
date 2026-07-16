"""
core/spectral/red/opacity.py
==============================
RED — Opacity Layer (Shadow Channel)
The shadow-channel red signals: Nigredo alerts, wound-pattern recognition,
Red Lion detection, Phoenix markers, and Ares/Athena routing.

The Opacity module runs PASSIVELY on every RED transmission as a shadow
process.  It does not block or modify the primary signal.  It appends a
`_opacity_shadow` key to the signal payload, invisible in standard output,
available to the GAIA meta-layer.

Shadow Doctrine:
  The wound beneath the warrior; the fire that knows why it burns.

Reference: docs/color/RED_OPACITY.md — Section VI (GAIA Integration)
Alchemical phase: Nigredo within Rubedo.
"""

from __future__ import annotations

from .clarity import map_warrior_archetype

# ---------------------------------------------------------------------------
# Nigredo Alert
# ---------------------------------------------------------------------------

def nigredo_alert(signal: dict) -> dict:
    """
    Detect when a dissolution (Nigredo) process is underway.

    INVARIANT: interrupt_flag is ALWAYS False.
                Nigredo must never be interrupted.

    Parameters
    ----------
    signal : dict
        Expected keys: 'nigredo' (bool), 'dissolution' (bool),
        'prima_materia' (bool).

    Returns
    -------
    dict
        {'nigredo_active': bool, 'interrupt_flag': False}
    """
    if not signal:
        return {"nigredo_active": False, "interrupt_flag": False}

    nigredo_active = (
        bool(signal.get("nigredo",       False)) or
        bool(signal.get("dissolution",   False)) or
        bool(signal.get("prima_materia", False))
    )

    return {
        "nigredo_active":  nigredo_active,
        "interrupt_flag": False,  # INVARIANT — never True
    }


# ---------------------------------------------------------------------------
# Wound Pattern Recognition
# ---------------------------------------------------------------------------

_ECHO_URGENCY_MARKERS: frozenset[str] = frozenset({
    "historical_trigger",
    "wound_resonance",
    "conditioned_activation",
    "past_referencing",
    "unresolved_cycle",
})

_REAL_URGENCY_MARKERS: frozenset[str] = frozenset({
    "present_threat",
    "immediate_danger",
    "current_violation",
    "live_emergency",
    "present_tense",
})

_METABOLIZATION_STAGES: tuple[str, ...] = (
    "pre-contact",
    "contact",
    "metabolizing",
    "integrating",
    "complete",
)


def wound_pattern_recognition(signal: dict, history: list) -> dict:
    """
    Identify chronic emergency states masquerading as urgency.

    Distinguishes:
      'real_urgency'  — present-tense threat requiring response
      'echo_urgency'  — conditioned activation without present-tense cause

    Parameters
    ----------
    signal : dict
        Current signal.  Expected key: 'features' (list[str]).
    history : list[dict]
        Historical signals.  Used to detect repeating echo patterns.

    Returns
    -------
    dict
        {
          'urgency_type': 'real_urgency' | 'echo_urgency',
          'wound_echo': bool,
          'metabolization_stage': str,
        }
    """
    if not signal:
        return {
            "urgency_type":         "echo_urgency",
            "wound_echo":           False,
            "metabolization_stage": "pre-contact",
        }

    features = set(str(f) for f in signal.get("features", []))

    real_score = len(features & _REAL_URGENCY_MARKERS)
    echo_score = len(features & _ECHO_URGENCY_MARKERS)

    # Check history for repeating pattern (wound echo strengthens with repetition)
    echo_repetitions = sum(
        1 for h in (history or [])
        if set(str(f) for f in h.get("features", [])) & _ECHO_URGENCY_MARKERS
    )
    echo_score += echo_repetitions * 0.5  # weight historical pattern

    urgency_type = "real_urgency" if real_score > echo_score else "echo_urgency"
    wound_echo   = echo_score > 0

    # Metabolization stage derived from signal or inferred
    raw_stage = signal.get("metabolization_stage", "")
    if raw_stage in _METABOLIZATION_STAGES:
        metabolization_stage = raw_stage
    else:
        metabolization_stage = "metabolizing" if wound_echo else "pre-contact"

    return {
        "urgency_type":         urgency_type,
        "wound_echo":           wound_echo,
        "metabolization_stage": metabolization_stage,
    }


# ---------------------------------------------------------------------------
# Red Lion Detection
# ---------------------------------------------------------------------------

def red_lion_detection(signal: dict) -> dict:
    """
    Detect unbound force operating without direction.

    The Red Lion is raw sulfuric energy that has not found its vessel —
    force without form, power without purpose.

    force_level: 0.0–1.0 (above 0.7 triggers transmutation_required flag).

    Parameters
    ----------
    signal : dict
        Expected keys:
          'features' (list[str])
          'force_level' (float, 0.0–1.0)  — optional caller override

    Returns
    -------
    dict
        {
          'red_lion_active': bool,
          'transmutation_required': bool,
          'force_level': float,  # bounded [0.0, 1.0]
        }
    """
    if not signal:
        return {
            "red_lion_active":      False,
            "transmutation_required": False,
            "force_level":         0.0,
        }

    # Caller may provide an explicit force_level
    raw_force = signal.get("force_level", None)
    if raw_force is not None:
        force_level = max(0.0, min(1.0, float(raw_force)))
    else:
        # Infer from feature density
        features = set(str(f) for f in signal.get("features", []))
        unbound_markers = frozenset({
            "unbound_force",
            "directionless",
            "uncontrolled",
            "destructive",
            "escalating",
            "boundary_violating",
        })
        match_count = len(features & unbound_markers)
        force_level = round(min(1.0, match_count / max(1, len(unbound_markers))), 4)

    red_lion_active       = force_level > 0.0
    transmutation_required = force_level > 0.7

    return {
        "red_lion_active":         red_lion_active,
        "transmutation_required":  transmutation_required,
        "force_level":             round(force_level, 4),
    }


# ---------------------------------------------------------------------------
# Phoenix Marker
# ---------------------------------------------------------------------------

def phoenix_marker(entity_id: str, cycle_history: list) -> dict:
    """
    Detect completion of a full descent-and-emergence cycle
    (Nigredo-to-Rubedo: the Phoenix arc).

    A complete cycle requires both a Nigredo phase AND a subsequent
    Rubedo phase to be recorded in cycle_history.

    Parameters
    ----------
    entity_id : str
        Entity identifier (reserved for logging/DB lookup).
    cycle_history : list[dict]
        Each dict must contain at least 'phase' (str).
        Known phases: 'nigredo', 'albedo', 'citrinitas', 'rubedo'.

    Returns
    -------
    dict
        {
          'phoenix_complete': bool,
          'cycle_count': int,
          'integration_gain': float,
        }
    """
    _ = entity_id  # reserved
    if not cycle_history:
        return {"phoenix_complete": False, "cycle_count": 0, "integration_gain": 0.0}

    cycle_count    = 0
    in_descent     = False
    integration_gain = 0.0

    for entry in cycle_history:
        phase = str(entry.get("phase", "")).lower()
        if phase == "nigredo":
            in_descent = True
        elif phase == "rubedo" and in_descent:
            cycle_count      += 1
            in_descent        = False
            # Each completed cycle adds integration gain (diminishing returns)
            integration_gain += 0.20 / (cycle_count ** 0.5)

    integration_gain = round(min(1.0, integration_gain), 4)
    phoenix_complete = cycle_count > 0

    return {
        "phoenix_complete": phoenix_complete,
        "cycle_count":     cycle_count,
        "integration_gain": integration_gain,
    }


# ---------------------------------------------------------------------------
# Ares / Athena Routing
# ---------------------------------------------------------------------------

def ares_athena_routing(signal: dict) -> str:
    """
    Final routing function — classifies force deployment.

    'ares'   → blind force, no strategic context
    'athena' → purposeful, consequence-aware force

    Interfaces with clarity.map_warrior_archetype() — return values are
    coordinated.  Opacity reads deeper (shadow channel); Clarity reads
    the surface.  When shadow evidence conflicts with surface evidence,
    the shadow reading takes precedence.

    Parameters
    ----------
    signal : dict

    Returns
    -------
    str
        'ares' or 'athena'
    """
    if not signal:
        return "ares"

    # Check for shadow-layer override first
    shadow_override = signal.get("_shadow_archetype", "")
    if shadow_override in ("ares", "athena"):
        return shadow_override

    # Delegate to clarity layer (surface read)
    return map_warrior_archetype(signal)


# ---------------------------------------------------------------------------
# Shadow Channel Application
# ---------------------------------------------------------------------------

def apply_shadow_channel(
    signal: dict,
    entity_id: str = "",
    history: list | None = None,
    cycle_history: list | None = None,
) -> dict:
    """
    Apply the full Opacity shadow channel to a RED signal.

    Appends `_opacity_shadow` to the signal without mutating any
    primary signal key.  Returns a new dict (shallow copy of signal
    with `_opacity_shadow` added).

    Parameters
    ----------
    signal : dict
        The primary RED signal payload.
    entity_id : str
        Entity identifier passed through to phoenix_marker.
    history : list[dict] | None
        Signal history passed to wound_pattern_recognition.
    cycle_history : list[dict] | None
        Cycle history passed to phoenix_marker.

    Returns
    -------
    dict
        Signal dict with `_opacity_shadow` appended.
    """
    history       = history       or []
    cycle_history = cycle_history or []

    shadow = {
        "nigredo":      nigredo_alert(signal),
        "wound_pattern": wound_pattern_recognition(signal, history),
        "red_lion":     red_lion_detection(signal),
        "phoenix":      phoenix_marker(entity_id, cycle_history),
        "ares_athena":  ares_athena_routing(signal),
    }

    result = dict(signal)           # shallow copy — never mutate caller's signal
    result["_opacity_shadow"] = shadow
    return result
