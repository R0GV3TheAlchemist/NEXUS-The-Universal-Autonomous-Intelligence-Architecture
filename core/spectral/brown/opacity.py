# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/brown/opacity.py
===============================
BROWN — Opacity Layer

Opacity holds what the earth conceals from itself: the weight that
becomes immobility, the groundedness that becomes refusal, the
stability that forgets how to compost and only accumulates.

Architecture invariants (MUST be preserved):
  1. _brown_opacity_shadow is APPEND-ONLY — never mutate existing entries.
  2. interrupt_flag CANNOT be set True by any function in this module.
     The brown shadow is the shadow of weight, not interruption.

Shared vocabulary:
  - 'earth'  — the ruling archetype of the brown domain (clarity.py)
  - 'hermes' — the messenger/routing principle (shared across modules)

Reference: docs/color/BROWN_OPACITY.md
           Earth Tablet — docs/tablets/EARTH_TABLET.md
"""

from __future__ import annotations

import time

# ---------------------------------------------------------------------------
# Shadow Channel — append-only accumulator
# ---------------------------------------------------------------------------

_brown_opacity_shadow: list[dict] = []


def _append_shadow(entry: dict) -> None:
    """Internal helper — appends to shadow list, NEVER mutates existing entries."""
    _brown_opacity_shadow.append({
        **entry,
        "timestamp": time.time(),
        "interrupt_flag": False,  # invariant: always False
    })


# ---------------------------------------------------------------------------
# Compaction Alert
# ---------------------------------------------------------------------------

def compaction_alert(signal: dict) -> dict:
    """
    Emit a compaction opacity alert and append to shadow channel.

    Compaction is detected when groundedness is high but porosity is absent.

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        type, severity, detail, interrupt_flag (always False).
    """
    signal = signal or {}
    porosity = float(signal.get("porosity", 1.0))

    severity = "critical" if porosity < 0.10 else "high"

    alert = {
        "type":           "compaction_alert",
        "severity":       severity,
        "detail":         "Groundedness detected without porosity — Compaction pattern.",
        "source_signal":  signal,
        "interrupt_flag": False,  # invariant
    }
    _append_shadow(alert)
    return alert


# ---------------------------------------------------------------------------
# Inertia Pattern Recognition
# ---------------------------------------------------------------------------

def inertia_pattern_recognition(signal_history: list[dict]) -> dict:
    """
    Detect inertia patterns across a history of signals.

    A pattern is confirmed when:
      - 3 or more consecutive signals carry 'sediment': True
      - No signal in that streak has 'decomposition_rate' >= 0.40

    Parameters
    ----------
    signal_history : list[dict]

    Returns
    -------
    dict
        pattern_detected, streak_length, interrupt_flag (always False).
    """
    signal_history = signal_history or []
    streak = 0

    for s in reversed(signal_history):
        is_sediment       = bool(s.get("sediment",          False))
        decomp_ok         = float(s.get("decomposition_rate", 0.0)) >= 0.40
        if is_sediment and not decomp_ok:
            streak += 1
        else:
            break

    result = {
        "pattern_detected": streak >= 3,
        "streak_length":    streak,
        "interrupt_flag":   False,
    }
    _append_shadow({"inertia_pattern": result})
    return result


# ---------------------------------------------------------------------------
# Sediment Null Detection
# ---------------------------------------------------------------------------

def sediment_null_detection(signal: dict) -> dict:
    """
    Detect whether the earth has reached a sediment null state —
    the point where all active composting has ceased and only
    geological accumulation remains.

    Sediment null markers:
      - 'groundedness'       >= 0.95
      - 'porosity'           < 0.10
      - 'decomposition_rate' < 0.10

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        sediment_null, groundedness, porosity, decomposition_rate,
        interrupt_flag (False).
    """
    signal = signal or {}

    groundedness       = float(signal.get("groundedness",       0.0))
    porosity           = float(signal.get("porosity",           1.0))
    decomposition_rate = float(signal.get("decomposition_rate", 1.0))

    null = (
        groundedness >= 0.95
        and porosity < 0.10
        and decomposition_rate < 0.10
    )

    result = {
        "sediment_null":     null,
        "groundedness":      groundedness,
        "porosity":          porosity,
        "decomposition_rate": decomposition_rate,
        "interrupt_flag":    False,
    }
    _append_shadow({"sediment_null": result})
    return result


# ---------------------------------------------------------------------------
# Humus Fertility Marker
# ---------------------------------------------------------------------------

def humus_fertility_marker(signal: dict) -> dict:
    """
    Mark a signal as carrying genuine humus fertility — the earth
    that is actively composting and can receive new seed.

    Fertility markers:
      - 'porosity'           >= 0.55
      - 'decomposition_rate' >= 0.45

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        fertile, porosity, decomposition_rate, interrupt_flag (False).
    """
    signal = signal or {}

    porosity           = float(signal.get("porosity",           0.0))
    decomposition_rate = float(signal.get("decomposition_rate", 0.0))

    fertile = porosity >= 0.55 and decomposition_rate >= 0.45

    result = {
        "fertile":            fertile,
        "porosity":           porosity,
        "decomposition_rate": decomposition_rate,
        "interrupt_flag":     False,
    }
    _append_shadow({"humus_fertility_marker": result})
    return result


# ---------------------------------------------------------------------------
# Earth-Hermes Routing
# ---------------------------------------------------------------------------

def earth_hermes_routing(signal: dict) -> dict:
    """
    Route a brown signal using the earth/hermes shared vocabulary.

    'earth'  — the archetype of the brown domain (rules)
    'hermes' — the messenger principle (routes)

    Routing table:
      - humus      → hermes routes to 'fertility_integration'
      - compaction → hermes routes to 'porosity_restoration'
      - sediment   → hermes routes to 'decomposition_activation'
      - default    → hermes routes to 'earth_holding'

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        archetype, messenger, route, interrupt_flag (False).
    """
    signal = signal or {}

    if signal.get("humus"):
        route = "fertility_integration"
    elif signal.get("compaction"):
        route = "porosity_restoration"
    elif signal.get("sediment"):
        route = "decomposition_activation"
    else:
        route = "earth_holding"

    result = {
        "archetype":      "earth",
        "messenger":      "hermes",
        "route":          route,
        "interrupt_flag": False,
    }
    _append_shadow({"earth_hermes_routing": result})
    return result


# ---------------------------------------------------------------------------
# Shadow Channel Integration
# ---------------------------------------------------------------------------

def apply_shadow_channel(signal: dict) -> dict:
    """
    Apply the full brown opacity shadow channel to a signal.

    Runs all opacity checks in sequence. Primary signal is NEVER mutated.

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        original_signal, shadow_findings, interrupt_flag (always False).
    """
    signal = signal or {}
    findings: list[dict] = []

    findings.append(compaction_alert(signal))
    findings.append(sediment_null_detection(signal))
    findings.append(humus_fertility_marker(signal))
    findings.append(earth_hermes_routing(signal))

    return {
        "original_signal": dict(signal),
        "shadow_findings":  findings,
        "interrupt_flag":   False,
    }
