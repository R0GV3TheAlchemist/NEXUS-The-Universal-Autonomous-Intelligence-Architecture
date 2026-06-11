"""
shadow_engine.archetypes — 7-archetype scoring matrix for the shadow engine.

Provides:
  - ShadowInputs      : dict-like dataclass of 16 biometric/emotional signals
  - ArchetypeDetector : score_all() + per-archetype scoring methods
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterator, Optional, Tuple

log = logging.getLogger(__name__)

# Archetype names (canonical strings)
ORPHAN    = "Orphan"
WARRIOR   = "Warrior"
WANDERER  = "Wanderer"
CAREGIVER = "Caregiver"
SEEKER    = "Seeker"
DESTROYER = "Destroyer"
CREATOR   = "Creator"

ALL_ARCHETYPES = [ORPHAN, WARRIOR, WANDERER, CAREGIVER, SEEKER, DESTROYER, CREATOR]


@dataclass
class ShadowInputs:
    """16-field input dataclass; supports dict-style item access for test ergonomics."""

    dominant_emotion:      str   = "neutral"
    valence_trend:         float = 0.0
    mood_momentum:         float = 0.0
    volatility:            float = 0.0
    is_volatile:           bool  = False
    arc_stability:         float = 0.5
    low_energy_flag:       bool  = False
    arousal:               float = 0.5
    decision_entropy:      float = 50.0
    hrv_coherence:         float = 50.0
    journaling_depth:      float = 50.0
    focus_session_length:  float = 50.0
    goal_completion_rate:  float = 50.0
    emotional_arc_stability: float = 50.0
    days_in_stage:         int   = 0
    regression_active:     bool  = False

    # ── dict-style access so tests can do inp["field"] = value ──
    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value) -> None:
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def to_dict(self) -> dict:
        return {
            "dominant_emotion":      self.dominant_emotion,
            "valence_trend":         self.valence_trend,
            "mood_momentum":         self.mood_momentum,
            "volatility":            self.volatility,
            "is_volatile":           self.is_volatile,
            "arc_stability":         self.arc_stability,
            "low_energy_flag":       self.low_energy_flag,
            "arousal":               self.arousal,
            "decision_entropy":      self.decision_entropy,
            "hrv_coherence":         self.hrv_coherence,
            "journaling_depth":      self.journaling_depth,
            "focus_session_length":  self.focus_session_length,
            "goal_completion_rate":  self.goal_completion_rate,
            "emotional_arc_stability": self.emotional_arc_stability,
            "days_in_stage":         self.days_in_stage,
            "regression_active":     self.regression_active,
        }


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _norm100(v: float) -> float:
    """Normalise a 0-100 signal to [0, 1]."""
    return _clamp(v / 100.0)


class ArchetypeDetector:
    """Scores all 7 shadow archetypes from ShadowInputs."""

    def __init__(self) -> None:
        log.info("ArchetypeDetector initialised")

    # ─────────────────────── per-archetype scorers ──────────────────────────

    def score_orphan(self, inp: ShadowInputs) -> float:
        """High on sadness, low energy, low goal completion, negative valence."""
        emotion_hit = 0.4 if inp.dominant_emotion in ("sadness", "grief") else 0.0
        energy_hit  = 0.2 if inp.low_energy_flag else 0.0
        valence     = _clamp(-inp.valence_trend) * 0.2   # negative trend → higher
        completion  = _clamp(1.0 - _norm100(inp.goal_completion_rate)) * 0.2
        return _clamp(emotion_hit + energy_hit + valence + completion)

    def score_warrior(self, inp: ShadowInputs) -> float:
        """High on anger, high volatility, high arousal."""
        emotion_hit = 0.35 if inp.dominant_emotion in ("anger", "rage") else 0.0
        vol         = _clamp(inp.volatility) * 0.35
        arousal     = _clamp(inp.arousal) * 0.30
        return _clamp(emotion_hit + vol + arousal)

    def score_wanderer(self, inp: ShadowInputs) -> float:
        """Low decision entropy (inverted), low arc stability, long stagnation."""
        entropy_inv = _clamp(1.0 - _norm100(inp.decision_entropy)) * 0.3
        stability   = _clamp(1.0 - _norm100(inp.emotional_arc_stability)) * 0.3
        stagnation  = _clamp(inp.days_in_stage / 180.0) * 0.4
        return _clamp(entropy_inv + stability + stagnation)

    def score_caregiver(self, inp: ShadowInputs) -> float:
        """Low HRV, low journal depth (= high self-ref proxy), sadness, low energy."""
        hrv_hit     = _clamp(1.0 - _norm100(inp.hrv_coherence)) * 0.3
        journal_hit = _clamp(1.0 - _norm100(inp.journaling_depth)) * 0.25
        emotion_hit = 0.25 if inp.dominant_emotion in ("sadness", "grief") else 0.0
        energy_hit  = 0.2 if inp.low_energy_flag else 0.0
        return _clamp(hrv_hit + journal_hit + emotion_hit + energy_hit)

    def score_seeker(self, inp: ShadowInputs) -> float:
        """Surprise, high volatility, short focus sessions, long time in stage."""
        emotion_hit = 0.25 if inp.dominant_emotion in ("surprise", "curiosity") else 0.0
        vol         = _clamp(inp.volatility) * 0.25
        focus_inv   = _clamp(1.0 - _norm100(inp.focus_session_length)) * 0.25
        stagnation  = _clamp(inp.days_in_stage / 180.0) * 0.25
        return _clamp(emotion_hit + vol + focus_inv + stagnation)

    def score_destroyer(self, inp: ShadowInputs) -> float:
        """Fear, strong negative valence, volatile, regression active."""
        emotion_hit  = 0.3 if inp.dominant_emotion in ("fear", "dread") else 0.0
        valence      = _clamp(-inp.valence_trend) * 0.3
        volatile_hit = 0.2 if inp.is_volatile else 0.0
        regress_hit  = 0.2 if inp.regression_active else 0.0
        return _clamp(emotion_hit + valence + volatile_hit + regress_hit)

    def score_creator(self, inp: ShadowInputs) -> float:
        """Deep journaling, long focus sessions, but low goal completion."""
        journal      = _norm100(inp.journaling_depth) * 0.4
        focus        = _norm100(inp.focus_session_length) * 0.3
        completion_i = _clamp(1.0 - _norm100(inp.goal_completion_rate)) * 0.3
        return _clamp(journal + focus + completion_i)

    # ─────────────────────── aggregate ──────────────────────────────────────

    def score_all(self, inp: ShadowInputs) -> Dict[str, float]:
        """Return {archetype_name: score} for all 7 archetypes."""
        return {
            ORPHAN:    self.score_orphan(inp),
            WARRIOR:   self.score_warrior(inp),
            WANDERER:  self.score_wanderer(inp),
            CAREGIVER: self.score_caregiver(inp),
            SEEKER:    self.score_seeker(inp),
            DESTROYER: self.score_destroyer(inp),
            CREATOR:   self.score_creator(inp),
        }
