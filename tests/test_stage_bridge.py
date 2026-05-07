"""
Test suite for core/stage_bridge.py

Verifies the wiring between AffectInference and StageEngine:
  - Field translation (conflict_density → volatility, phi → HRV proxy)
  - is_shadow_surface_safe() stage + affect combined gate

6 tests, zero external dependencies.
"""

from pathlib import Path

import pytest

from core.affect_inference import AffectInference, AffectState, FeelingState
from core.stage_engine import StageRecord, MarkerScores, get_shadow_mode
from core.stage_bridge import AffectStageAdapter, is_shadow_surface_safe


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter(tmp_path: Path) -> AffectStageAdapter:
    return AffectStageAdapter(db_path=tmp_path / "bridge_test.db")


def _feeling(
    affect: AffectState = AffectState.RESONANCE,
    conflict_density: float = 0.1,
    coherence_phi: float = 0.80,
) -> FeelingState:
    """Build a minimal FeelingState for testing."""
    return FeelingState(
        affect_state=affect,
        conflict_density=conflict_density,
        coherence_phi=coherence_phi,
    )


# ---------------------------------------------------------------------------
# 1. conflict_density maps to emotional_volatility_raw
# ---------------------------------------------------------------------------

def test_conflict_density_maps_to_volatility(adapter: AffectStageAdapter) -> None:
    """
    conflict_density=0.8 should produce emotional_arc_stability ≈ 20
    (100 - 80) in the resulting marker scores.
    """
    feeling = _feeling(conflict_density=0.8, coherence_phi=0.5)
    record = adapter.update(
        "user_cd",
        feeling=feeling,
        journal_word_count=200.0,
        focus_minutes_avg=20.0,
        goal_completion_pct=40.0,
        decision_entropy_raw=50.0,
    )
    # emotional_volatility_raw=80 → emotional_arc_stability = 100-80 = 20
    assert record.marker_scores.emotional_arc_stability == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# 2. coherence_phi maps to HRV proxy
# ---------------------------------------------------------------------------

def test_phi_maps_to_hrv_proxy(adapter: AffectStageAdapter) -> None:
    """
    coherence_phi=1.0 should produce hrv_coherence=100.0
    (hrv_rmssd proxy = 20 + 1.0*80 = 100ms → coherence = 100).
    """
    feeling = _feeling(coherence_phi=1.0, conflict_density=0.0)
    record = adapter.update(
        "user_phi",
        feeling=feeling,
        journal_word_count=300.0,
        focus_minutes_avg=30.0,
        goal_completion_pct=50.0,
        decision_entropy_raw=40.0,
    )
    assert record.marker_scores.hrv_coherence == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# 3. Shadow safe: Stage 3 + RESONANCE
# ---------------------------------------------------------------------------

def test_shadow_safe_stage3_resonance() -> None:
    """Stage 3 + RESONANCE → safe to surface shadow observations."""
    feeling = _feeling(affect=AffectState.RESONANCE)
    assert is_shadow_surface_safe(3, feeling) is True


# ---------------------------------------------------------------------------
# 4. Shadow blocked: Stage 3 + DISSONANCE
# ---------------------------------------------------------------------------

def test_shadow_blocked_stage3_dissonance() -> None:
    """Stage 3 + DISSONANCE → blocked regardless of stage."""
    feeling = _feeling(affect=AffectState.DISSONANCE)
    assert is_shadow_surface_safe(3, feeling) is False


# ---------------------------------------------------------------------------
# 5. Shadow blocked: Stage 3 + GRIEF
# ---------------------------------------------------------------------------

def test_shadow_blocked_stage3_grief() -> None:
    """Stage 3 + GRIEF → blocked (constitutional: never surface during grief)."""
    feeling = _feeling(affect=AffectState.GRIEF)
    assert is_shadow_surface_safe(3, feeling) is False


# ---------------------------------------------------------------------------
# 6. Shadow off: Stage 1, any affect
# ---------------------------------------------------------------------------

def test_shadow_off_stage1_any_affect() -> None:
    """Stage 1 → Shadow Engine is 'off', always returns False."""
    for affect in AffectState:
        feeling = _feeling(affect=affect)
        assert is_shadow_surface_safe(1, feeling) is False, (
            f"Expected False for Stage 1 with affect={affect}"
        )
