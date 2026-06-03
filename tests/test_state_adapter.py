"""
tests/test_state_adapter.py
Unit tests for GAIAStateAdapter, AsyncGAIAStateAdapter, and SynergyParams.

All tests use lightweight mock records — no GAIA runtime required.
See specs/architecture/STATE_ADAPTER_SPEC.md for the full test checklist.
"""
from __future__ import annotations

import math
import sys
import types
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from core.state_adapter import (
    SCHUMANN_BASELINE_HZ,
    SCHUMANN_HARMONIC_TOLERANCE,
    SOLFEGGIO_HZ,
    AsyncGAIAStateAdapter,
    GAIAStateAdapter,
    SynergyParams,
)


# ── Helpers ──────────────────────────────────────────────────────────────── #

class MockRecord:
    """Minimal duck-typed Gaian record for tests."""
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


def make_adapter(**kwargs: Any) -> GAIAStateAdapter:
    return GAIAStateAdapter(MockRecord(**kwargs))


# ── SynergyParams TypedDict ────────────────────────────────────────────────── #

class TestSynergyParamsContract:
    def test_all_keys_present(self):
        params = make_adapter().to_synergy_params()
        required = {"dominant_hz", "individuation_phase", "love_arc_stage",
                    "schumann_aligned", "coherence_score", "emotional_valence",
                    "bond_depth"}
        assert required == set(params.keys())

    def test_types_are_correct(self):
        params = make_adapter().to_synergy_params()
        assert isinstance(params["dominant_hz"], float)
        assert isinstance(params["individuation_phase"], str)
        assert isinstance(params["love_arc_stage"], str)
        assert isinstance(params["schumann_aligned"], bool)
        assert isinstance(params["coherence_score"], float)
        assert isinstance(params["emotional_valence"], float)
        assert isinstance(params["bond_depth"], float)


# ── Hz resolver ───────────────────────────────────────────────────────────── #

class TestResolveHz:
    def test_numeric_dominant_hz_passed_through(self):
        assert make_adapter(dominant_hz=639.0).resolved_hz() == 639.0

    def test_solfeggio_note_lookup_mi(self):
        assert make_adapter(active_solfeggio_note="mi").resolved_hz() == 528.0

    def test_solfeggio_note_lookup_all(self):
        for note, hz in SOLFEGGIO_HZ.items():
            assert make_adapter(active_solfeggio_note=note).resolved_hz() == hz

    def test_unknown_note_defaults_to_528(self):
        assert make_adapter(active_solfeggio_note="zzz").resolved_hz() == 528.0

    def test_missing_attrs_defaults_to_528(self):
        assert GAIAStateAdapter(MockRecord()).resolved_hz() == 528.0

    def test_zero_numeric_hz_falls_back_to_note(self):
        assert make_adapter(dominant_hz=0, active_solfeggio_note="la").resolved_hz() == 852.0


# ── Individuation resolver ─────────────────────────────────────────────────── #

class TestResolveIndividuation:
    def test_default_is_persona(self):
        assert make_adapter().resolved_individuation_phase() == "persona"

    def test_custom_phase_returned(self):
        assert make_adapter(jungian_phase="shadow").resolved_individuation_phase() == "shadow"

    def test_self_phase(self):
        assert make_adapter(jungian_phase="self").resolved_individuation_phase() == "self"


# ── Love arc resolver ─────────────────────────────────────────────────────── #

class TestResolveLoveArc:
    def test_default_is_awakening(self):
        assert make_adapter().resolved_love_arc_stage() == "awakening"

    def test_custom_stage_returned(self):
        assert make_adapter(love_arc_stage="deepening").resolved_love_arc_stage() == "deepening"


# ── Schumann resolver ─────────────────────────────────────────────────────── #

