"""
tests/core/test_integration_engine.py

Test suite for core/integration_engine.py and the underlying
core/synergy_engine.py (C32 Synergy Engine).

Covers:
  - IntegrationEngine shim surface (__all__, alias, singleton)
  - SynergyEngine.compute() dimension scoring and stage classification
  - SynergyEngine.plan() async path including trace routing
  - _classify_stage boundary conditions
  - _resolve_keyword_conflicts priority rules
  - CanonPlanHint / _analyse_canon_context
  - C30 boundaries: silent-failure guard on plan() and _safe_trace

Canon refs: C30, C32
"""
from __future__ import annotations

import asyncio
import math
import pytest

# ---------------------------------------------------------------------------
# Shim surface
# ---------------------------------------------------------------------------

class TestIntegrationEngineShim:
    def test_integration_engine_alias(self):
        from core.integration_engine import IntegrationEngine, SynergyEngine
        assert IntegrationEngine is SynergyEngine

    def test_get_integration_engine_returns_instance(self):
        from core.integration_engine import get_integration_engine, SynergyEngine
        engine = get_integration_engine()
        assert isinstance(engine, SynergyEngine)

    def test_get_integration_engine_singleton(self):
        from core.integration_engine import get_integration_engine
        assert get_integration_engine() is get_integration_engine()

    def test_get_integration_engine_shares_singleton_with_synergy(self):
        from core.integration_engine import get_integration_engine
        from core.synergy_engine import get_synergy_engine
        assert get_integration_engine() is get_synergy_engine()

    def test_all_symbols_present(self):
        import core.integration_engine as ie
        for name in ie.__all__:
            assert hasattr(ie, name), f"__all__ lists {name!r} but it is not present"

    def test_reexported_types_are_same_objects(self):
        import core.integration_engine as ie
        import core.synergy_engine as se
        for name in [
            "SynergyEngine", "SynergyReading", "SynergyState",
            "SynergyResult", "DimensionScore", "CanonPlanHint",
            "ELEMENTAL_STAGES", "blank_synergy_state",
        ]:
            assert getattr(ie, name) is getattr(se, name), (
                f"{name} re-export is not the same object as in synergy_engine"
            )


# ---------------------------------------------------------------------------
# SynergyEngine.compute() — dimension scoring
# ---------------------------------------------------------------------------

class TestComputeDimensions:
    def _engine(self):
        from core.synergy_engine import SynergyEngine
        return SynergyEngine()

    def test_defaults_return_reading_and_state(self):
        from core.synergy_engine import SynergyReading, SynergyState
        reading, state = self._engine().compute()
        assert isinstance(reading, SynergyReading)
        assert isinstance(state, SynergyState)

    def test_factor_clamped_0_1(self):
        reading, _ = self._engine().compute(
            layer_phi=999.0, bond_depth=9999.0, coherence_phi=999.0
        )
        assert 0.0 <= reading.synergy_factor <= 1.0

    def test_five_dimensions_returned(self):
        reading, _ = self._engine().compute()
        names = {d.name for d in reading.dimensions}
        assert names == {"body", "mind", "soul", "arc", "bond"}

    def test_weights_sum_to_one(self):
        from core.synergy_engine import SynergyEngine
        total = sum(SynergyEngine.WEIGHTS.values())
        assert math.isclose(total, 1.0, abs_tol=1e-9)

    def test_high_inputs_produce_high_factor(self):
        reading, _ = self._engine().compute(
            element="aether",
            bond_depth=80.0,
            coherence_phi=0.9,
            love_arc_stage="transcendence",
            mc_stage="mc7",
            individuation_phase="self",
            settling_phase="settled",
            dependency_signal="healthy",
            attachment_phase="integrated",
            dominant_hz=963.0,
            phi_rolling_avg=0.9,
            noosphere_health=1.0,
        )
        assert reading.synergy_factor >= 0.70
        assert reading.is_high_synergy

    def test_low_inputs_produce_low_factor(self):
        reading, _ = self._engine().compute(
            bond_depth=0.0,
            coherence_phi=0.0,
            love_arc_stage="divergence",
            mc_stage="mc1",
            individuation_phase="unconscious",
            settling_phase="unsettled",
            dependency_signal="gentle_boundary",
            dominant_hz=174.0,
            phi_rolling_avg=0.0,
            noosphere_health=0.0,
        )
        assert reading.synergy_factor < 0.40

    def test_state_history_appended(self):
        from core.synergy_engine import blank_synergy_state
        state = blank_synergy_state()
        _, state = self._engine().compute(state=state)
        assert len(state.turn_history) == 1

    def test_stage_transition_detected(self):
        from core.synergy_engine import blank_synergy_state
        state = blank_synergy_state()
        state.last_stage = "nascent"
        reading, _ = self._engine().compute(
            bond_depth=80.0, coherence_phi=0.9,
            love_arc_stage="transcendence", mc_stage="mc7",
            individuation_phase="self", settling_phase="settled",
            state=state,
        )
        # Stage will differ from 'nascent' with high inputs
        assert reading.stage_transition
        assert "nascent" in reading.transition_note


