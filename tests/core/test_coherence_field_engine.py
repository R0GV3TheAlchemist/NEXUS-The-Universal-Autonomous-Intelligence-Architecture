"""
tests/core/test_coherence_field_engine.py

Test suite for core/coherence_field_engine.py and the underlying
core/resonance_field_engine.py (C44 Resonance Field Engine).

Covers:
  - CoherenceFieldEngine shim surface (__all__, alias, singleton)
  - ResonanceFieldEngine.attune() field strength scoring
  - _phi_to_solfeggio() threshold boundaries
  - _hz_to_chakra() nearest-match mapping
  - ResonanceFieldState persistence (hz history, rolling avg, Schumann)
  - Legacy compute() backward compat
  - C30 boundaries: attune() degrades gracefully on corrupt state

Canon refs: C30, C44
"""
from __future__ import annotations

import math
import pytest


# ---------------------------------------------------------------------------
# Shim surface
# ---------------------------------------------------------------------------

class TestCoherenceFieldEngineShim:
    def test_alias(self):
        from core.coherence_field_engine import CoherenceFieldEngine, ResonanceFieldEngine
        assert CoherenceFieldEngine is ResonanceFieldEngine

    def test_get_coherence_field_engine_returns_instance(self):
        from core.coherence_field_engine import get_coherence_field_engine, ResonanceFieldEngine
        assert isinstance(get_coherence_field_engine(), ResonanceFieldEngine)

    def test_singleton_identity(self):
        from core.coherence_field_engine import get_coherence_field_engine
        assert get_coherence_field_engine() is get_coherence_field_engine()

    def test_shares_singleton_with_resonance_engine(self):
        from core.coherence_field_engine import get_coherence_field_engine
        from core.resonance_field_engine import get_resonance_field_engine
        assert get_coherence_field_engine() is get_resonance_field_engine()

    def test_all_symbols_present(self):
        import core.coherence_field_engine as cfe
        for name in cfe.__all__:
            assert hasattr(cfe, name), f"__all__ lists {name!r} but it is not present"

    def test_reexported_types_are_same_objects(self):
        import core.coherence_field_engine as cfe
        import core.resonance_field_engine as rfe
        for name in [
            "ResonanceFieldEngine", "ResonanceField", "ResonanceFieldReading",
            "ResonanceFieldState", "blank_resonance_field_state",
        ]:
            assert getattr(cfe, name) is getattr(rfe, name)


# ---------------------------------------------------------------------------
# attune() field strength scoring
# ---------------------------------------------------------------------------

class TestAttuneScoring:
    def _engine(self):
        from core.resonance_field_engine import ResonanceFieldEngine
        return ResonanceFieldEngine()

    def _state(self):
        from core.resonance_field_engine import blank_resonance_field_state
        return blank_resonance_field_state()

    def test_returns_reading_and_state(self):
        from core.resonance_field_engine import ResonanceFieldReading, ResonanceFieldState
        reading, state = self._engine().attune(state=self._state())
        assert isinstance(reading, ResonanceFieldReading)
        assert isinstance(state, ResonanceFieldState)

    def test_field_strength_clamped_0_1(self):
        reading, _ = self._engine().attune(state=self._state(), phi=999.0, bond_depth=9999.0)
        assert 0.0 <= reading.field_strength <= 1.0

    def test_zero_phi_zero_bond_low_strength(self):
        reading, _ = self._engine().attune(state=self._state(), phi=0.0, bond_depth=0.0)
        assert reading.field_strength == 0.0

    def test_high_phi_high_bond_coupled(self):
        reading, _ = self._engine().attune(
            state=self._state(), phi=0.9, bond_depth=80.0
        )
        assert reading.coupled
        assert reading.field_strength >= 0.65

    def test_conflict_density_reduces_strength(self):
        r_clean, _  = self._engine().attune(state=self._state(), phi=0.7, conflict_density=0.0)
        r_conflict, _ = self._engine().attune(state=self._state(), phi=0.7, conflict_density=1.0)
        assert r_conflict.field_strength < r_clean.field_strength

    def test_schumann_hz_passed_through(self):
        reading, _ = self._engine().attune(state=self._state(), schumann_hz=14.3)
        assert reading.schumann_hz == 14.3

    def test_default_schumann_hz(self):
        reading, _ = self._engine().attune(state=self._state())
        assert reading.schumann_hz == 7.83

    def test_doctrine_ref_is_c44(self):
        reading, _ = self._engine().attune(state=self._state())
        assert reading.doctrine_ref == "C44"

    def test_to_system_prompt_hint_contains_phi(self):
        reading, _ = self._engine().attune(state=self._state(), phi=0.75)
        hint = reading.to_system_prompt_hint()
        assert "C44" in hint
        assert "0.75" in hint