class TestResolveSchumannAlignment:
    # ── original passing tests (unchanged) ───────────────────────────────── #

    def test_explicit_true_override(self):
        assert make_adapter(schumann_aligned=True).resolved_schumann_aligned() is True

    def test_explicit_false_override(self):
        assert make_adapter(schumann_aligned=False).resolved_schumann_aligned() is False

    def test_computed_aligned_within_tolerance(self):
        # 528 Hz mod 7.83 ≈ 0.06 → harmonic_phase ≈ 0.008 < 0.10 → aligned
        adapter = make_adapter(dominant_hz=528.0)
        assert adapter.resolved_schumann_aligned() is True

    def test_computed_not_aligned(self):
        # 500 Hz mod 7.83 ≈ 3.36 → harmonic_phase ≈ 0.43 → not aligned
        adapter = make_adapter(dominant_hz=500.0)
        assert adapter.resolved_schumann_aligned() is False

    def test_custom_schumann_hz(self):
        adapter = make_adapter(dominant_hz=14.0, schumann_hz=7.0)
        # 14.0 mod 7.0 = 0.0 → harmonic_phase = 0.0 < 0.10 → aligned
        assert adapter.resolved_schumann_aligned() is True

    # ── Bug 1: float modulo precision at exact harmonic multiples ─────────── #
    #
    # 15.66 / 7.83 = 2.0 exactly, but IEEE-754 fmod yields a residual close
    # to 7.83 instead of 0.0.  Without the epsilon correction the old code
    # would land this in the upper window only by luck; for other exact
    # multiples it could miss entirely.

    def test_exact_double_harmonic_aligned(self):
        """2× schumann — float residual must be snapped to 0 (aligned)."""
        # 15.66 % 7.83 → ~7.8299... without correction → phase ~0.9999...
        # With correction: raw_mod snapped to 0.0 → phase 0.0 → aligned
        adapter = make_adapter(dominant_hz=15.66, schumann_hz=7.83)
        assert adapter.resolved_schumann_aligned() is True

    def test_exact_triple_harmonic_aligned(self):
        """3× schumann — same residual trap at a higher multiple."""
        adapter = make_adapter(dominant_hz=23.49, schumann_hz=7.83)
        assert adapter.resolved_schumann_aligned() is True

    def test_exact_large_harmonic_aligned(self):
        """67× schumann (≈ 524.61 Hz) — residual at a high harmonic."""
        hz = 7.83 * 67  # 524.61 — near mi (528 Hz)
        adapter = make_adapter(dominant_hz=hz, schumann_hz=7.83)
        assert adapter.resolved_schumann_aligned() is True

    # ── Tolerance boundary tests ──────────────────────────────────────────── #
    #
    # Verify the 10% window is respected precisely at its edges.

    def test_just_inside_lower_boundary_aligned(self):
        """harmonic_phase = tolerance - small_delta → aligned."""
        schumann = 10.0
        # phase = 0.09 (just inside 10% lower window)
        hz = schumann * 10 + schumann * 0.09   # 100 + 0.9 = 100.9
        adapter = make_adapter(dominant_hz=hz, schumann_hz=schumann)
        assert adapter.resolved_schumann_aligned() is True

    def test_just_outside_lower_boundary_not_aligned(self):
        """harmonic_phase = tolerance + small_delta → not aligned."""
        schumann = 10.0
        # phase = 0.11 (just outside 10% lower window)
        hz = schumann * 10 + schumann * 0.11   # 100 + 1.1 = 101.1
        adapter = make_adapter(dominant_hz=hz, schumann_hz=schumann)
        assert adapter.resolved_schumann_aligned() is False

    def test_just_inside_upper_boundary_aligned(self):
        """harmonic_phase = 1 - tolerance + small_delta → aligned."""
        schumann = 10.0
        # phase = 0.91 (just inside 10% upper window)
        hz = schumann * 10 + schumann * 0.91   # 100 + 9.1 = 109.1
        adapter = make_adapter(dominant_hz=hz, schumann_hz=schumann)
        assert adapter.resolved_schumann_aligned() is True

    def test_just_outside_upper_boundary_not_aligned(self):
        """harmonic_phase = 1 - tolerance - small_delta → not aligned."""
        schumann = 10.0
        # phase = 0.89 (just outside 10% upper window)
        hz = schumann * 10 + schumann * 0.89   # 100 + 8.9 = 108.9
        adapter = make_adapter(dominant_hz=hz, schumann_hz=schumann)
        assert adapter.resolved_schumann_aligned() is False

    # ── Bug 2: degenerate / non-finite schumann_hz values ─────────────────── #

    def test_schumann_hz_zero_returns_false(self):
        """schumann_hz=0 must not cause ZeroDivisionError or NaN result."""
        adapter = make_adapter(dominant_hz=528.0, schumann_hz=0.0)
        assert adapter.resolved_schumann_aligned() is False

    def test_schumann_hz_negative_returns_false(self):
        """Negative schumann is physically nonsensical → not aligned."""
        adapter = make_adapter(dominant_hz=528.0, schumann_hz=-7.83)
        assert adapter.resolved_schumann_aligned() is False

    def test_schumann_hz_nan_returns_false(self):
        """NaN from a broken sensor must not propagate into SynergyEngine."""
        adapter = make_adapter(dominant_hz=528.0, schumann_hz=float("nan"))
        assert adapter.resolved_schumann_aligned() is False

    def test_schumann_hz_inf_returns_false(self):
        """Infinite schumann_hz is non-physical → not aligned."""
        adapter = make_adapter(dominant_hz=528.0, schumann_hz=float("inf"))
        assert adapter.resolved_schumann_aligned() is False


# ── Coherence resolver ────────────────────────────────────────────────────── #

