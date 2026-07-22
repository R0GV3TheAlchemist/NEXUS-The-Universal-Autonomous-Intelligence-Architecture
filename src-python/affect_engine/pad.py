# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Affect Engine — PAD Model Core
# Phase E: Pleasure-Arousal-Dominance state vector — live outputs.
# Architecture: NEXUS_UNIVERSAL_OS.md Domain 2.2
# GAIAN Law V: Emotional Sovereignty

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# PAD space constants
# ---------------------------------------------------------------------------

PLEASURE_MIN, PLEASURE_MAX     = -1.0,  1.0
AROUSAL_MIN,  AROUSAL_MAX      =  0.0,  1.0
DOMINANCE_MIN, DOMINANCE_MAX   =  0.0,  1.0

# Exponential moving-average smoothing factor (0 = ignore new, 1 = replace)
_EMA_ALPHA = 0.35


# ---------------------------------------------------------------------------
# PAD label classifier
# Regions from Russell & Mehrabian (1977) mapped to a 3x3x3 label grid.
# ---------------------------------------------------------------------------

_PAD_LABELS: list[tuple[str, tuple[float, float], tuple[float, float], tuple[float, float]]] = [
    # (label,    P range,        A range,        D range)
    ("elated",   ( 0.5,  1.0),  (0.6,  1.0),   (0.5, 1.0)),
    ("excited",  ( 0.3,  1.0),  (0.7,  1.0),   (0.4, 1.0)),
    ("happy",    ( 0.4,  1.0),  (0.3,  0.7),   (0.4, 1.0)),
    ("calm",     ( 0.2,  1.0),  (0.0,  0.35),  (0.4, 1.0)),
    ("serene",   ( 0.3,  1.0),  (0.0,  0.3),   (0.5, 1.0)),
    ("focused",  ( 0.0,  0.6),  (0.4,  0.75),  (0.5, 1.0)),
    ("neutral",  (-0.2,  0.2),  (0.3,  0.6),   (0.3, 0.7)),
    ("bored",    (-0.5,  0.1),  (0.0,  0.35),  (0.2, 0.6)),
    ("sad",      (-1.0, -0.2),  (0.0,  0.4),   (0.0, 0.4)),
    ("anxious",  (-0.5,  0.1),  (0.55, 1.0),   (0.0, 0.45)),
    ("angry",    (-1.0, -0.1),  (0.6,  1.0),   (0.5, 1.0)),
    ("distressed",(-1.0, -0.3), (0.5,  1.0),   (0.0, 0.5)),
    ("tense",    (-0.4,  0.1),  (0.6,  1.0),   (0.0, 0.5)),
    ("relaxed",  ( 0.2,  1.0),  (0.0,  0.4),   (0.3, 0.8)),
]


def classify_pad(pleasure: float, arousal: float, dominance: float) -> str:
    """
    Return the closest PAD label for the given P, A, D values.
    Matches the first region whose bounds contain all three dimensions;
    falls back to Euclidean nearest-centroid if no exact match.
    """
    # Try exact region match first
    for label, (p0, p1), (a0, a1), (d0, d1) in _PAD_LABELS:
        if p0 <= pleasure <= p1 and a0 <= arousal <= a1 and d0 <= dominance <= d1:
            return label

    # Euclidean nearest centroid fallback
    best_label, best_dist = "neutral", float("inf")
    for label, (p0, p1), (a0, a1), (d0, d1) in _PAD_LABELS:
        cp = (p0 + p1) / 2
        ca = (a0 + a1) / 2
        cd = (d0 + d1) / 2
        dist = math.sqrt((pleasure - cp) ** 2 + (arousal - ca) ** 2 + (dominance - cd) ** 2)
        if dist < best_dist:
            best_dist = dist
            best_label = label
    return best_label


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# AffectState — the live PAD output
# ---------------------------------------------------------------------------

@dataclass
class AffectState:
    """Live PAD affective state vector."""
    pleasure:   float = 0.0
    arousal:    float = 0.5
    dominance:  float = 0.5
    label:      str   = "neutral"
    timestamp:  str   = ""
    confidence: float = 1.0          # 0–1: how certain the classifier is
    sources:    list[str] = field(default_factory=list)  # which signals contributed

    def __post_init__(self) -> None:
        self.pleasure  = clamp(self.pleasure,  PLEASURE_MIN,  PLEASURE_MAX)
        self.arousal   = clamp(self.arousal,   AROUSAL_MIN,   AROUSAL_MAX)
        self.dominance = clamp(self.dominance, DOMINANCE_MIN, DOMINANCE_MAX)
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.label == "neutral" and (self.pleasure != 0.0 or self.arousal != 0.5):
            self.label = classify_pad(self.pleasure, self.arousal, self.dominance)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pleasure":   self.pleasure,
            "arousal":    self.arousal,
            "dominance":  self.dominance,
            "label":      self.label,
            "timestamp":  self.timestamp,
            "confidence": self.confidence,
            "sources":    self.sources,
        }

    def blend(self, other: "AffectState", alpha: float = _EMA_ALPHA) -> "AffectState":
        """EMA blend: return a new AffectState smoothed toward `other`."""
        p = self.pleasure  + alpha * (other.pleasure  - self.pleasure)
        a = self.arousal   + alpha * (other.arousal   - self.arousal)
        d = self.dominance + alpha * (other.dominance - self.dominance)
        conf = 0.5 * (self.confidence + other.confidence)
        sources = list(set(self.sources) | set(other.sources))
        label = classify_pad(p, a, d)
        return AffectState(
            pleasure=round(p, 4),
            arousal=round(a, 4),
            dominance=round(d, 4),
            label=label,
            confidence=round(conf, 4),
            sources=sources,
        )
