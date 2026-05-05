"""
Affect Engine — Arc Trend Analyser  (Issue #65)

Computes higher-order signals from a rolling valence / arousal history
that Stage Engine (#63) and Shadow Engine (#67) consume.

All inputs are plain lists of floats; no SovereignMemory dependency here
— the engine fetches the history and passes it in.  This keeps the
analyser pure-Python and trivially unit-testable.

Outputs
-------
ArcTrend dataclass with:
  valence_trend    : float   — slope of 30-day valence OLS regression (-1 to 1)
  mood_momentum    : float   — 7-day vs 30-day mean delta, clamped [-1, 1]
  volatility       : float   — population std-dev of last 30 valence values
  is_volatile      : bool    — True when volatility > VOLATILITY_THRESHOLD
  dominant_emotion : str     — modal emotion label in last 30 snapshots
  low_energy_flag  : bool    — True when arousal 7d mean < LOW_AROUSAL_THRESHOLD
  arc_stability    : float   — 0–1, same formula as Stage Engine marker 6
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, asdict
from statistics import pstdev
from typing import Sequence

VOLATILITY_THRESHOLD = 0.35
LOW_AROUSAL_THRESHOLD = 0.25


@dataclass
class ArcTrend:
    valence_trend    : float   # OLS slope, clipped to [-1, 1]
    mood_momentum    : float   # 7d−30d mean delta, clipped to [-1, 1]
    volatility       : float   # pstdev of valence, [0, 1]
    is_volatile      : bool
    dominant_emotion : str
    low_energy_flag  : bool
    arc_stability    : float   # 0–1

    def to_dict(self) -> dict:
        return asdict(self)


def compute_arc_trend(
    valence_history  : Sequence[float],
    arousal_history  : Sequence[float],
    emotion_labels   : Sequence[str],
) -> ArcTrend:
    """
    Compute ArcTrend from rolling history lists.

    Args:
        valence_history:  Up to 30 daily valence readings (-1 to 1).
        arousal_history:  Up to 30 daily arousal readings (0 to 1).
        emotion_labels:   Emotion label strings for the same window.

    Returns:
        ArcTrend dataclass.
    """
    v = list(valence_history[-30:]) if valence_history else []
    a = list(arousal_history[-30:]) if arousal_history else []
    e = list(emotion_labels[-30:])  if emotion_labels   else []

    # ─ valence trend (OLS slope) ─────────────────────────────────
    valence_trend = _ols_slope(v) if len(v) >= 3 else 0.0
    valence_trend = max(-1.0, min(1.0, valence_trend))

    # ─ mood momentum ───────────────────────────────────────
    if len(v) >= 7:
        mean_7d  = sum(v[-7:]) / 7.0
        mean_30d = sum(v) / len(v)
        mood_momentum = max(-1.0, min(1.0, mean_7d - mean_30d))
    else:
        mood_momentum = 0.0

    # ─ volatility ─────────────────────────────────────────
    volatility  = pstdev(v) if len(v) >= 2 else 0.0
    is_volatile = volatility > VOLATILITY_THRESHOLD

    # ─ arc stability (shared formula with Stage Engine marker 6) ───
    if len(v) > 1:
        mu    = sum(v) / len(v)
        sigma = math.sqrt(sum((x - mu) ** 2 for x in v) / len(v))
        zero_crossings = sum(
            1 for a_, b in zip(v, v[1:])
            if (a_ < 0 <= b) or (a_ >= 0 > b)
        )
        zcr         = zero_crossings / max(1, len(v) - 1)
        arc_stability = math.exp(-2.5 * sigma) * (1.0 - 0.8 * zcr)
        arc_stability = max(0.0, min(1.0, arc_stability))
    else:
        arc_stability = 0.50

    # ─ dominant emotion ──────────────────────────────────
    if e:
        counter = Counter(e)
        dominant_emotion = counter.most_common(1)[0][0]
    else:
        dominant_emotion = "neutral"

    # ─ low energy flag ───────────────────────────────────
    if len(a) >= 7:
        arousal_7d_mean = sum(a[-7:]) / 7.0
        low_energy_flag = arousal_7d_mean < LOW_AROUSAL_THRESHOLD
    else:
        low_energy_flag = False

    return ArcTrend(
        valence_trend    = valence_trend,
        mood_momentum    = mood_momentum,
        volatility       = volatility,
        is_volatile      = is_volatile,
        dominant_emotion = dominant_emotion,
        low_energy_flag  = low_energy_flag,
        arc_stability    = arc_stability,
    )


def _ols_slope(values: list[float]) -> float:
    """
    Ordinary-least-squares slope of values over integer x indices.
    Returns the slope (rise per step).  Normalised by window length
    so units are comparable regardless of window size.
    """
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    num   = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    denom = sum((x - x_mean) ** 2 for x in xs)
    return (num / denom) if denom else 0.0
