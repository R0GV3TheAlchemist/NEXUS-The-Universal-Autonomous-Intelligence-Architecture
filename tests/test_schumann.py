"""
Test suite for core/schumann.py
Spec: docs/knowledge/SCHUMANN_BIOMETRIC_ALIGNMENT_SPEC.md  (Issue #64)

9 tests covering:
  - compute_alignment formula (perfect, divergence, Kp penalty cap, never negative)
  - HRVNormalizer (baseline, excellent, rolling mean shift)
  - SchumannParser (output always 0-100)
  - AlignmentScorer UI tier mapping
"""

import pytest

from core.schumann import (
    AlignmentScorer,
    AlignmentState,
    HRVNormalizer,
    SchumannParser,
    compute_alignment,
    _score_to_ui_tier,
)


# ---------------------------------------------------------------------------
# 1. compute_alignment — perfect convergence
# ---------------------------------------------------------------------------

def test_compute_alignment_perfect() -> None:
    """hrv_score == schumann_score, kp=0 → score = 100."""
    assert compute_alignment(50.0, 50.0, 0.0) == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# 2. compute_alignment — divergence
# ---------------------------------------------------------------------------

def test_compute_alignment_divergence() -> None:
    """hrv=80, schumann=20, kp=0 → base = 100 - 60 = 40."""
    assert compute_alignment(80.0, 20.0, 0.0) == pytest.approx(40.0)


# ---------------------------------------------------------------------------
# 3. Kp penalty capped at 30
# ---------------------------------------------------------------------------

def test_kp_penalty_capped_at_30() -> None:
    """kp=20 → penalty = min(60, 30) = 30, not 60."""
    # Perfect convergence so base=100; penalty should be exactly 30
    score = compute_alignment(50.0, 50.0, 20.0)
    assert score == pytest.approx(70.0)  # 100 - 30


# ---------------------------------------------------------------------------
# 4. Alignment never negative
# ---------------------------------------------------------------------------

def test_alignment_never_negative() -> None:
    """Worst-case divergence + max Kp penalty → score >= 0."""
    # Max divergence: base = 100 - 100 = 0; max penalty = 30
    score = compute_alignment(0.0, 100.0, 9.0)
    assert score >= 0.0
    assert score == pytest.approx(0.0)  # max(0, 0 - 27) = 0


# ---------------------------------------------------------------------------
# 5. HRVNormalizer — static baseline (single reading)
# ---------------------------------------------------------------------------

def test_hrv_normalizer_baseline() -> None:
    """RMSSD = 20ms (static min) with no history → score = 0."""
    n = HRVNormalizer()
    score = n.normalize(20.0)
    assert score == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 6. HRVNormalizer — excellent HRV (static range)
# ---------------------------------------------------------------------------

def test_hrv_normalizer_excellent() -> None:
    """RMSSD = 100ms (static max) with no prior history → score = 100."""
    n = HRVNormalizer()
    score = n.normalize(100.0)
    assert score == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# 7. HRVNormalizer — rolling mean shifts normalization
# ---------------------------------------------------------------------------

def test_hrv_normalizer_rolling_mean() -> None:
    """
    With a rolling history of [20, 20, ..., 80], normalizing 80
    should yield 100.0 (top of the observed range).
    """
    n = HRVNormalizer()
    for _ in range(10):
        n.add_reading(20.0)
    score = n.normalize(80.0)
    assert score == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# 8. SchumannParser — output always 0-100
# ---------------------------------------------------------------------------

def test_schumann_parser_normalizes_to_range() -> None:
    """Any sequence of amplitude readings must produce scores in [0, 100]."""
    p = SchumannParser()
    readings = [0.05, 0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    for r in readings:
        score = p.normalize(r)
        assert 0.0 <= score <= 100.0, f"Out of range for amplitude={r}: {score}"


# ---------------------------------------------------------------------------
# 9. AlignmentScorer — UI tier mapping
# ---------------------------------------------------------------------------

def test_alignment_state_ui_tier_mapping() -> None:
    """Verify spec UI tier thresholds: vibrant>=80, standard 40-59, minimal<20."""
    assert _score_to_ui_tier(85.0) == "vibrant"
    assert _score_to_ui_tier(80.0) == "vibrant"
    assert _score_to_ui_tier(65.0) == "full"
    assert _score_to_ui_tier(50.0) == "standard"
    assert _score_to_ui_tier(30.0) == "core"
    assert _score_to_ui_tier(15.0) == "minimal"
    assert _score_to_ui_tier(0.0)  == "minimal"
