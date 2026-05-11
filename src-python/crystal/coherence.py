"""
crystal/coherence.py
Computes the composite coherence score Ψ from the four component scores.

Ψ = w_A·A + w_S·S + w_E·E + w_H·H

Weights (from spec C-CC01 §3.1):
  Affect    w_A = 0.35
  Stage     w_S = 0.30
  Shadow    w_E = 0.20
  Schumann  w_H = 0.15
"""

from __future__ import annotations

from .components import (
    derive_affect_coherence,
    derive_schumann_alignment,
    derive_shadow_integration,
    derive_stage_coherence,
)

# Weights — must sum to 1.0
W_AFFECT   = 0.35
W_STAGE    = 0.30
W_SHADOW   = 0.20
W_SCHUMANN = 0.15

assert abs(W_AFFECT + W_STAGE + W_SHADOW + W_SCHUMANN - 1.0) < 1e-9, \
    "Crystal Core weights must sum to 1.0"


def compute_coherence(
    *,
    # Affect stream
    arc_stability:        float,
    valence_trend:        float,
    volatility:           float,
    # Stage stream
    marker_scores:        dict[str, float],
    # Shadow stream
    integration_progress: float,
    shadow_intensity:     float,
    shadow_available:     bool = True,
    # Schumann stream
    schumann_alignment:   float,
    schumann_confidence:  float,
    schumann_available:   bool = True,
) -> tuple[float, float, float, float, float]:
    """
    Compute Ψ and all four component scores.

    Returns
    -------
    (psi, affect_coherence, stage_coherence, shadow_integration, schumann_alignment)
    All values in [0.0, 1.0].
    """
    A = derive_affect_coherence(
        arc_stability=arc_stability,
        valence_trend=valence_trend,
        volatility=volatility,
    )
    S = derive_stage_coherence(marker_scores)
    E = derive_shadow_integration(
        integration_progress=integration_progress,
        shadow_intensity=shadow_intensity,
        available=shadow_available,
    )
    H = derive_schumann_alignment(
        alignment_score=schumann_alignment,
        confidence=schumann_confidence,
        available=schumann_available,
    )

    psi = W_AFFECT * A + W_STAGE * S + W_SHADOW * E + W_SCHUMANN * H
    psi = max(0.0, min(1.0, psi))

    return psi, A, S, E, H
