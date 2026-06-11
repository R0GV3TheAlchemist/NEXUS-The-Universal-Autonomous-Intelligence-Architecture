"""
shadow_engine.intensity — computes shadow intensity modifiers.

Provides:
  - compute_intensity_modifier   : day-based ramp → [0.6, 1.0]
  - compute_shadow_intensity     : score × day modifier → [0.0, 1.0]
"""
from __future__ import annotations

INTENSITY_FLOOR: float = 0.6
INTENSITY_RAMP_DAYS: int = 14


def compute_intensity_modifier(days: int) -> float:
    """
    Return a multiplicative day-trust modifier in [INTENSITY_FLOOR, 1.0].

    The modifier ramps linearly from INTENSITY_FLOOR at day 0 to 1.0 at
    day INTENSITY_RAMP_DAYS, then stays at 1.0 thereafter.

    Args:
        days: Number of days the shadow pattern has been active (>= 0).

    Returns:
        A float in [0.6, 1.0].
    """
    clamped = min(days, INTENSITY_RAMP_DAYS)
    ramp = clamped / INTENSITY_RAMP_DAYS  # 0.0 → 1.0 over 14 days
    modifier = INTENSITY_FLOOR + (1.0 - INTENSITY_FLOOR) * ramp
    return round(modifier, 10)


def compute_shadow_intensity(score: float, days: int) -> float:
    """
    Compute shadow intensity from an archetype score and a day count.

    Formula: intensity = score × compute_intensity_modifier(days)

    Args:
        score: Archetype score in [0, 1].
        days:  Number of days the shadow has been active.

    Returns:
        Normalised intensity in [0.0, 1.0].
    """
    raw = max(0.0, min(1.0, score)) * compute_intensity_modifier(days)
    return max(0.0, min(1.0, raw))
