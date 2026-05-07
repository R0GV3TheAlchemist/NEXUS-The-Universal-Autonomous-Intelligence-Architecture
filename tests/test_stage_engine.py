"""
Test suite for core/stage_engine.py
Spec: docs/knowledge/STAGE_ENGINE_SPEC.md  (Issue #63)

11 tests covering:
  - Marker scoring profiles
  - 4-of-6 advance gate
  - Minimum window enforcement
  - Regression detection (5-of-6, 14-day)
  - Regression labeling
  - StageTransition history writing
  - SQLite round-trip persistence
  - Shadow Engine gate
"""

import tempfile
from pathlib import Path
from dataclasses import asdict

import pytest

from core.stage_engine import (
    MarkerScorer,
    StageEvaluator,
    StageEngine,
    StageRecord,
    MarkerScores,
    StageTransition,
    ADVANCE_MARKERS,
    get_shadow_mode,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scorer() -> MarkerScorer:
    return MarkerScorer()


@pytest.fixture
def evaluator() -> StageEvaluator:
    return StageEvaluator()


@pytest.fixture
def tmp_engine(tmp_path: Path) -> StageEngine:
    return StageEngine(db_path=tmp_path / "test_stage.db")


def _make_record(
    stage: int = 1,
    days: int = 0,
    scores: MarkerScores | None = None,
) -> StageRecord:
    if scores is None:
        scores = MarkerScores(
            decision_entropy=50.0,
            hrv_coherence=50.0,
            journaling_depth=50.0,
            focus_session_length=30.0,
            goal_completion_rate=50.0,
            emotional_arc_stability=50.0,
        )
    return StageRecord(
        user_id="test_user",
        current_stage=stage,
        stage_entered_at="2026-01-01T00:00:00+00:00",
        days_in_stage=days,
        marker_scores=scores,
    )


# ---------------------------------------------------------------------------
# 1. Marker Scoring — Stage 1 Profile
# ---------------------------------------------------------------------------

def test_marker_scoring_stage1_profile(scorer: MarkerScorer) -> None:
    """High entropy + low HRV → scores that reflect Stage 1 characteristics."""
    scores = scorer.score(
        decision_entropy_raw=90.0,
        hrv_rmssd_ms=25.0,
        journal_word_count=50.0,
        focus_minutes_avg=8.0,
        goal_completion_pct=10.0,
        emotional_volatility_raw=85.0,
    )
    assert scores.decision_entropy == pytest.approx(90.0)
    assert scores.hrv_coherence < 10.0          # low coherence
    assert scores.journaling_depth < 15.0       # shallow
    assert scores.focus_session_length == pytest.approx(8.0)
    assert scores.goal_completion_rate == pytest.approx(10.0)
    assert scores.emotional_arc_stability < 20.0  # volatile


# ---------------------------------------------------------------------------
# 2. Marker Scoring — Stage 4 Profile
# ---------------------------------------------------------------------------

def test_marker_scoring_stage4_profile(scorer: MarkerScorer) -> None:
    """High goal completion + stable HRV → Stage 4 score profile."""
    scores = scorer.score(
        decision_entropy_raw=30.0,
        hrv_rmssd_ms=90.0,
        journal_word_count=600.0,
        focus_minutes_avg=75.0,
        goal_completion_pct=80.0,
        emotional_volatility_raw=15.0,
    )
    assert scores.decision_entropy == pytest.approx(30.0)
    assert scores.hrv_coherence > 80.0
    assert scores.journaling_depth == pytest.approx(100.0)  # clamped at 100
    assert scores.focus_session_length == pytest.approx(75.0)
    assert scores.goal_completion_rate == pytest.approx(80.0)
    assert scores.emotional_arc_stability > 80.0


# ---------------------------------------------------------------------------
# 3. Advance requires 4 of 6 markers
# ---------------------------------------------------------------------------

def test_advance_requires_4_of_6(evaluator: StageEvaluator) -> None:
    """3 markers met → no candidate; 4 markers met → candidate (window OK)."""
    # Build scores that meet exactly 3 Stage-1 advance markers
    # Stage 1 advance: entropy < 70, hrv >= 30, journaling >= 20,
    #                  focus >= 15, goal >= 20, stability >= 30
    scores_3_met = MarkerScores(
        decision_entropy=65.0,   # < 70 ✓
        hrv_coherence=35.0,      # >= 30 ✓
        journaling_depth=25.0,   # >= 20 ✓
        focus_session_length=10.0,   # < 15 ✗
        goal_completion_rate=15.0,   # < 20 ✗
        emotional_arc_stability=25.0, # < 30 ✗
    )
    record = _make_record(stage=1, days=21)
    candidate, _, _ = evaluator.evaluate(record, scores_3_met)
    assert candidate is False

    # Build scores that meet exactly 4 markers
    scores_4_met = MarkerScores(
        decision_entropy=65.0,   # ✓
        hrv_coherence=35.0,      # ✓
        journaling_depth=25.0,   # ✓
        focus_session_length=20.0,   # >= 15 ✓
        goal_completion_rate=15.0,   # ✗
        emotional_arc_stability=25.0, # ✗
    )
    record2 = _make_record(stage=1, days=21)
    candidate2, _, _ = evaluator.evaluate(record2, scores_4_met)
    assert candidate2 is True


# ---------------------------------------------------------------------------
# 4. Minimum window blocks early transition
# ---------------------------------------------------------------------------

def test_minimum_window_blocks_early_transition(evaluator: StageEvaluator) -> None:
    """4 markers met but only 5 days in stage → no transition."""
    scores = MarkerScores(
        decision_entropy=65.0,
        hrv_coherence=35.0,
        journaling_depth=25.0,
        focus_session_length=20.0,
        goal_completion_rate=15.0,
        emotional_arc_stability=25.0,
    )
    record = _make_record(stage=1, days=5)  # 5 < 21 minimum
    candidate, _, _ = evaluator.evaluate(record, scores)
    assert candidate is False


# ---------------------------------------------------------------------------
# 5. Minimum window allows transition after 21 days
# ---------------------------------------------------------------------------

def test_minimum_window_allows_transition_after_21_days(evaluator: StageEvaluator) -> None:
    """4 markers met + 21 days in Stage 1 → transition candidate fires."""
    scores = MarkerScores(
        decision_entropy=65.0,
        hrv_coherence=35.0,
        journaling_depth=25.0,
        focus_session_length=20.0,
        goal_completion_rate=15.0,
        emotional_arc_stability=25.0,
    )
    record = _make_record(stage=1, days=21)
    candidate, _, _ = evaluator.evaluate(record, scores)
    assert candidate is True


# ---------------------------------------------------------------------------
# 6. Regression requires 5 of 6 prior-stage markers for 14 days
# ---------------------------------------------------------------------------

def test_regression_requires_5_of_6_for_14_days(evaluator: StageEvaluator) -> None:
    """4 prior-stage markers → no regression; 5 + 14 days → regression."""
    # Stage 2 user regressing toward Stage 1 behavior
    # Stage 1 advance markers: entropy < 70, hrv >= 30, journaling >= 20,
    #                           focus >= 15, goal >= 20, stability >= 30
    # Regression = FAILING those markers
    # Failing: entropy >= 70 (fail lt<70), hrv < 30 (fail gte>=30), etc.

    # 4 failing markers (below regression threshold)
    scores_4_failing = MarkerScores(
        decision_entropy=75.0,   # fails < 70 ✓ (failing)
        hrv_coherence=25.0,      # fails >= 30 ✓
        journaling_depth=15.0,   # fails >= 20 ✓
        focus_session_length=20.0,   # passes >= 15 ✗ (not failing)
        goal_completion_rate=25.0,   # passes >= 20 ✗
        emotional_arc_stability=25.0, # fails >= 30 ✓
    )
    record = _make_record(stage=2, days=30)
    _, regress, _ = evaluator.evaluate(record, scores_4_failing, regression_days_sustained=14)
    assert regress is False

    # 5 failing markers + 14 days → regression
    scores_5_failing = MarkerScores(
        decision_entropy=75.0,   # failing ✓
        hrv_coherence=25.0,      # failing ✓
        journaling_depth=15.0,   # failing ✓
        focus_session_length=10.0,   # fails >= 15 ✓
        goal_completion_rate=25.0,   # passes ✗
        emotional_arc_stability=25.0, # failing ✓
    )
    record2 = _make_record(stage=2, days=30)
    _, regress2, _ = evaluator.evaluate(record2, scores_5_failing, regression_days_sustained=14)
    assert regress2 is True


# ---------------------------------------------------------------------------
# 7. Regression is labeled 'StageXR', not 'failure'
# ---------------------------------------------------------------------------

def test_regression_labeled_not_failure(tmp_engine: StageEngine) -> None:
    """Regression transition writes label '2R' (not 'failure') to history."""
    uid = "regress_user"
    # Seed with a Stage 2 record with enough days
    record = _make_record(stage=2, days=30)
    record.user_id = uid
    tmp_engine.save(record)

    # Force regression: 5 failing markers, 14 days sustained
    result = tmp_engine.update(
        uid,
        decision_entropy_raw=75.0,
        hrv_rmssd_ms=22.0,       # hrv_coherence ≈ 2.5 → fails >= 30
        journal_word_count=50.0, # journaling_depth = 10 → fails >= 20
        focus_minutes_avg=8.0,   # fails >= 15
        goal_completion_pct=25.0,# passes >= 20 (only 4 failing)
        emotional_volatility_raw=80.0,  # stability = 20 → fails >= 30
        regression_days_sustained=14,
    )

    assert len(result.stage_history) == 1
    t = result.stage_history[0]
    assert t.label == "2R"
    assert "failure" not in t.label
    assert t.from_stage == 2
    assert t.to_stage == 1


# ---------------------------------------------------------------------------
# 8. Transition writes StageTransition to history
# ---------------------------------------------------------------------------

def test_transition_writes_stage_history(tmp_engine: StageEngine) -> None:
    """Advance transition writes a StageTransition record with correct fields."""
    uid = "advance_user"
    record = _make_record(stage=1, days=21)
    record.user_id = uid
    tmp_engine.save(record)

    result = tmp_engine.update(
        uid,
        decision_entropy_raw=60.0,   # < 70 ✓
        hrv_rmssd_ms=50.0,           # coherence ≈ 37.5 >= 30 ✓
        journal_word_count=120.0,    # depth = 24 >= 20 ✓
        focus_minutes_avg=20.0,      # >= 15 ✓
        goal_completion_pct=10.0,    # < 20 ✗
        emotional_volatility_raw=60.0,  # stability = 40 >= 30 ✓
    )

    assert result.current_stage == 2
    assert len(result.stage_history) == 1
    t = result.stage_history[0]
    assert t.from_stage == 1
    assert t.to_stage == 2
    assert len(t.markers_met) >= 4
    assert t.label == ""
    assert t.transitioned_at != ""


# ---------------------------------------------------------------------------
# 9. SQLite round-trip persistence
# ---------------------------------------------------------------------------

def test_stage_record_persists_and_reloads(tmp_engine: StageEngine) -> None:
    """StageRecord survives a SQLite write/read round-trip."""
    uid = "persist_user"
    record = _make_record(stage=3, days=45)
    record.user_id = uid
    record.stage_history.append(StageTransition(
        from_stage=2, to_stage=3,
        transitioned_at="2026-04-01T00:00:00+00:00",
        markers_met=["hrv_coherence", "journaling_depth"],
        ceremony_shown=True,
        label="",
    ))
    tmp_engine.save(record)

    loaded = tmp_engine.load(uid)
    assert loaded.current_stage == 3
    assert loaded.days_in_stage == 45
    assert len(loaded.stage_history) == 1
    assert loaded.stage_history[0].from_stage == 2
    assert loaded.stage_history[0].ceremony_shown is True
    assert loaded.marker_scores.hrv_coherence == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# 10. Shadow Engine gate — Stage 1
# ---------------------------------------------------------------------------

def test_shadow_engine_gate_stage1() -> None:
    """Stage 1 Shadow Engine mode must be 'off'."""
    assert get_shadow_mode(1) == "off"


# ---------------------------------------------------------------------------
# 11. Shadow Engine gate — Stage 3
# ---------------------------------------------------------------------------

def test_shadow_engine_gate_stage3() -> None:
    """Stage 3 Shadow Engine mode must be 'full'."""
    assert get_shadow_mode(3) == "full"
