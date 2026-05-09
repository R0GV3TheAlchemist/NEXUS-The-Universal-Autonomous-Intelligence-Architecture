"""
tests/test_schumann_alignment.py

pytest suite for core/schumann_alignment.py
Issue: #64 (Phase 2 — Python sidecar)

Covers:
  - compute_alignment() formula and boundary conditions
  - score_to_ui_tier() tier mapping
  - HRVNormalizer: ingestion, normalisation, edge cases
  - SchumannParser: ingestion, normalisation, edge cases
  - AlignmentStateEmitter: all four failure modes
  - AlignmentState.to_json() round-trip
"""

from __future__ import annotations

import asyncio
import json
import math
import pytest

from core.schumann_alignment import (
    AlignmentState,
    AlignmentStateEmitter,
    HRVNormalizer,
    SchumannParser,
    compute_alignment,
    score_to_ui_tier,
)


# ===========================================================================
# compute_alignment
# ===========================================================================

class TestComputeAlignment:

    def test_perfect_alignment_no_kp(self):
        """Identical HRV and Schumann scores with Kp=0 → score 100."""
        assert compute_alignment(50.0, 50.0, 0.0) == pytest.approx(100.0)

    def test_perfect_alignment_with_kp_penalty(self):
        """Kp=5 should subtract 15 points from a perfect base."""
        score = compute_alignment(50.0, 50.0, 5.0)
        assert score == pytest.approx(85.0)

    def test_kp_penalty_capped_at_30(self):
        """Kp=20 → penalty=30 (capped), not 60."""
        score = compute_alignment(50.0, 50.0, 20.0)
        assert score == pytest.approx(70.0)

    def test_kp_penalty_exactly_30_at_kp10(self):
        """Kp=10 → penalty=30 exactly."""
        score = compute_alignment(50.0, 50.0, 10.0)
        assert score == pytest.approx(70.0)

    def test_score_never_below_zero(self):
        """Score is clamped at 0 even when divergence + kp would go negative."""
        score = compute_alignment(0.0, 100.0, 30.0)
        assert score == 0.0

    def test_large_divergence_reduces_score(self):
        """HRV=0, Schumann=100 → base=0, kp_penalty=0 → score=0."""
        assert compute_alignment(0.0, 100.0, 0.0) == pytest.approx(0.0)

    def test_moderate_divergence(self):
        """HRV=70, Schumann=50, Kp=2 → base=80, penalty=6 → score=74."""
        assert compute_alignment(70.0, 50.0, 2.0) == pytest.approx(74.0)

    def test_boundary_hrv_0_schumann_0(self):
        assert compute_alignment(0.0, 0.0, 0.0) == pytest.approx(100.0)

    def test_boundary_hrv_100_schumann_100(self):
        assert compute_alignment(100.0, 100.0, 0.0) == pytest.approx(100.0)

    def test_invalid_hrv_above_100(self):
        with pytest.raises(ValueError):
            compute_alignment(101.0, 50.0, 0.0)

    def test_invalid_hrv_negative(self):
        with pytest.raises(ValueError):
            compute_alignment(-1.0, 50.0, 0.0)

    def test_invalid_schumann_above_100(self):
        with pytest.raises(ValueError):
            compute_alignment(50.0, 101.0, 0.0)

    def test_invalid_kp_negative(self):
        with pytest.raises(ValueError):
            compute_alignment(50.0, 50.0, -1.0)


# ===========================================================================
# score_to_ui_tier
# ===========================================================================

class TestScoreToUiTier:

    @pytest.mark.parametrize("score,expected", [
        (100.0, "vibrant"),
        (80.0,  "vibrant"),
        (79.9,  "full"),
        (60.0,  "full"),
        (59.9,  "standard"),
        (40.0,  "standard"),
        (39.9,  "core"),
        (20.0,  "core"),
        (19.9,  "minimal"),
        (0.0,   "minimal"),
    ])
    def test_tier_boundaries(self, score, expected):
        assert score_to_ui_tier(score) == expected


