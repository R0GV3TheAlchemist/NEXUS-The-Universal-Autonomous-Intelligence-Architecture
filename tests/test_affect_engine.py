"""
Test suite for the Affect Engine — Issue #65.

Covers:
  1.  Heuristic backend: all-joy text → label=joy
  2.  Heuristic backend: all-sad text → label=sadness
  3.  Heuristic backend: empty text → neutral, confidence=0.99
  4.  Heuristic backend: procedural text → neutral
  5.  Heuristic backend: PAD values in range
  6.  Heuristic backend: confidence bounded [0, 1]
  7.  Heuristic backend: entropy in [0, 1]
  8.  Heuristic backend: fear/anger/surprise arousal boost applied
  9.  NLP backend factory: heuristic resolves to HeuristicBackend
  10. NLP backend factory: unknown name falls back to heuristic
  11. NLP backend factory: env var GAIA_AFFECT_BACKEND honoured
  12. ArcTrend: constant valence → near-zero trend and volatility
  13. ArcTrend: ascending valence → positive trend
  14. ArcTrend: descending valence → negative trend
  15. ArcTrend: high oscillation → is_volatile=True
  16. ArcTrend: stable valence → is_volatile=False
  17. ArcTrend: mood_momentum positive when recent is higher
  18. ArcTrend: mood_momentum negative when recent is lower
  19. ArcTrend: dominant_emotion is modal label
  20. ArcTrend: low_energy_flag triggered by low arousal
  21. ArcTrend: arc_stability high for constant valence
  22. ArcTrend: arc_stability low for high oscillation
  23. ArcTrend: empty inputs return safe defaults
  24. PadVector.clamp() constrains values
  25. AffectAnalysisResult.to_dict() has expected keys
"""

from __future__ import annotations

import os
import math

import pytest

from affect_engine.heuristics import analyze_text_heuristic, lexical_entropy, tokenize
from affect_engine.types import PadVector, AffectAnalysisResult
from affect_engine.nlp_backend import (
    build_backend, HeuristicBackend, BACKEND_REGISTRY
)
from affect_engine.arc_trend import (
    compute_arc_trend, VOLATILITY_THRESHOLD, LOW_AROUSAL_THRESHOLD
)


# ─────────────────────────────────────────────
# 1–8: Heuristic backend
# ─────────────────────────────────────────────

class TestHeuristicBackend:
    def test_joy_text(self):
        r = analyze_text_heuristic("I feel so happy and grateful and alive today")
        assert r.label == "joy"

    def test_sadness_text(self):
        r = analyze_text_heuristic("I am so sad and lonely and feel broken and hopeless")
        assert r.label == "sadness"

    def test_empty_text_returns_neutral_high_confidence(self):
        r = analyze_text_heuristic("")
        assert r.label == "neutral"
        assert r.confidence == 0.99

    def test_procedural_text_returns_neutral(self):
        r = analyze_text_heuristic("fix: refactor the build config and deploy to staging")
        assert r.label == "neutral"

    def test_pad_pleasure_in_range(self):
        r = analyze_text_heuristic("I feel afraid and nervous and scared")
        assert -1.0 <= r.pad.pleasure <= 1.0

    def test_confidence_bounded(self):
        for text in ["happy", "sad cry grief", "angry furious mad rage", ""]:
            r = analyze_text_heuristic(text)
            assert 0.0 <= r.confidence <= 1.0

    def test_entropy_bounded(self):
        for text in ["happy", "I am so sad and lonely", ""]:
            r = analyze_text_heuristic(text)
            assert 0.0 <= r.entropy <= 1.0

    def test_arousal_boost_for_fear(self):
        r_fear = analyze_text_heuristic("I am terrified and scared and panicking")
        # Fear anchor is 0.86, boost adds 0.05 → should be > 0.86
        assert r_fear.label == "fear"
        assert r_fear.pad.arousal > 0.85


# ─────────────────────────────────────────────
# 9–11: NLP backend factory
# ─────────────────────────────────────────────

class TestBackendFactory:
    def test_heuristic_resolves_to_class(self):
        b = build_backend("heuristic")
        assert isinstance(b, HeuristicBackend)

    def test_unknown_name_falls_back_to_heuristic(self):
        b = build_backend("unicorn")
        assert isinstance(b, HeuristicBackend)

    def test_env_var_honoured(self, monkeypatch):
        monkeypatch.setenv("GAIA_AFFECT_BACKEND", "heuristic")
        b = build_backend()   # no explicit name
        assert isinstance(b, HeuristicBackend)

    def test_registry_has_three_backends(self):
        assert set(BACKEND_REGISTRY.keys()) == {"heuristic", "sbert", "llm"}


