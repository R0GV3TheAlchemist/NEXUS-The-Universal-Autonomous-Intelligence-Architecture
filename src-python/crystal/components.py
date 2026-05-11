"""
crystal/components.py
Derives the four component coherence scores from raw stream payloads.

Each public function accepts a dict (or None when the stream is offline)
and returns a float in [0.0, 1.0].

Public API
----------
derive_affect_coherence(payload)   -> float   A
derive_stage_coherence(payload)    -> float   S
derive_shadow_integration(payload) -> float   E
derive_schumann_alignment(payload) -> float   H

Payload shapes
--------------
affect:   {arc_stability: float, valence_trend: float, volatility: float}
stage:    {marker_scores: list[float]}   # six values, each [0, 100]
shadow:   {integration_progress: float, shadow_intensity: float}  | None
schumann: {alignment_score: float, confidence: float}             | None
"""

from __future__ import annotations

from typing import Optional


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# A — Affect Coherence
# ---------------------------------------------------------------------------

def derive_affect_coherence(payload: dict) -> float:
    """
    A = mean(arc_stability, (valence_trend+1)/2, 1-volatility)

    arc_stability  [0, 1]
    valence_trend  [-1, 1]  shifted to [0, 1]
    volatility     [0, 1]   inverted so high volatility lowers A
    """
    arc_stability = float(payload.get("arc_stability", 0.5))
    valence_trend = float(payload.get("valence_trend", 0.0))
    volatility    = float(payload.get("volatility",    0.0))

    trend_norm = (valence_trend + 1.0) / 2.0   # [-1,1] -> [0,1]
    raw = (arc_stability + trend_norm + (1.0 - volatility)) / 3.0
    return _clamp(raw)


# ---------------------------------------------------------------------------
# S — Stage Coherence
# ---------------------------------------------------------------------------

def derive_stage_coherence(payload: dict) -> float:
    """
    S = mean of marker_scores normalised from [0, 100] to [0, 1].

    marker_scores is a list of up to six floats.  Missing or empty list
    defaults to 0.5 (neutral).
    """
    scores: list = payload.get("marker_scores") or []
    if not scores:
        return 0.5
    normalised = [_clamp(float(v) / 100.0) for v in scores]
    return _clamp(sum(normalised) / len(normalised))


# ---------------------------------------------------------------------------
# E — Shadow Integration
# ---------------------------------------------------------------------------

def derive_shadow_integration(payload: Optional[dict]) -> float:
    """
    E = integration_progress * (1 - 0.5 * shadow_intensity)

    None payload (Shadow Engine offline) -> neutral 0.5.
    """
    if payload is None:
        return 0.5
    progress  = float(payload.get("integration_progress", 0.5))
    intensity = float(payload.get("shadow_intensity",      0.0))
    raw = progress * (1.0 - 0.5 * intensity)
    return _clamp(raw)


# ---------------------------------------------------------------------------
# H — Schumann Alignment
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD = 0.4   # spec C-CC01 §3.1


def derive_schumann_alignment(payload: Optional[dict]) -> float:
    """
    H = alignment_score when confidence >= 0.4, else 0.5 (neutral).

    None payload (Schumann stream offline) -> neutral 0.5.
    """
    if payload is None:
        return 0.5
    confidence      = float(payload.get("confidence",      0.0))
    alignment_score = float(payload.get("alignment_score", 0.5))
    if confidence < CONFIDENCE_THRESHOLD:
        return 0.5
    return _clamp(alignment_score)