class TestResolveCoherence:
    def test_normal_value(self):
        assert make_adapter(hrv_coherence_score=0.75).resolved_coherence() == 0.75

    def test_clamped_high(self):
        assert make_adapter(hrv_coherence_score=1.5).resolved_coherence() == 1.0

    def test_clamped_low(self):
        assert make_adapter(hrv_coherence_score=-0.3).resolved_coherence() == 0.0

    def test_fallback_to_coherence_score(self):
        assert make_adapter(coherence_score=0.6).resolved_coherence() == 0.6

    def test_default_is_0_5(self):
        assert make_adapter().resolved_coherence() == 0.5

    def test_invalid_type_returns_default(self):
        assert make_adapter(hrv_coherence_score="bad").resolved_coherence() == 0.5


# ── Emotional valence resolver ────────────────────────────────────────────── #

class TestResolveEmotionalValence:
    def test_normal_value(self):
        assert make_adapter(affective_valence=0.3).resolved_emotional_valence() == 0.3

    def test_clamped_high(self):
        assert make_adapter(affective_valence=2.0).resolved_emotional_valence() == 1.0

    def test_clamped_low(self):
        assert make_adapter(affective_valence=-5.0).resolved_emotional_valence() == -1.0

    def test_fallback_to_emotional_valence(self):
        assert make_adapter(emotional_valence=0.55).resolved_emotional_valence() == 0.55

    def test_default_is_0(self):
        assert make_adapter().resolved_emotional_valence() == 0.0


# ── Bond depth resolver ───────────────────────────────────────────────────── #

class TestResolveBondDepth:
    def test_normal_value(self):
        assert make_adapter(bond_depth=0.88).resolved_bond_depth() == 0.88

    def test_clamped_high(self):
        assert make_adapter(bond_depth=1.1).resolved_bond_depth() == 1.0

    def test_clamped_low(self):
        assert make_adapter(bond_depth=-0.1).resolved_bond_depth() == 0.0

    def test_default_is_0_5(self):
        assert make_adapter().resolved_bond_depth() == 0.5


# ── to_synergy_params() ───────────────────────────────────────────────────── #

class TestToSynergyParams:
    def test_all_defaults_on_empty_record(self):
        params = GAIAStateAdapter(MockRecord()).to_synergy_params()
        assert params["dominant_hz"] == 528.0
        assert params["individuation_phase"] == "persona"
        assert params["love_arc_stage"] == "awakening"
        assert params["coherence_score"] == 0.5
        assert params["emotional_valence"] == 0.0
        assert params["bond_depth"] == 0.5

    def test_full_record_round_trip(self):
        record = MockRecord(
            dominant_hz=639.0,
            jungian_phase="anima",
            love_arc_stage="sovereign",
            schumann_aligned=True,
            hrv_coherence_score=0.91,
            affective_valence=0.66,
            bond_depth=0.77,
        )
        params = GAIAStateAdapter(record).to_synergy_params()
        assert params["dominant_hz"] == 639.0
        assert params["individuation_phase"] == "anima"
        assert params["love_arc_stage"] == "sovereign"
        assert params["schumann_aligned"] is True
        assert params["coherence_score"] == 0.91
        assert params["emotional_valence"] == 0.66
        assert params["bond_depth"] == 0.77

    def test_without_trace_module(self):
        """Adapter works when core.trace is unavailable."""
        with patch("core.state_adapter._TRACE_AVAILABLE", False):
            params = GAIAStateAdapter(MockRecord()).to_synergy_params()
        assert "dominant_hz" in params

    def test_with_trace_module_mocked(self):
        """Adapter emits trace when core.trace IS available."""
        mock_trace_ctx = MagicMock()
        mock_trace_ctx.__enter__ = MagicMock(return_value=MagicMock())
        mock_trace_ctx.__exit__ = MagicMock(return_value=False)
        mock_trace_cls = MagicMock(return_value=mock_trace_ctx)

        with patch("core.state_adapter._TRACE_AVAILABLE", True), \
             patch("core.state_adapter.GAIATrace", mock_trace_cls):
            GAIAStateAdapter(MockRecord(id="test-001")).to_synergy_params()

        mock_trace_cls.assert_called_once()


# ── Repr ─────────────────────────────────────────────────────────────────── #

class TestRepr:
    def test_repr_with_id(self):
        r = repr(make_adapter(id="gaian-xyz"))
        assert "gaian-xyz" in r

    def test_repr_without_id(self):
        r = repr(GAIAStateAdapter(MockRecord()))
        assert "unknown" in r


# ── Async adapter ─────────────────────────────────────────────────────────── #

class TestAsyncGAIAStateAdapter:
    def test_sync_method_still_works(self):
        adapter = AsyncGAIAStateAdapter(MockRecord())
        params = adapter.to_synergy_params()
        assert "dominant_hz" in params

    @pytest.mark.asyncio
    async def test_async_method_returns_params(self):
        with patch("core.state_adapter._TRACE_AVAILABLE", False):
            adapter = AsyncGAIAStateAdapter(MockRecord(dominant_hz=417.0))
            params = await adapter.to_synergy_params_async()
        assert params["dominant_hz"] == 417.0
