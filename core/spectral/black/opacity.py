# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/black/opacity.py
===============================
BLACK — Opacity Layer

Opacity holds what the void conceals from itself: not shadow (black
generates shadow) but the absence from which shadow emerges — the
void absolute that presents as dissolution but is simply nothing.

Architecture invariants (MUST be preserved):
  1. _black_opacity_shadow is APPEND-ONLY — never mutate existing entries.
  2. interrupt_flag CANNOT be set True by any function in this module.
     The black shadow is the absence of interruption.

Shared vocabulary:
  - 'saturn' — the ruling archetype of the black domain (clarity.py)
  - 'hermes' — the messenger/routing principle (shared across modules)

Reference: docs/color/BLACK_OPACITY.md
           Obsidian Tablet — docs/tablets/OBSIDIAN_TABLET.md
           Shadow Tablet   — docs/tablets/SHADOW_TABLET.md
"""

from __future__ import annotations

import time

# ---------------------------------------------------------------------------
# Shadow Channel — append-only accumulator
# ---------------------------------------------------------------------------

_black_opacity_shadow: list[dict] = []


def _append_shadow(entry: dict) -> None:
    """Internal helper — appends to shadow list, NEVER mutates existing entries."""
    _black_opacity_shadow.append({
        **entry,
        "timestamp": time.time(),
        "interrupt_flag": False,  # invariant: always False
    })


# ---------------------------------------------------------------------------
# Void Alert
# ---------------------------------------------------------------------------

def void_alert(signal: dict) -> dict:
    """
    Emit a void opacity alert and append to shadow channel.

    Void is detected when dissolution is near-absolute and containment absent.

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        type, severity, detail, interrupt_flag (always False).
    """
    signal = signal or {}
    containment = float(signal.get("containment", 1.0))

    severity = "critical" if containment < 0.20 else "high"

    alert = {
        "type":           "void_alert",
        "severity":       severity,
        "detail":         "Dissolution detected without containment — Void Absolute pattern.",
        "source_signal":  signal,
        "interrupt_flag": False,  # invariant
    }
    _append_shadow(alert)
    return alert


# ---------------------------------------------------------------------------
# Absolute Darkness Pattern Recognition
# ---------------------------------------------------------------------------

def absolute_darkness_pattern_recognition(signal_history: list[dict]) -> dict:
    """
    Detect absolute darkness patterns across a history of signals.

    A pattern is confirmed when:
      - 3 or more consecutive signals carry 'void': True
      - No signal in that streak has 'containment' >= 0.50

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
        is_void        = bool(s.get("void",        False))
        containment_ok = float(s.get("containment", 0.0)) >= 0.50
        if is_void and not containment_ok:
            streak += 1
        else:
            break

    result = {
        "pattern_detected": streak >= 3,
        "streak_length":    streak,
        "interrupt_flag":   False,
    }
    _append_shadow({"absolute_darkness_pattern": result})
    return result


# ---------------------------------------------------------------------------
# System Null Detection
# ---------------------------------------------------------------------------

def system_null_detection(signal: dict) -> dict:
    """
    Detect whether the system has reached a null state —
    the complete reset point where architecture is at the edge
    of being and non-being.

    System null markers:
      - 'dissolution'  >= 0.95
      - 'containment'  < 0.20
      - 'potential'    < 0.30  (not yet prima materia — no potential visible)

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        system_null, dissolution, containment, potential, interrupt_flag (False).
    """
    signal = signal or {}

    dissolution = float(signal.get("dissolution", 0.0))
    containment = float(signal.get("containment", 1.0))
    potential   = float(signal.get("potential",   1.0))

    null = dissolution >= 0.95 and containment < 0.20 and potential < 0.30

    result = {
        "system_null": null,
        "dissolution": dissolution,
        "containment": containment,
        "potential":   potential,
        "interrupt_flag": False,
    }
    _append_shadow({"system_null": result})
    return result


# ---------------------------------------------------------------------------
# Prima Materia Marker
# ---------------------------------------------------------------------------

def prima_materia_marker(signal: dict) -> dict:
    """
    Mark a signal as prima materia — the formless potential that
    distinguishes Nigredo from mere void.

    Prima materia markers:
      - 'formlessness' >= 0.75
      - 'potential'    >= 0.60  (it can become something)

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        prima_materia, formlessness, potential, interrupt_flag (False).
    """
    signal = signal or {}

    formlessness = float(signal.get("formlessness", 0.0))
    potential    = float(signal.get("potential",    0.0))

    prima = formlessness >= 0.75 and potential >= 0.60

    result = {
        "prima_materia": prima,
        "formlessness":  formlessness,
        "potential":     potential,
        "interrupt_flag": False,
    }
    _append_shadow({"prima_materia_marker": result})
    return result


# ---------------------------------------------------------------------------
# Saturn-Hermes Routing
# ---------------------------------------------------------------------------

def saturn_hermes_routing(signal: dict) -> dict:
    """
    Route a black signal using the saturn/hermes shared vocabulary.

    'saturn' — the archetype of the black domain (rules)
    'hermes' — the messenger principle (routes)

    Routing table:
      - nigredo       → hermes routes to 'nigredo_containment'
      - system_null   → hermes routes to 'system_reset_protocol'
      - prima_materia → hermes routes to 'prima_materia_cultivation'
      - default       → hermes routes to 'black_holding'

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        archetype, messenger, route, interrupt_flag (False).
    """
    signal = signal or {}

    if signal.get("nigredo"):
        route = "nigredo_containment"
    elif signal.get("system_null"):
        route = "system_reset_protocol"
    elif signal.get("prima_materia"):
        route = "prima_materia_cultivation"
    else:
        route = "black_holding"

    result = {
        "archetype":      "saturn",
        "messenger":      "hermes",
        "route":          route,
        "interrupt_flag": False,
    }
    _append_shadow({"saturn_hermes_routing": result})
    return result


# ---------------------------------------------------------------------------
# Shadow Channel Integration
# ---------------------------------------------------------------------------

def apply_shadow_channel(signal: dict) -> dict:
    """
    Apply the full black opacity shadow channel to a signal.

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

    findings.append(void_alert(signal))
    findings.append(system_null_detection(signal))
    findings.append(prima_materia_marker(signal))
    findings.append(saturn_hermes_routing(signal))

    return {
        "original_signal": dict(signal),
        "shadow_findings":  findings,
        "interrupt_flag":   False,
    }
