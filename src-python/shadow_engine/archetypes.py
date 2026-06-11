"""
shadow_engine/archetypes.py
7-archetype scoring matrix.

All scoring methods receive a ShadowInputs dataclass so they stay
pure functions — easy to unit-test without any I/O.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing      import Optional


@dataclass
class ShadowInputs:
    """Inputs assembled by ShadowEngine from Affect + Stage streams."""
    # --- Affect stream ---
    dominant_emotion:  str   = "neutral"  # joy | sadness | anger | fear | disgust | surprise | neutral
    valence_trend:     float = 0.0        # -1.0 – 1.0
    mood_momentum:     float = 0.0        # -1.0 – 1.0
    volatility:        float = 0.0        # 0.0 – 1.0  (pstdev, clamped)
    is_volatile:       bool  = False
    arc_stability:     float = 0.5        # 0.0 – 1.0
    low_energy_flag:   bool  = False
    arousal:           float = 0.5        # 0.0 – 1.0  (mean arousal from PAD)

    # --- Stage stream ---
    decision_entropy:        float = 50.0   # 0 – 100
    hrv_coherence:           float = 50.0   # 0 – 100
    journaling_depth:        float = 50.0   # 0 – 100
    focus_session_length:    float = 50.0   # 0 – 100
    goal_completion_rate:    float = 50.0   # 0 – 100
    emotional_arc_stability: float = 50.0   # 0 – 100
    days_in_stage:           int   = 0
    regression_active:       bool  = False

    def get(self, key: str, default=None):
        """Dict-style .get() for backward compat with any code using ShadowInputs as a dict."""
        return getattr(self, key, default)


ARCHETYPE_NAMES: list[str] = [
    "Orphan",
    "Wanderer",
    "Warrior",
    "Caregiver",
    "Seeker",
    "Destroyer",
    "Creator",
]

ARCHETYPE_METADATA: dict[str, dict] = {
    "Orphan":    {"core_wound": "Abandonment",           "keywords": ["alone", "abandoned", "helpless", "nobody", "lost"]},
    "Wanderer":  {"core_wound": "Alienation",            "keywords": ["directionless", "searching", "drifting", "uncertain", "identity"]},
    "Warrior":   {"core_wound": "Aggression",            "keywords": ["fight", "battle", "angry", "control", "force"]},
    "Caregiver": {"core_wound": "Martyrdom",             "keywords": ["sacrifice", "others", "giving", "tired", "needed"]},
    "Seeker":    {"core_wound": "Restlessness",          "keywords": ["curious", "explore", "next", "bored", "restless"]},
    "Destroyer": {"core_wound": "Compulsive disruption", "keywords": ["destroy", "burn", "chaos", "collapse", "fear"]},
    "Creator":   {"core_wound": "Perfectionism",         "keywords": ["perfect", "create", "unfinished", "paralysed", "idea"]},
}


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _bool(v: bool | int | float | None) -> float:
    if v is None:
        return 0.0
    return 1.0 if v else 0.0


def _emotion_in(inp: ShadowInputs, *emotions: str) -> float:
    return 1.0 if inp.get("dominant_emotion", "neutral") in emotions else 0.0


class ArchetypeDetector:
    """Pure scoring — no I/O."""

    @staticmethod
    def score_orphan(inp: ShadowInputs) -> float:
        return _clamp(
            0.40 * _emotion_in(inp, "sadness")
            + 0.25 * (1.0 - inp.get("goal_completion_rate", 50.0) / 100.0)
            + 0.20 * _bool(inp.get("low_energy_flag", False))
            + 0.15 * max(0.0, -inp.get("valence_trend", 0.0))
        )

    @staticmethod
    def score_wanderer(inp: ShadowInputs) -> float:
        stage_coherence = inp.get("emotional_arc_stability", 50.0) / 100.0
        days = inp.get("days_in_stage", 0)
        return _clamp(
            0.35 * (1.0 - inp.get("decision_entropy", 50.0) / 100.0)
            + 0.30 * (1.0 - stage_coherence)
            + 0.20 * _emotion_in(inp, "neutral")
            + 0.15 * min(days / 90.0, 1.0)
        )

    @staticmethod
    def score_warrior(inp: ShadowInputs) -> float:
        arousal = inp.get("arousal", 0.5)
        excess = max(0.0, arousal - 0.70) / 0.30 if arousal > 0.70 else 0.0
        return _clamp(
            0.40 * _emotion_in(inp, "anger")
            + 0.30 * inp.get("volatility", 0.0)
            + 0.20 * excess
            + 0.10 * max(0.0, -inp.get("mood_momentum", 0.0))
        )

    @staticmethod
    def score_caregiver(inp: ShadowInputs) -> float:
        journal = inp.get("journaling_depth", 50.0) / 100.0
        self_ref_proxy = 1.0 - journal * 0.4
        return _clamp(
            0.40 * self_ref_proxy
            + 0.30 * (1.0 - inp.get("hrv_coherence", 50.0) / 100.0)
            + 0.20 * _emotion_in(inp, "sadness", "neutral")
            + 0.10 * _bool(inp.get("low_energy_flag", False))
        )

    @staticmethod
    def score_seeker(inp: ShadowInputs) -> float:
        days = inp.get("days_in_stage", 0)
        stagnation = 0.5 if days > 60 else 0.0
        return _clamp(
            0.35 * _emotion_in(inp, "surprise", "neutral")
            + 0.30 * inp.get("volatility", 0.0)
            + 0.25 * (1.0 - inp.get("focus_session_length", 50.0) / 100.0)
            + 0.10 * stagnation
        )

    @staticmethod
    def score_destroyer(inp: ShadowInputs) -> float:
        return _clamp(
            0.35 * _emotion_in(inp, "fear", "anger")
            + 0.30 * max(0.0, -inp.get("valence_trend", 0.0))
            + 0.25 * _bool(inp.get("is_volatile", False))
            + 0.10 * _bool(inp.get("regression_active", False))
        )

    @staticmethod
    def score_creator(inp: ShadowInputs) -> float:
        return _clamp(
            0.40 * (inp.get("journaling_depth", 50.0) / 100.0)
            + 0.30 * (1.0 - inp.get("goal_completion_rate", 50.0) / 100.0)
            + 0.20 * (inp.get("focus_session_length", 50.0) / 100.0)
            + 0.10 * _emotion_in(inp, "neutral", "joy")
        )

    def score_all(self, inp: ShadowInputs) -> dict[str, float]:
        """Return a score for every archetype."""
        return {
            "Orphan":    self.score_orphan(inp),
            "Wanderer":  self.score_wanderer(inp),
            "Warrior":   self.score_warrior(inp),
            "Caregiver": self.score_caregiver(inp),
            "Seeker":    self.score_seeker(inp),
            "Destroyer": self.score_destroyer(inp),
            "Creator":   self.score_creator(inp),
        }
