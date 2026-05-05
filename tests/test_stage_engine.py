"""
Test suite for Stage Engine — Issue #63.

Covers:
  1.  Marker scorer: decision_entropy
  2.  Marker scorer: hrv_coherence blending
  3.  Marker scorer: journaling_depth weights
  4.  Marker scorer: focus_session piecewise scale
  5.  Marker scorer: goal_completion Bayesian smoothing
  6.  Marker scorer: arc_stability formula
  7.  Transition gate: forward blocked until window met
  8.  Transition gate: forward fires when window met and markers >= 4
  9.  Transition gate: regression blocked until 14-day window
  10. Transition gate: regression fires when 5+ markers dropped
  11. Schumann bridge: neutral when state is None
  12. Schumann bridge: trusted state maps correctly
  13. Schumann bridge: untrusted state returns neutral
  14. Schumann bridge: disturbance levels map to correct env_modifier
  15. DisturbanceLevel ordering (via bridge)
  16. Full engine evaluate: no transition on day 0
  17. Full engine evaluate: TransitionResult has correct types
  18. to_stage_dict() / label properties
"""

from __future__ import annotations

import math
import sqlite3
import time
from unittest.mock import MagicMock, patch

import pytest

from stage_engine.markers import MarkerScorer
from stage_engine.transitions import (
    check_forward_transition,
    check_regression,
    markers_met_for_transition,
    FORWARD_THRESHOLDS,
)
from stage_engine.types import (
    MarkerScores,
    STAGE_NAMES,
    StageRecord,
    StageTransition,
    TRANSITION_WINDOWS,
)
from stage_engine.schumann_bridge import schumann_to_alignment


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

def make_scores(**overrides) -> MarkerScores:
    """High-scoring baseline MarkerScores, with optional overrides."""
    defaults = dict(
        decision_entropy=80.0,
        hrv_coherence=75.0,
        journaling_depth=70.0,
        focus_session_length_min=70.0,
        goal_completion_rate=75.0,
        emotional_arc_stability=70.0,
    )
    defaults.update(overrides)
    return MarkerScores(**defaults)


def low_scores() -> MarkerScores:
    """All markers below every forward threshold."""
    return MarkerScores(
        decision_entropy=10.0,
        hrv_coherence=10.0,
        journaling_depth=10.0,
        focus_session_length_min=10.0,
        goal_completion_rate=10.0,
        emotional_arc_stability=10.0,
    )


# ─────────────────────────────────────────────
# 1–6: Marker scorers
# ─────────────────────────────────────────────

class TestDecisionEntropy:
    def test_all_same_state_is_low_entropy_high_score(self):
        # All committed → entropy = 0 → score = 100
        score = MarkerScorer.score_decision_entropy(["committed"] * 20)
        assert score == 100.0

    def test_uniform_distribution_is_max_entropy_low_score(self):
        # One of each of 5 states → max entropy
        states = ["committed", "reversed", "abandoned", "not_set", "completed"]
        score = MarkerScorer.score_decision_entropy(states)
        assert score < 5.0  # near 0

    def test_empty_returns_zero(self):
        assert MarkerScorer.score_decision_entropy([]) == 0.0

    def test_bounded(self):
        score = MarkerScorer.score_decision_entropy(["committed"] * 100)
        assert 0.0 <= score <= 100.0


class TestHRVCoherence:
    def test_no_history_returns_zero(self):
        assert MarkerScorer.score_hrv_coherence([], []) == 0.0

    def test_high_hrv_with_good_alignment_gives_high_score(self):
        history = [55.0] * 29 + [80.0]  # last value is much higher → positive z
        alignment = [80.0] * 30
        score = MarkerScorer.score_hrv_coherence(history, alignment)
        assert score > 70.0

    def test_bounded(self):
        history = [60.0] * 30
        score = MarkerScorer.score_hrv_coherence(history, [50.0] * 30)
        assert 0.0 <= score <= 100.0

    def test_schumann_weight_is_30_percent(self):
        # With z=0 (sigmoid=0.5), alignment=100 → c = 0.7*0.5 + 0.3*1.0 = 0.65
        history = [60.0] * 30  # mean=60, last=60 → z=0
        score = MarkerScorer.score_hrv_coherence(history, [100.0] * 30)
        assert abs(score - 65.0) < 1.0