# ===========================================================================
# HRVNormalizer
# ===========================================================================

class TestHRVNormalizer:

    def test_returns_50_with_no_history(self):
        norm = HRVNormalizer()
        assert norm.normalize(60.0) == pytest.approx(50.0)

    def test_returns_50_with_one_sample(self):
        norm = HRVNormalizer()
        norm.ingest(60.0)
        assert norm.normalize(60.0) == pytest.approx(50.0)

    def test_baseline_mean_at_two_samples(self):
        norm = HRVNormalizer()
        norm.ingest(50.0)
        norm.ingest(60.0)
        assert norm.baseline_mean == pytest.approx(55.0)

    def test_normalise_at_mean_returns_50(self):
        norm = HRVNormalizer()
        for v in [50.0, 60.0, 70.0, 80.0]:
            norm.ingest(v)
        mean = norm.baseline_mean
        score = norm.normalize(mean)
        assert score == pytest.approx(50.0, abs=0.01)

    def test_score_clamped_at_100(self):
        """Extreme high RMSSD should not exceed 100."""
        norm = HRVNormalizer()
        for _ in range(50):
            norm.ingest(50.0)
        assert norm.normalize(50000.0) == pytest.approx(100.0)

    def test_score_clamped_at_0(self):
        """Extreme low RMSSD should not go below 0."""
        norm = HRVNormalizer()
        for _ in range(50):
            norm.ingest(50.0)
        assert norm.normalize(0.0) >= 0.0

    def test_constant_history_returns_50(self):
        """Zero stdev → baseline 50 to avoid division by zero."""
        norm = HRVNormalizer()
        for _ in range(10):
            norm.ingest(55.0)
        assert norm.normalize(55.0) == pytest.approx(50.0)

    def test_negative_rmssd_raises(self):
        norm = HRVNormalizer()
        with pytest.raises(ValueError):
            norm.ingest(-1.0)

    def test_sample_count(self):
        norm = HRVNormalizer()
        for i in range(5):
            norm.ingest(float(i * 10))
        assert norm.sample_count == 5


# ===========================================================================
# SchumannParser
# ===========================================================================

class TestSchumannParser:

    def test_returns_50_with_no_history(self):
        parser = SchumannParser()
        assert parser.normalize(1.0) == pytest.approx(50.0)

    def test_normalise_at_mean_returns_50(self):
        parser = SchumannParser()
        for v in [1.0, 2.0, 3.0, 4.0]:
            parser.ingest(v)
        mean = sum([1.0, 2.0, 3.0, 4.0]) / 4
        score = parser.normalize(mean)
        assert score == pytest.approx(50.0, abs=0.01)

    def test_score_clamped_at_100(self):
        parser = SchumannParser()
        for _ in range(50):
            parser.ingest(2.0)
        assert parser.normalize(99999.0) == pytest.approx(100.0)

    def test_score_clamped_at_0(self):
        parser = SchumannParser()
        for _ in range(50):
            parser.ingest(50.0)
        assert parser.normalize(0.0) >= 0.0

    def test_constant_history_returns_50(self):
        parser = SchumannParser()
        for _ in range(10):
            parser.ingest(3.0)
        assert parser.normalize(3.0) == pytest.approx(50.0)

    def test_negative_amplitude_raises_on_ingest(self):
        parser = SchumannParser()
        with pytest.raises(ValueError):
            parser.ingest(-0.1)

    def test_negative_amplitude_raises_on_normalize(self):
        parser = SchumannParser()
        with pytest.raises(ValueError):
            parser.normalize(-1.0)


# ===========================================================================
# AlignmentStateEmitter — failure modes
# ===========================================================================

