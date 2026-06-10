"""
shadow_engine.intensity — computes shadow intensity modifiers.

Provides:
  - compute_shadow_intensity    : computes raw intensity from signals
  - compute_intensity_modifier  : returns a [0, 2] modifier based on intensity
"""
from __future__ import annotations

import math
from typing import List, Optional


def compute_shadow_intensity(
    base_intensity: float,
    signals: Optional[List[float]] = None,
    context_weight: float = 1.0,
) -> float:
    """
    Compute shadow intensity from a base value and optional signal list.

    Args:
        base_intensity: Raw intensity in [0, 1].
        signals:        Additional intensity signals (each in [0, 1]).
        context_weight: Scaling factor for the context contribution.

    Returns:
        Normalised intensity in [0, 1].
    """
    if not signals:
        return max(0.0, min(1.0, base_intensity))

    signal_mean = sum(signals) / len(signals)
    combined = base_intensity * 0.6 + signal_mean * 0.4 * context_weight
    return max(0.0, min(1.0, combined))


def compute_intensity_modifier(
    intensity: float,
    amplification: float = 1.0,
) -> float:
    """
    Convert a [0, 1] intensity value into a multiplicative modifier.

    A modifier of 1.0 means neutral; >1.0 amplifies; <1.0 dampens.

    Formula: modifier = 1 + sin(intensity * π/2) * amplification

    Returns a value in [1.0, 1.0 + amplification].
    """
    modifier = 1.0 + math.sin(intensity * math.pi / 2) * amplification
    return max(0.0, modifier)
