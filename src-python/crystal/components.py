"""
crystal/components.py
Derives the four component coherence scores (A, S, E, H) from raw stream data.

All functions return float in [0.0, 1.0].
All functions are pure — no side effects, no I/O.
"""

from __future__ import annotations


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# A — Affect Coherence
# Formula: (arc_stability + clip(valence_trend × 0.5 + 0.5, 0, 1) + (1 - vol)) / 3
# ---------------------------------------------------------------------------

def derive_affect_coherence(
    arc_stability:  float,   # [0, 1]   from ArcTrend.arc_stability
    valence_trend:  float,   # [-1, 1]  from ArcTrend.valence_trend
    volatility:     float,   # [0, 1]   from ArcTrend.volatility
) -> float:
    """
    Affect coherence A.

    A = (arc_stability + clip(valence_trend × 0.5 + 0.5) + (1 − volatility)) / 3
    """
    a_stab  = _clamp(arc_stability)
    v_norm  = _clamp(valence_trend * 0.5 + 0.5)
    inv_vol = _clamp(1.0 - volatility)
    return _clamp((a_stab + v_norm + inv_vol) / 3.0)


# ---------------------------------------------------------------------------
# S — Stage Coherence
# Formula: mean of six marker scores, each normalised from [0, 100] → [0, 1]
# ---------------------------------------------------------------------------

_STAGE_MARKER_KEYS = (
    "decision_entropy",
    "hrv_coherence",
    "journaling_depth",
    "focus_session_length",
    "goal_completion_rate",
    "emotional_arc_stability",
)


def derive_stage_coherence(marker_scores: dict[str, float]) -> float:
    """
    Stage coherence S.

    S = mean(m_i / 100) for each of the six stage marker scores.
    Missing keys default to 50 (neutral).
    """
    values = [
        _clamp(marker_scores.get(key, 50.0) / 100.0)
        for key in _STAGE_MARKER_KEYS
    ]
    return _clamp(sum(values) / len(values))


# ---------------------------------------------------------------------------
# E — Shadow Integration
# Formula: integration_progress × (1 − 0.4 × shadow_intensity)
# Defaults to 0.5 when Shadow Engine unavailable.
# ---------------------------------------------------------------------------

def derive_shadow_integration(
    integration_progress: float,   # [0, 1]
    shadow_intensity:     float,   # [0, 1]
    available:            bool = True,
) -> float:
    """
    Shadow integration E.

    E = integration_progress × (1 − 0.4 × shadow_intensity)

    When Shadow Engine is unavailable, returns the neutral default 0.5.
    """
    if not available:
        return 0.5
    ip  = _clamp(integration_progress)
    si  = _clamp(shadow_intensity)
    return _clamp(ip * (1.0 - 0.4 * si))


# ---------------------------------------------------------------------------
# H — Schumann Alignment
# Formula: alignment_score if confidence >= 0.4 else 0.5 (neutral fallback)
# ---------------------------------------------------------------------------

SCHUMANN_CONFIDENCE_THRESHOLD = 0.4


def derive_schumann_alignment(
    alignment_score: float,   # [0, 1]
    confidence:      float,   # [0, 1]
    available:       bool = True,
) -> float:
    """
    Schumann alignment H.

    H = alignment_score  if confidence >= 0.4
      = 0.5              otherwise (low-confidence or unavailable → neutral)
    """
    if not available or confidence < SCHUMANN_CONFIDENCE_THRESHOLD:
        return 0.5
    return _clamp(alignment_score)
