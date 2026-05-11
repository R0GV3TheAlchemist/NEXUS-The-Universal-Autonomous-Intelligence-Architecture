"""
crystal/coherence.py
Computes the composite coherence score Ψ from the four component scores.

Ψ = w_A·A + w_S·S + w_E·E + w_H·H

Weights (spec C-CC01 §3.1):
  Affect    w_A = 0.35
  Stage     w_S = 0.30
  Shadow    w_E = 0.20
  Schumann  w_H = 0.15

Public API (primary — used by tests and CrystalState builder)
--------------------------------------------------------------
compute_coherence(
    affect_coherence,    # float [0,1]  – from components.derive_affect_coherence
    stage_coherence,     # float [0,1]  – from components.derive_stage_coherence
    shadow_integration,  # float [0,1]  – from components.derive_shadow_integration
    schumann_alignment,  # float [0,1]  – from components.derive_schumann_alignment
) -> float   # Ψ in [0.0, 1.0]

Legacy raw-streams entry-point (used by engine.py)
---------------------------------------------------
compute_coherence_from_streams(**kwargs) -> tuple[float, float, float, float, float]
   (psi, A, S, E, H)
"""

from __future__ import annotations

from typing import Optional

from .components import (
    derive_affect_coherence,
    derive_stage_coherence,
    derive_shadow_integration,
    derive_schumann_alignment,
)

# Weights — must sum to 1.0
W_AFFECT   = 0.35
W_STAGE    = 0.30
W_SHADOW   = 0.20
W_SCHUMANN = 0.15

assert abs(W_AFFECT + W_STAGE + W_SHADOW + W_SCHUMANN - 1.0) < 1e-9, \
    "Crystal Core weights must sum to 1.0"


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Primary API — accepts pre-derived component scores
# ---------------------------------------------------------------------------

def compute_coherence(
    affect_coherence:   float = 0.5,
    stage_coherence:    float = 0.5,
    shadow_integration: float = 0.5,
    schumann_alignment: float = 0.5,
) -> float:
    """
    Compute Ψ from the four pre-derived component scores.

    Parameters
    ----------
    affect_coherence   : A  [0, 1]
    stage_coherence    : S  [0, 1]
    shadow_integration : E  [0, 1]
    schumann_alignment : H  [0, 1]

    Returns
    -------
    float — Ψ in [0.0, 1.0]
    """
    psi = (
        W_AFFECT   * affect_coherence
        + W_STAGE    * stage_coherence
        + W_SHADOW   * shadow_integration
        + W_SCHUMANN * schumann_alignment
    )
    return _clamp(psi)


# ---------------------------------------------------------------------------
# Legacy entry-point — accepts raw stream fields, used by engine.py
# ---------------------------------------------------------------------------

def compute_coherence_from_streams(
    *,
    arc_stability:        float = 0.5,
    valence_trend:        float = 0.0,
    volatility:           float = 0.0,
    marker_scores:        Optional[list] = None,
    integration_progress: float = 0.5,
    shadow_intensity:     float = 0.0,
    shadow_available:     bool  = True,
    schumann_alignment:   float = 0.5,
    schumann_confidence:  float = 0.0,
    schumann_available:   bool  = True,
) -> tuple[float, float, float, float, float]:
    """
    Derive all four components from raw stream fields, then compute Ψ.

    Returns
    -------
    (psi, A, S, E, H) — all floats in [0.0, 1.0]
    """
    A = derive_affect_coherence({
        "arc_stability": arc_stability,
        "valence_trend": valence_trend,
        "volatility":    volatility,
    })
    S = derive_stage_coherence({
        "marker_scores": marker_scores or [],
    })
    E = derive_shadow_integration(
        None if not shadow_available else {
            "integration_progress": integration_progress,
            "shadow_intensity":      shadow_intensity,
        }
    )
    H = derive_schumann_alignment(
        None if not schumann_available else {
            "alignment_score": schumann_alignment,
            "confidence":      schumann_confidence,
        }
    )

    psi = compute_coherence(A, S, E, H)
    return psi, A, S, E, H