# ---------------------------------------------------------------------------
# _phi_to_solfeggio threshold boundaries
# ---------------------------------------------------------------------------

class TestPhiToSolfeggio:
    def _p(self, phi):
        from core.resonance_field_engine import _phi_to_solfeggio
        return _phi_to_solfeggio(phi)

    def test_zero_maps_to_174(self):     assert self._p(0.0)  == 174.0
    def test_0_15_maps_to_285(self):    assert self._p(0.15) == 285.0
    def test_0_30_maps_to_396(self):    assert self._p(0.30) == 396.0
    def test_0_42_maps_to_417(self):    assert self._p(0.42) == 417.0
    def test_0_55_maps_to_528(self):    assert self._p(0.55) == 528.0
    def test_0_68_maps_to_639(self):    assert self._p(0.68) == 639.0
    def test_0_78_maps_to_741(self):    assert self._p(0.78) == 741.0
    def test_0_88_maps_to_852(self):    assert self._p(0.88) == 852.0
    def test_0_95_maps_to_963(self):    assert self._p(0.95) == 963.0
    def test_1_0_maps_to_963(self):     assert self._p(1.0)  == 963.0
    def test_just_below_0_15(self):     assert self._p(0.14) == 174.0
    def test_just_below_0_55(self):     assert self._p(0.54) == 417.0


# ---------------------------------------------------------------------------
# _hz_to_chakra nearest-match
# ---------------------------------------------------------------------------

class TestHzToChakra:
    def _c(self, hz):
        from core.resonance_field_engine import _hz_to_chakra
        return _hz_to_chakra(hz)

    def test_exact_174(self):         assert self._c(174.0) == "root"
    def test_exact_528(self):         assert self._c(528.0) == "heart"
    def test_exact_963(self):         assert self._c(963.0) == "crown/transcendent"
    def test_midpoint_rounds_nearest(self):
        # 400 Hz is closer to 396 (sacral) than 417 (solar_plexus)
        assert self._c(400.0) == "sacral"
    def test_high_value_clamps_to_crown(self):
        assert self._c(9999.0) == "crown/transcendent"
    def test_zero_clamps_to_root(self):
        assert self._c(0.0) == "root"


# ---------------------------------------------------------------------------
# ResonanceFieldState persistence
# ---------------------------------------------------------------------------