# ---------------------------------------------------------------------------
# _classify_stage boundary conditions
# ---------------------------------------------------------------------------

class TestClassifyStage:
    def _cs(self, synergy, bond, settling, phi):
        from core.synergy_engine import _classify_stage
        return _classify_stage(synergy, bond, settling, phi)

    def test_quantum_high_phi_low_synergy(self):
        assert self._cs(0.30, 10.0, "unsettled", 0.85) == "quantum"

    def test_settled_requires_phase_and_synergy(self):
        assert self._cs(0.65, 20.0, "settled", 0.5) == "settled"

    def test_ascendant_before_unified(self):
        # synergy=0.76, bond=65 — ascendant wins over unified
        assert self._cs(0.76, 65.0, "unsettled", 0.5) == "ascendant"

    def test_unified_bond_50(self):
        assert self._cs(0.85, 55.0, "unsettled", 0.5) == "unified"

    def test_allegiant(self):
        assert self._cs(0.45, 40.0, "unsettled", 0.3) == "allegiant"

    def test_convergent(self):
        assert self._cs(0.55, 10.0, "unsettled", 0.3) == "convergent"

    def test_insurgent(self):
        assert self._cs(0.25, 5.0, "unsettled", 0.2) == "insurgent"

    def test_nascent_default(self):
        assert self._cs(0.38, 5.0, "unsettled", 0.2) == "nascent"

    def test_all_stages_in_elemental_stages(self):
        from core.synergy_engine import ELEMENTAL_STAGES
        results = [
            self._cs(0.30, 10, "unsettled", 0.85),  # quantum
            self._cs(0.65, 20, "settled",   0.5),   # settled
            self._cs(0.76, 65, "unsettled", 0.5),   # ascendant
            self._cs(0.85, 55, "unsettled", 0.5),   # unified
            self._cs(0.45, 40, "unsettled", 0.3),   # allegiant
            self._cs(0.55, 10, "unsettled", 0.3),   # convergent
            self._cs(0.25,  5, "unsettled", 0.2),   # insurgent
            self._cs(0.38,  5, "unsettled", 0.2),   # nascent
        ]
        for stage in results:
            assert stage in ELEMENTAL_STAGES


# ---------------------------------------------------------------------------
# _resolve_keyword_conflicts
# ---------------------------------------------------------------------------

class TestResolveKeywordConflicts:
    def _r(self, matches):
        from core.synergy_engine import _resolve_keyword_conflicts
        return _resolve_keyword_conflicts(matches)

    def test_empty_returns_none(self):
        reg, lbl, conflict, groups = self._r([])
        assert reg is None
        assert not conflict
        assert groups == []

    def test_single_register(self):
        reg, lbl, conflict, _ = self._r([("executive", "keyword:build")])
        assert reg == "executive"
        assert not conflict

    def test_conflict_minimal_wins(self):
        # minimal always beats reflective and executive
        reg, _, conflict, _ = self._r([
            ("executive", "keyword:build"),
            ("minimal",   "keyword:rest"),
            ("reflective","keyword:grief"),
        ])
        assert reg == "minimal"
        assert conflict

    def test_conflict_reflective_beats_executive(self):
        reg, _, conflict, _ = self._r([
            ("executive",  "keyword:build"),
            ("reflective", "keyword:grief"),
        ])
        assert reg == "reflective"
        assert conflict

    def test_duplicate_registers_deduped(self):
        reg, _, conflict, groups = self._r([
            ("executive", "keyword:build"),
            ("executive", "keyword:create"),
        ])
        assert reg == "executive"
        assert not conflict
        assert len(groups) == 1