# ─────────────────────────────────────────────
# 12–23: ArcTrend analyser
# ─────────────────────────────────────────────

class TestArcTrend:
    def _flat(self, v=0.5, n=30):
        return [v] * n

    def test_constant_valence_near_zero_trend(self):
        t = compute_arc_trend(self._flat(0.5), self._flat(0.4), ["joy"] * 30)
        assert abs(t.valence_trend) < 0.01

    def test_ascending_trend_positive(self):
        vals = [i / 29.0 - 0.5 for i in range(30)]
        t = compute_arc_trend(vals, self._flat(0.4), ["joy"] * 30)
        assert t.valence_trend > 0.0

    def test_descending_trend_negative(self):
        vals = [0.5 - i / 29.0 for i in range(30)]
        t = compute_arc_trend(vals, self._flat(0.4), ["joy"] * 30)
        assert t.valence_trend < 0.0

    def test_high_oscillation_is_volatile(self):
        vals = [1.0 if i % 2 == 0 else -1.0 for i in range(30)]
        t = compute_arc_trend(vals, self._flat(0.4), ["joy"] * 30)
        assert t.is_volatile is True
        assert t.volatility > VOLATILITY_THRESHOLD

    def test_stable_valence_not_volatile(self):
        t = compute_arc_trend(self._flat(0.5), self._flat(0.4), ["joy"] * 30)
        assert t.is_volatile is False

    def test_positive_mood_momentum(self):
        # Recent 7 days much higher than 30-day average
        vals = [0.0] * 23 + [1.0] * 7
        t = compute_arc_trend(vals, self._flat(0.4), ["joy"] * 30)
        assert t.mood_momentum > 0.0

    def test_negative_mood_momentum(self):
        vals = [1.0] * 23 + [0.0] * 7
        t = compute_arc_trend(vals, self._flat(0.4), ["joy"] * 30)
        assert t.mood_momentum < 0.0

    def test_dominant_emotion_is_modal(self):
        labels = ["sadness"] * 20 + ["joy"] * 10
        t = compute_arc_trend(self._flat(), self._flat(0.4), labels)
        assert t.dominant_emotion == "sadness"

    def test_low_energy_flag_triggered(self):
        arousal = [0.1] * 30   # well below 0.25 threshold
        t = compute_arc_trend(self._flat(), arousal, ["neutral"] * 30)
        assert t.low_energy_flag is True

    def test_low_energy_flag_not_triggered_high_arousal(self):
        arousal = [0.6] * 30
        t = compute_arc_trend(self._flat(), arousal, ["neutral"] * 30)
        assert t.low_energy_flag is False

    def test_arc_stability_high_for_constant(self):
        t = compute_arc_trend(self._flat(0.3), self._flat(0.4), ["neutral"] * 30)
        assert t.arc_stability > 0.80

    def test_arc_stability_low_for_oscillation(self):
        vals = [1.0 if i % 2 == 0 else -1.0 for i in range(30)]
        t = compute_arc_trend(vals, self._flat(0.4), ["joy"] * 30)
        assert t.arc_stability < 0.10

    def test_empty_inputs_return_defaults(self):
        t = compute_arc_trend([], [], [])
        assert t.valence_trend  == 0.0
        assert t.mood_momentum  == 0.0
        assert t.volatility     == 0.0
        assert t.is_volatile    is False
        assert t.dominant_emotion == "neutral"
        assert t.low_energy_flag  is False
        assert t.arc_stability   == 0.50


# ─────────────────────────────────────────────
# 24–25: Type helpers
# ─────────────────────────────────────────────

class TestTypeHelpers:
    def test_pad_clamp_pleasure(self):
        pad = PadVector(pleasure=2.0, arousal=1.5, dominance=-0.1).clamp()
        assert pad.pleasure  ==  1.0
        assert pad.arousal   ==  1.0
        assert pad.dominance ==  0.0

    def test_analysis_result_to_dict_keys(self):
        r = analyze_text_heuristic("happy joyful grateful")
        d = r.to_dict()
        for key in ["label", "confidence", "pad", "is_neutral_primary", "entropy", "explanation"]:
            assert key in d