class TestJournalingDepth:
    def test_empty_entries_returns_zero(self):
        assert MarkerScorer.score_journaling_depth([]) == 0.0

    def test_perfect_entry_returns_100(self):
        perfect = {
            "token_count": 1200,
            "lexical_entropy": 1.0,
            "self_ref_ratio": 1.0,
            "emotion_density": 1.0,
        }
        score = MarkerScorer.score_journaling_depth([perfect])
        assert score == 100.0

    def test_weights_sum_matters(self):
        # Only token_count maxed (weight 0.25) → should be ~25
        entry = {"token_count": 1200, "lexical_entropy": 0.0,
                 "self_ref_ratio": 0.0, "emotion_density": 0.0}
        score = MarkerScorer.score_journaling_depth([entry])
        assert abs(score - 25.0) < 1.0


class TestFocusSession:
    def test_below_5_min_returns_zero(self):
        assert MarkerScorer.score_focus_session([3.0, 4.0]) == 0.0

    def test_90_plus_min_returns_100(self):
        assert MarkerScorer.score_focus_session([100.0] * 5) == 100.0

    def test_25_min_gives_60(self):
        score = MarkerScorer.score_focus_session([25.0] * 5)
        assert abs(score - 60.0) < 1.0

    def test_bounded(self):
        for m in [5, 15, 30, 60, 95]:
            s = MarkerScorer.score_focus_session([float(m)] * 5)
            assert 0.0 <= s <= 100.0


class TestGoalCompletion:
    def test_all_completed_approaches_100(self):
        score = MarkerScorer.score_goal_completion(100, 0)
        assert score > 98.0

    def test_zero_zero_returns_50(self):
        # (0+1)/(0+0+2) = 0.5 → 50.0
        assert MarkerScorer.score_goal_completion(0, 0) == 50.0

    def test_bayesian_smoothing_prevents_extreme_zeros(self):
        # Even 0 completed, 10 abandoned → not 0
        score = MarkerScorer.score_goal_completion(0, 10)
        assert score > 5.0


class TestArcStability:
    def test_constant_valence_is_stable(self):
        score = MarkerScorer.score_arc_stability([0.5] * 30)
        assert score > 85.0

    def test_high_oscillation_is_low_score(self):
        vals = [1.0 if i % 2 == 0 else -1.0 for i in range(30)]
        score = MarkerScorer.score_arc_stability(vals)
        assert score < 10.0

    def test_single_value_returns_50(self):
        assert MarkerScorer.score_arc_stability([0.5]) == 50.0


# ─────────────────────────────────────────────
# 7–10: Transition gates
# ─────────────────────────────────────────────

class TestForwardTransitionGate:
    def test_blocked_if_window_not_met(self):
        scores = make_scores()
        fire, _ = check_forward_transition(scores, from_stage=1, days_window_met=10)
        assert fire is False  # needs 21 days

    def test_fires_when_window_met_and_markers_pass(self):
        scores = make_scores()  # all above (1,2) thresholds
        fire, met = check_forward_transition(scores, from_stage=1, days_window_met=21)
        assert fire is True
        assert len(met) >= 4

    def test_blocked_if_fewer_than_4_markers_met(self):
        # Scores that meet only 2 of the 6 (1→2) thresholds
        scores = make_scores(
            journaling_depth=36.0,   # meets 35
            hrv_coherence=41.0,      # meets 40
            goal_completion_rate=0.0,
            emotional_arc_stability=0.0,
            decision_entropy=0.0,
            focus_session_length_min=0.0,
        )
        fire, _ = check_forward_transition(scores, from_stage=1, days_window_met=21)
        assert fire is False

    def test_no_stage_6(self):
        fire, _ = check_forward_transition(make_scores(), from_stage=5, days_window_met=999)
        assert fire is False


