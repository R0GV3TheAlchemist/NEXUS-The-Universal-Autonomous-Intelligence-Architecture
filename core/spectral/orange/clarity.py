# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/spectral/orange/clarity.py
================================
Depth-readable signals for the ORANGE (Citrinitas) spectral layer.
Clarity layer: signals available to authorised interpreters.

Functions
---------
distinguish_ambition_creativity  — Separate ambition-driven from creativity-driven signals.
detect_solar_wound               — Identify suppressed solar/identity wound patterns.
classify_orange_fire             — Classify the quality of the orange fire signal.
assess_solar_integration         — Score how integrated the solar energy is (0.0-1.0).
map_solar_archetype              — Map a signal to a solar archetype label.
"""

from __future__ import annotations
from typing import Any

# Solar archetypes expressed in ORANGE frequency
_SOLAR_ARCHETYPES = {
    "creator":    "The Creator — generative, originative force",
    "sovereign":  "The Sovereign — self-authoring, centred authority",
    "adventurer": "The Adventurer — expansive, risk-embracing explorer",
    "fool":       "The Fool — ungrounded fire, impulsive dispersal",
}


def distinguish_ambition_creativity(signal: dict[str, Any]) -> str:
    """
    Distinguish whether the signal is primarily ambition-driven or creativity-driven.

    Heuristic
    ---------
    - If signal contains "goal" or "achievement" key with a value → "ambition"
    - If signal contains "expression" or "play" key with a value  → "creativity"
    - Both present → "integrated"
    - Neither     → "undifferentiated"
    """
    has_ambition   = bool(signal.get("goal") or signal.get("achievement"))
    has_creativity = bool(signal.get("expression") or signal.get("play"))

    if has_ambition and has_creativity:
        return "integrated"
    if has_ambition:
        return "ambition"
    if has_creativity:
        return "creativity"
    return "undifferentiated"


def detect_solar_wound(signal: dict[str, Any]) -> dict[str, Any]:
    """
    Detect patterns indicative of a suppressed solar / identity wound.

    Returns a dict with:
      wound_detected  : bool
      pattern         : str  — short description of the wound pattern
      severity        : str  — "mild" | "moderate" | "severe"
    """
    patterns: list[tuple[bool, str, str]] = [
        (bool(signal.get("shame")),         "solar shame — identity collapse",    "severe"),
        (bool(signal.get("grandiosity")),   "solar inflation — ego overreach",    "moderate"),
        (bool(signal.get("performance")),   "performance mask — false solar self","moderate"),
        (bool(signal.get("self_doubt")),    "solar doubt — creative paralysis",   "mild"),
    ]

    for detected, pattern, severity in patterns:
        if detected:
            return {"wound_detected": True, "pattern": pattern, "severity": severity}

    return {"wound_detected": False, "pattern": "", "severity": "none"}


def classify_orange_fire(signal: dict[str, Any]) -> str:
    """
    Classify the quality of the orange fire signal into one of three states.

    "generative"  — healthy creative fire, constructive
    "consuming"   — fire that burns without building, destructive
    "dormant"     — fire present but not yet ignited
    """
    intensity = float(signal.get("intensity", 0.0))
    direction = signal.get("direction", "inward")
    blocked   = bool(signal.get("blocked"))

    if blocked or intensity < 0.2:
        return "dormant"
    if direction == "outward" and intensity >= 0.5:
        return "generative"
    return "consuming"


def assess_solar_integration(signal: dict[str, Any]) -> float:
    """
    Score how integrated the solar energy is, returning a float in [0.0, 1.0].

    Factors contributing to integration score (+0.25 each):
      - "grounded" key is True
      - "purposeful" key is True
      - "expressive" key is True
      - intensity in [0.4, 0.85] (healthy range — not suppressed, not inflated)
    """
    score = 0.0
    if signal.get("grounded"):
        score += 0.25
    if signal.get("purposeful"):
        score += 0.25
    if signal.get("expressive"):
        score += 0.25
    intensity = float(signal.get("intensity", 0.0))
    if 0.4 <= intensity <= 0.85:
        score += 0.25
    return round(score, 4)


def map_solar_archetype(signal: dict[str, Any]) -> str:
    """
    Map a signal to a solar archetype label.

    Uses classify_orange_fire + assess_solar_integration to select archetype:
      dormant   + low integration  → "fool"
      dormant   + any             → "adventurer" (potential)
      consuming + any             → "sovereign" (unclaimed)
      generative + high (>=0.75)  → "creator"
      generative + lower          → "adventurer"
    """
    fire_class  = classify_orange_fire(signal)
    integration = assess_solar_integration(signal)

    if fire_class == "dormant":
        return "fool" if integration < 0.25 else "adventurer"
    if fire_class == "consuming":
        return "sovereign"
    # generative
    return "creator" if integration >= 0.75 else "adventurer"