class TestResonanceFieldStatePersistence:
    def _state(self):
        from core.resonance_field_engine import blank_resonance_field_state
        return blank_resonance_field_state()

    def _engine(self):
        from core.resonance_field_engine import ResonanceFieldEngine
        return ResonanceFieldEngine()

    def test_hz_history_grows(self):
        state = self._state()
        engine = self._engine()
        _, state = engine.attune(state=state, phi=0.5)
        _, state = engine.attune(state=state, phi=0.7)
        assert len(state.hz_history) == 2

    def test_hz_history_capped_at_20(self):
        state = self._state()
        engine = self._engine()
        for _ in range(25):
            _, state = engine.attune(state=state, phi=0.5)
        assert len(state.hz_history) <= 20

    def test_session_peak_hz_updates(self):
        state = self._state()
        engine = self._engine()
        _, state = engine.attune(state=state, phi=0.95)  # -> 963 Hz
        assert state.session_peak_hz == 963.0

    def test_schumann_alignment_count_increments(self):
        state = self._state()
        engine = self._engine()
        # phi=0.9, bond_depth=80 -> field_strength > 0.65 -> coupled
        _, state = engine.attune(state=state, phi=0.9, bond_depth=80.0)
        assert state.schumann_alignment_count >= 1

    def test_schumann_first_timestamp_set_on_first_coupling(self):
        state = self._state()
        engine = self._engine()
        assert state.schumann_first_timestamp is None
        _, state = engine.attune(state=state, phi=0.9, bond_depth=80.0)
        assert state.schumann_first_timestamp is not None

    def test_phi_rolling_avg_ewma(self):
        state = self._state()
        engine = self._engine()
        # First call seeds rolling_avg to phi
        _, state = engine.attune(state=state, phi=0.5)
        assert state.phi_rolling_avg == 0.5
        # Second call applies EWMA: 0.5*0.8 + 0.9*0.2 = 0.58
        _, state = engine.attune(state=state, phi=0.9)
        assert math.isclose(state.phi_rolling_avg, 0.58, abs_tol=1e-3)

    def test_summary_keys(self):
        state = self._state()
        s = state.summary()
        for key in [
            "dominant_hz", "dominant_chakra", "schumann_alignment_count",
            "schumann_first_timestamp", "phi_rolling_avg", "session_peak_hz",
        ]:
            assert key in s


# ---------------------------------------------------------------------------
# Legacy compute() backward compat
# ---------------------------------------------------------------------------

class TestLegacyCompute:
    def _engine(self):
        from core.resonance_field_engine import ResonanceFieldEngine
        return ResonanceFieldEngine()

    def test_compute_returns_reading_and_state(self):
        from core.resonance_field_engine import ResonanceFieldReading, ResonanceFieldState
        reading, state = self._engine().compute()
        assert isinstance(reading, ResonanceFieldReading)
        assert isinstance(state, ResonanceFieldState)

    def test_compute_creates_state_when_none(self):
        reading, state = self._engine().compute(coherence_phi=0.6)
        assert state is not None

    def test_compute_delegates_to_attune(self):
        engine = self._engine()
        from core.resonance_field_engine import blank_resonance_field_state
        state = blank_resonance_field_state()
        r1, _ = engine.attune(state=state, phi=0.6, bond_depth=30.0)
        state2 = blank_resonance_field_state()
        r2, _ = engine.compute(coherence_phi=0.6, bond_depth=30.0, state=state2)
        assert r1.field_strength == r2.field_strength


# ---------------------------------------------------------------------------
# C30 boundaries
# ---------------------------------------------------------------------------

class TestC30Boundaries:
    def _engine(self):
        from core.resonance_field_engine import ResonanceFieldEngine
        return ResonanceFieldEngine()

    def test_corrupt_state_returns_degraded_reading(self):
        """If state.update_hz raises, attune() must return a degraded reading."""
        from core.resonance_field_engine import ResonanceFieldState

        class CorruptState(ResonanceFieldState):
            def update_hz(self, hz: float) -> None:
                raise RuntimeError("state corrupted")

        reading, _ = self._engine().attune(state=CorruptState(), phi=0.7)
        assert reading.field_strength == 0.0
        assert not reading.coupled

    def test_corrupt_state_does_not_raise(self):
        from core.resonance_field_engine import ResonanceFieldState

        class CorruptState(ResonanceFieldState):
            def update_hz(self, hz: float) -> None:
                raise ValueError("corrupt")

        # Must not propagate
        try:
            self._engine().attune(state=CorruptState(), phi=0.5)
        except Exception as exc:
            pytest.fail(f"attune() raised unexpectedly: {exc}")