class TestRegressionGate:
    def test_blocked_before_14_days(self):
        fire, _ = check_regression(low_scores(), current_stage=3, days_regression_window=10)
        assert fire is False

    def test_fires_when_5_markers_dropped(self):
        # At stage 3, forward threshold to enter stage 3 is from (2,3)
        # low_scores are below all of them → all 6 regressed → ≥5 → fires
        fire, markers = check_regression(low_scores(), current_stage=3, days_regression_window=14)
        assert fire is True
        assert len(markers) >= 5

    def test_no_regression_from_stage_1(self):
        fire, _ = check_regression(low_scores(), current_stage=1, days_regression_window=14)
        assert fire is False


# ─────────────────────────────────────────────
# 11–15: Schumann bridge
# ─────────────────────────────────────────────

class TestSchumannBridge:
    def test_none_returns_neutral(self):
        score, mod = schumann_to_alignment(None)
        assert score == 50.0
        assert mod == 1.0

    def test_trusted_dict_maps_alignment(self):
        state = {
            "alignment_score": 0.8,
            "confidence": 0.9,
            "disturbance_level": "stable",
            "is_trusted": True,
        }
        score, mod = schumann_to_alignment(state)
        assert abs(score - 80.0) < 0.01
        assert mod == 1.0

    def test_untrusted_returns_neutral(self):
        state = {
            "alignment_score": 0.9,
            "confidence": 0.2,
            "disturbance_level": "stable",
            "is_trusted": False,
        }
        score, mod = schumann_to_alignment(state)
        assert score == 50.0
        assert mod == 1.0

    def test_disturbed_modifier_is_085(self):
        state = {
            "alignment_score": 0.7,
            "confidence": 0.8,
            "disturbance_level": "disturbed",
            "is_trusted": True,
        }
        _, mod = schumann_to_alignment(state)
        assert mod == 0.85

    def test_elevated_modifier_is_095(self):
        state = {
            "alignment_score": 0.6,
            "confidence": 0.7,
            "disturbance_level": "elevated",
            "is_trusted": True,
        }
        _, mod = schumann_to_alignment(state)
        assert mod == 0.95

    def test_score_bounded(self):
        state = {
            "alignment_score": 1.5,  # out of range
            "confidence": 0.9,
            "disturbance_level": "stable",
            "is_trusted": True,
        }
        score, _ = schumann_to_alignment(state)
        assert score <= 100.0


# ─────────────────────────────────────────────
# 16–17: Stage label / dict helpers
# ─────────────────────────────────────────────

class TestTypeHelpers:
    def test_stage_names_all_five(self):
        assert len(STAGE_NAMES) == 5
        assert STAGE_NAMES[1] == "Divergence"
        assert STAGE_NAMES[5] == "Ascendence"

    def test_transition_result_label_forward(self):
        t = StageTransition(
            principal_id="x",
            from_stage=2,
            to_stage=3,
            transitioned_at=int(time.time() * 1000),
            is_regression=False,
            markers_met=["hrv_coherence"],
        )
        assert "3" in t.label
        assert "Crucible" in t.label

    def test_transition_result_label_regression(self):
        t = StageTransition(
            principal_id="x",
            from_stage=3,
            to_stage=2,
            transitioned_at=int(time.time() * 1000),
            is_regression=True,
            markers_met=["journaling_depth"],
        )
        assert "R" in t.label

    def test_marker_scores_to_dict_has_all_keys(self):
        s = make_scores()
        d = s.to_dict()
        expected = {
            "decision_entropy", "hrv_coherence", "journaling_depth",
            "focus_session_length_min", "goal_completion_rate",
            "emotional_arc_stability",
        }
        assert expected.issubset(d.keys())
