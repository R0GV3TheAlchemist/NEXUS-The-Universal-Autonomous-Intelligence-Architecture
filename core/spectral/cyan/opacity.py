# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/cyan/opacity.py
==============================
CYAN — Opacity Layer

Opacity holds what the dissolving medium conceals from itself:
the flood that presents as flow, the universal solvent that has
lost the distinction between what should dissolve and what should hold.

Architecture invariants (MUST be preserved):
  1. _cyan_opacity_shadow is APPEND-ONLY — never mutate existing entries.
  2. interrupt_flag CANNOT be set True by any function in this module.
     The cyan shadow accumulates — it does not interrupt.

Shared vocabulary:
  - 'mercury' — the ruling archetype of the cyan domain (clarity.py)
  - 'hermes'  — the messenger/routing principle (shared across modules)

Reference: docs/color/CYAN_OPACITY.md
           Aqua Tablet — docs/tablets/AQUA_TABLET.md
"""

from __future__ import annotations

import time

# ---------------------------------------------------------------------------
# Shadow Channel — append-only accumulator
# ---------------------------------------------------------------------------

_cyan_opacity_shadow: list[dict] = []


def _append_shadow(entry: dict) -> None:
    """Internal helper — appends to shadow list, NEVER mutates existing entries."""
    _cyan_opacity_shadow.append({
        **entry,
        "timestamp": time.time(),
        "interrupt_flag": False,  # invariant: always False
    })


# ---------------------------------------------------------------------------
# Flood Alert
# ---------------------------------------------------------------------------

def flood_alert(signal: dict) -> dict:
    """
    Emit a flood opacity alert and append to shadow channel.

    Flood is detected when dissolution is high and reformation is absent.

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        type, severity, detail, interrupt_flag (always False).
    """
    signal = signal or {}
    dissolution = float(signal.get("dissolution", 0.0))
    reformation = float(signal.get("reformation", 1.0))

    severity = "critical" if (dissolution >= 0.80 and reformation < 0.25) else "high"

    alert = {
        "type":           "flood_alert",
        "severity":       severity,
        "detail":         "Dissolution detected without reformation — Flood pattern.",
        "source_signal":  signal,
        "interrupt_flag": False,  # invariant
    }
    _append_shadow(alert)
    return alert


# ---------------------------------------------------------------------------
# Network Noise Pattern Recognition
# ---------------------------------------------------------------------------

def network_noise_pattern_recognition(signal_history: list[dict]) -> dict:
    """
    Detect network noise patterns across a history of signals.

    A noise pattern is confirmed when:
      - 3 or more consecutive signals carry 'network_noise': True
      - No signal in that streak has 'signal_clarity' >= 0.50

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
        is_noise   = bool(s.get("network_noise",  False))
        clarity_ok = float(s.get("signal_clarity", 0.0)) >= 0.50
        if is_noise and not clarity_ok:
            streak += 1
        else:
            break

    result = {
        "pattern_detected": streak >= 3,
        "streak_length":    streak,
        "interrupt_flag":   False,
    }
    _append_shadow({"network_noise_pattern": result})
    return result


# ---------------------------------------------------------------------------
# Universal Solvent Detection
# ---------------------------------------------------------------------------

def universal_solvent_detection(signal: dict) -> dict:
    """
    Detect whether the dissolution medium has become a universal solvent —
    dissolving the container along with the content.

    Universal solvent markers:
      - 'dissolution' >= 0.85
      - 'selectivity' < 0.30  (not discriminating what to dissolve)

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        universal_solvent, dissolution, selectivity, interrupt_flag (False).
    """
    signal = signal or {}

    dissolution = float(signal.get("dissolution", 0.0))
    selectivity = float(signal.get("selectivity", 1.0))

    universal = dissolution >= 0.85 and selectivity < 0.30

    result = {
        "universal_solvent": universal,
        "dissolution":       dissolution,
        "selectivity":       selectivity,
        "interrupt_flag":    False,
    }
    _append_shadow({"universal_solvent": result})
    return result


# ---------------------------------------------------------------------------
# Akashic Overload Marker
# ---------------------------------------------------------------------------

def akashic_overload_marker(signal: dict) -> dict:
    """
    Mark a signal as Akashic overload — retrieval returning so much
    that it returns effectively nothing.

    Overload markers:
      - 'retrieval_volume' > 0.90
      - 'retrieval_precision' < 0.35

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        akashic_overload, retrieval_volume, retrieval_precision, interrupt_flag (False).
    """
    signal = signal or {}

    retrieval_volume    = float(signal.get("retrieval_volume",    0.0))
    retrieval_precision = float(signal.get("retrieval_precision", 1.0))

    overload = retrieval_volume > 0.90 and retrieval_precision < 0.35

    result = {
        "akashic_overload":    overload,
        "retrieval_volume":    retrieval_volume,
        "retrieval_precision": retrieval_precision,
        "interrupt_flag":      False,
    }
    _append_shadow({"akashic_overload": result})
    return result


# ---------------------------------------------------------------------------
# Mercury-Hermes Routing
# ---------------------------------------------------------------------------

def mercury_hermes_routing(signal: dict) -> dict:
    """
    Route a cyan signal using the mercury/hermes shared vocabulary.

    'mercury' — the archetype of the cyan domain (rules)
    'hermes'  — the messenger principle (routes)

    Routing table:
      - solutio          → hermes routes to 'dissolution_integration'
      - flood            → hermes routes to 'container_restoration'
      - akashic_overload → hermes routes to 'retrieval_precision_audit'
      - default          → hermes routes to 'cyan_holding'

    Parameters
    ----------
    signal : dict

    Returns
    -------
    dict
        archetype, messenger, route, interrupt_flag (False).
    """
    signal = signal or {}

    if signal.get("solutio"):
        route = "dissolution_integration"
    elif signal.get("flood"):
        route = "container_restoration"
    elif signal.get("akashic_overload"):
        route = "retrieval_precision_audit"
    else:
        route = "cyan_holding"

    result = {
        "archetype":      "mercury",
        "messenger":      "hermes",
        "route":          route,
        "interrupt_flag": False,
    }
    _append_shadow({"mercury_hermes_routing": result})
    return result


# ---------------------------------------------------------------------------
# Shadow Channel Integration
# ---------------------------------------------------------------------------

def apply_shadow_channel(signal: dict) -> dict:
    """
    Apply the full cyan opacity shadow channel to a signal.

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

    findings.append(flood_alert(signal))
    findings.append(universal_solvent_detection(signal))
    findings.append(akashic_overload_marker(signal))
    findings.append(mercury_hermes_routing(signal))

    return {
        "original_signal": dict(signal),
        "shadow_findings":  findings,
        "interrupt_flag":   False,
    }