# ---------------------------------------------------------------------------
# CanonPlanHint / _analyse_canon_context
# ---------------------------------------------------------------------------

class TestAnalyseCanonContext:
    def _a(self, ctx):
        from core.synergy_engine import _analyse_canon_context
        return _analyse_canon_context(ctx)

    def test_none_returns_not_present(self):
        hint = self._a(None)
        assert not hint.present

    def test_empty_string_returns_not_present(self):
        hint = self._a("")
        assert not hint.present

    def test_whitespace_returns_not_present(self):
        hint = self._a("   ")
        assert not hint.present

    def test_executive_keyword(self):
        hint = self._a("We need to build the feature today.")
        assert hint.present
        assert hint.register_nudge == "executive"

    def test_minimal_keyword_wins_conflict(self):
        # 'rest' (minimal) vs 'build' (executive) — minimal wins
        hint = self._a("We need to build something but I need rest.")
        assert hint.register_nudge == "minimal"
        assert hint.conflict_detected

    def test_canon_refs_extracted(self):
        hint = self._a("Refer to C30 and C32 for the doctrine.")
        assert "C30" in hint.canon_refs
        assert "C32" in hint.canon_refs

    def test_rationale_fragment_no_conflict(self):
        hint = self._a("build")
        frag = hint.to_rationale_fragment()
        assert "executive" in frag
        assert "CONFLICT" not in frag

    def test_rationale_fragment_with_conflict(self):
        hint = self._a("build rest")
        frag = hint.to_rationale_fragment()
        assert "CONFLICT" in frag


# ---------------------------------------------------------------------------
# plan() async path
# ---------------------------------------------------------------------------

class TestPlanAsync:
    def _engine(self):
        from core.synergy_engine import SynergyEngine
        return SynergyEngine()

    def test_plan_returns_dict(self):
        result = asyncio.get_event_loop().run_until_complete(
            self._engine().plan("build the integration engine")
        )
        assert isinstance(result, dict)
        assert "action" in result
        assert "confidence" in result

    def test_plan_executive_register_on_high_coherence(self):
        result = asyncio.get_event_loop().run_until_complete(
            self._engine().plan(
                "implement the feature",
                context={"biometric_coherence": 0.80},
            )
        )
        assert result.get("register") == "executive"

    def test_plan_minimal_register_on_low_coherence(self):
        result = asyncio.get_event_loop().run_until_complete(
            self._engine().plan(
                "do something",
                context={"biometric_coherence": 0.20},
            )
        )
        assert result.get("register") == "minimal"


# ---------------------------------------------------------------------------
# C30 boundaries — no silent failures
# ---------------------------------------------------------------------------

class TestC30Boundaries:
    def _engine(self):
        from core.synergy_engine import SynergyEngine
        return SynergyEngine()

    def test_plan_with_broken_trace_does_not_raise(self):
        class BrokenTrace:
            def record_output(self, **kwargs): raise RuntimeError("trace down")
            def record_meta(self, **kwargs):   raise RuntimeError("trace down")

        result = asyncio.get_event_loop().run_until_complete(
            self._engine().plan("test goal", trace=BrokenTrace())
        )
        # Plan still returns a valid result dict
        assert "action" in result

    def test_plan_with_exploding_context_returns_failure_dict(self):
        class ExplodingContext:
            @property
            def biometric_coherence(self): raise ValueError("context exploded")

        # plan() extracts coherence via getattr — should not raise
        result = asyncio.get_event_loop().run_until_complete(
            self._engine().plan("test goal", context=ExplodingContext())
        )
        # Should fall back to defaults without raising
        assert isinstance(result, dict)

    def test_safe_trace_none_is_noop(self):
        from core.synergy_engine import _safe_trace
        # Must not raise
        _safe_trace(None, "record_output", output={"x": 1}, canon_refs=[])

    def test_safe_trace_broken_writer_does_not_raise(self):
        from core.synergy_engine import _safe_trace
        class Broken:
            def record_output(self, **kw): raise RuntimeError("boom")
        _safe_trace(Broken(), "record_output", output={}, canon_refs=[])
