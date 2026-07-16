# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
"""
core/spectral/green/clarity.py — Depth-readable signals, VIRIDITAS layer.
"""
from __future__ import annotations
from typing import Any

_EARTH_ARCHETYPES = {
    "gardener":   "The Gardener — tending, nurturing, patient growth",
    "healer":     "The Healer — restoring balance, mending wounds",
    "wildling":   "The Wildling — uncontained growth, boundary-less",
    "dormant":    "The Dormant Seed — potential held in stillness",
}


def distinguish_growth_healing(signal: dict[str, Any]) -> str:
    has_growth  = bool(signal.get("expansion") or signal.get("building"))
    has_healing = bool(signal.get("restoration") or signal.get("mending"))
    if has_growth and has_healing:
        return "integrated"
    if has_growth:
        return "growth"
    if has_healing:
        return "healing"
    return "undifferentiated"


def detect_earth_wound(signal: dict[str, Any]) -> dict[str, Any]:
    patterns: list[tuple[bool, str, str]] = [
        (bool(signal.get("over_giving")),  "depletion wound — self-sacrificial giving", "severe"),
        (bool(signal.get("hoarding")),      "contraction wound — resource hoarding",    "moderate"),
        (bool(signal.get("stagnation")),    "stagnation — growth blocked inward",       "moderate"),
        (bool(signal.get("rootlessness")), "rootless — no ground to grow from",        "mild"),
    ]
    for detected, pattern, severity in patterns:
        if detected:
            return {"wound_detected": True, "pattern": pattern, "severity": severity}
    return {"wound_detected": False, "pattern": "", "severity": "none"}


def classify_green_vitality(signal: dict[str, Any]) -> str:
    intensity = float(signal.get("intensity", 0.0))
    rooted    = bool(signal.get("rooted"))
    blocked   = bool(signal.get("blocked"))
    if blocked or intensity < 0.2:
        return "dormant"
    if rooted and intensity >= 0.5:
        return "flourishing"
    return "overgrown"


def assess_earth_integration(signal: dict[str, Any]) -> float:
    score = 0.0
    if signal.get("rooted"):
        score += 0.25
    if signal.get("reciprocal"):
        score += 0.25
    if signal.get("patient"):
        score += 0.25
    intensity = float(signal.get("intensity", 0.0))
    if 0.4 <= intensity <= 0.85:
        score += 0.25
    return round(score, 4)


def map_earth_archetype(signal: dict[str, Any]) -> str:
    vitality    = classify_green_vitality(signal)
    integration = assess_earth_integration(signal)
    if vitality == "dormant":
        return "dormant" if integration < 0.25 else "gardener"
    if vitality == "overgrown":
        return "wildling"
    return "healer" if integration >= 0.75 else "gardener"