class TestAlignmentStateEmitter:

    def _make_emitter(self) -> AlignmentStateEmitter:
        hrv = HRVNormalizer()
        sch = SchumannParser()
        return AlignmentStateEmitter(hrv, sch)

    # --- happy path --------------------------------------------------------

    def test_happy_path_returns_alignment_state(self):
        emitter = self._make_emitter()
        state = asyncio.run(
            emitter.compute(raw_rmssd=60.0, raw_schumann_amplitude=2.0, solar_kp=1.0)
        )
        assert isinstance(state, AlignmentState)
        assert 0.0 <= state.score <= 100.0
        assert state.ui_tier in ("minimal", "core", "standard", "full", "vibrant")

    # --- failure mode 1: wearable unavailable ------------------------------

    def test_failure_mode_hrv_unavailable(self):
        """No wearable → hrv_score=50, fallback recorded."""
        emitter = self._make_emitter()
        state = asyncio.run(
            emitter.compute(raw_rmssd=None, raw_schumann_amplitude=2.0, solar_kp=0.0)
        )
        assert state.hrv_score == pytest.approx(50.0)
        assert "hrv_unavailable" in state.fallback_mode

    # --- failure mode 2: schumann feed unavailable -------------------------

    def test_failure_mode_schumann_unavailable(self):
        """Feed down → schumann_score=50, fallback recorded."""
        emitter = self._make_emitter()
        state = asyncio.run(
            emitter.compute(raw_rmssd=60.0, raw_schumann_amplitude=None, solar_kp=0.0)
        )
        assert state.schumann_score == pytest.approx(50.0)
        assert "schumann_unavailable" in state.fallback_mode

    # --- failure mode 3: both unavailable → standard tier ------------------

    def test_failure_mode_both_unavailable_forces_standard(self):
        """Both feeds down → score=50 → standard tier."""
        emitter = self._make_emitter()
        state = asyncio.run(
            emitter.compute(raw_rmssd=None, raw_schumann_amplitude=None, solar_kp=0.0)
        )
        assert state.score == pytest.approx(50.0)
        assert state.ui_tier == "standard"
        assert "both_unavailable_standard_forced" in state.fallback_mode

    # --- failure mode 4: Kp > 8 storm → restorative (score=0) -------------

    def test_failure_mode_kp_storm_forces_score_zero(self):
        """Kp > 8 → score forced to 0 regardless of HRV/Schumann."""
        emitter = self._make_emitter()
        state = asyncio.run(
            emitter.compute(raw_rmssd=60.0, raw_schumann_amplitude=2.0, solar_kp=9.0)
        )
        assert state.score == pytest.approx(0.0)
        assert state.ui_tier == "minimal"
        assert "kp_storm" in state.fallback_mode

    def test_kp_exactly_8_does_not_trigger_storm(self):
        """Kp == 8.0 is not *above* the threshold — no storm override."""
        emitter = self._make_emitter()
        state = asyncio.run(
            emitter.compute(raw_rmssd=None, raw_schumann_amplitude=None, solar_kp=8.0)
        )
        assert "kp_storm" not in state.fallback_mode

    # --- last_state --------------------------------------------------------

    def test_last_state_is_set_after_compute(self):
        emitter = self._make_emitter()
        assert emitter.last_state is None
        asyncio.run(
            emitter.compute(raw_rmssd=55.0, raw_schumann_amplitude=1.5, solar_kp=0.0)
        )
        assert emitter.last_state is not None

    # --- JSON round-trip ---------------------------------------------------

    def test_to_json_round_trip(self):
        emitter = self._make_emitter()
        state = asyncio.run(
            emitter.compute(raw_rmssd=60.0, raw_schumann_amplitude=2.0, solar_kp=1.0)
        )
        payload = json.loads(state.to_json())
        assert payload["score"] == state.score
        assert payload["ui_tier"] == state.ui_tier
        assert payload["hrv_score"] == state.hrv_score
        assert payload["schumann_score"] == state.schumann_score
        assert "last_updated" in payload
        assert "fallback_mode" in payload
