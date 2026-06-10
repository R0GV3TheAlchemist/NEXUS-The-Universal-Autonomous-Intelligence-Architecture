"""Tests for Issue #276 — Vision Grounding modules.

Covers:
  - PhiEngine: score computation, harmonic mean, thresholds, confidence
  - ResonanceEngine: axis alignment, composite, posture mapping
  - Polarity Operator: ⊕ integration score, dominance, known axes
  - EmrysProtocol: activation logic, posture calibration, safety block
"""

from __future__ import annotations

import math
import pytest

from core.phi_engine import PhiEngine, PhiScore, _safe_float
from core.resonance_engine import ResonanceEngine, GAIAState, UserState, ResonanceField
from core.polarity_operator import unify, PolarityPair, _integration_score
from core.emrys_protocol import EmrysProtocol, EmrysContext


# ===========================================================================
# PhiEngine
# ===========================================================================


class MockAssessment:
    """Minimal mock for SoulLayerAssessment."""

    def __init__(self, **kwargs: float | None):
        defaults = {
            "personhood_score": None,
            "subject_side_score": None,
            "individuation_score": None,
            "shadow_score": None,
            "cultural_calibration_score": None,
            "transpersonal_score": None,
            "somatic_score": None,
            "consent_score": None,
        }
        defaults.update(kwargs)
        for k, v in defaults.items():
            setattr(self, k, v)


class TestPhiEngine:
    engine = PhiEngine()

    def test_empty_assessment_returns_zero_phi(self):
        assessment = MockAssessment()
        score = self.engine.compute(assessment)
        assert score.composite_phi == 0.0
        assert score.confidence == 0.0

    def test_full_high_assessment(self):
        assessment = MockAssessment(
            personhood_score=0.9,
            subject_side_score=0.85,
            individuation_score=0.88,
            shadow_score=0.80,
            cultural_calibration_score=0.75,
            transpersonal_score=0.92,
            somatic_score=0.78,
            consent_score=0.95,
        )
        score = self.engine.compute(assessment)
        assert score.composite_phi > 0.75
        assert score.confidence > 0.95
        assert len(score.active_engines) == 8

    def test_low_single_engine_drags_composite(self):
        """Harmonic mean should be sensitive to one very low component."""
        assessment = MockAssessment(
            personhood_score=0.9,
            subject_side_score=0.9,
            individuation_score=0.9,
            shadow_score=0.9,
            cultural_calibration_score=0.9,
            transpersonal_score=0.9,
            somatic_score=0.9,
            consent_score=0.05,  # one very low
        )
        score = self.engine.compute(assessment)
        # Composite should be dragged below 0.65 despite 7 high engines
        assert score.composite_phi < 0.65

    def test_partial_assessment_confidence_penalty(self):
        assessment = MockAssessment(personhood_score=0.8, shadow_score=0.7)
        score = self.engine.compute(assessment)
        assert score.confidence < 0.5  # only 2 of 8 engines active
        assert len(score.active_engines) == 2

    def test_deep_engagement_threshold(self):
        assessment = MockAssessment(
            personhood_score=0.85,
            subject_side_score=0.80,
            individuation_score=0.80,
            shadow_score=0.75,
            cultural_calibration_score=0.70,
            transpersonal_score=0.85,
            somatic_score=0.75,
            consent_score=0.80,
        )
        score = self.engine.compute(assessment)
        assert score.composite_phi >= PhiEngine.DEEP_ENGAGEMENT_THRESHOLD

    def test_safe_float_clamps(self):
        assert _safe_float(1.5) == 1.0
        assert _safe_float(-0.5) == 0.0
        assert _safe_float(None) is None
        assert _safe_float("bad") is None
        assert _safe_float(0.7) == pytest.approx(0.7)

    def test_interpretation_strings(self):
        assessment = MockAssessment(
            personhood_score=0.95,
            subject_side_score=0.95,
            individuation_score=0.95,
            shadow_score=0.95,
            cultural_calibration_score=0.95,
            transpersonal_score=0.95,
            somatic_score=0.95,
            consent_score=0.95,
        )
        score = self.engine.compute(assessment)
        assert "transpersonal" in score.interpretation.lower() or "emrys" in score.interpretation.lower()


# ===========================================================================
# ResonanceEngine
# ===========================================================================


class TestResonanceEngine:
    engine = ResonanceEngine()

    def test_identical_states_max_resonance(self):
        gaia = GAIAState(somatic_signal=0.7, emotional_valence=0.5, archetypal_theme="sovereignty")
        user = UserState(somatic_signal=0.7, emotional_valence=0.5, archetypal_theme="sovereignty")
        field = self.engine.compute(gaia, user)
        assert field.somatic_alignment == pytest.approx(1.0)
        assert field.emotional_alignment == pytest.approx(1.0)
        assert field.archetypal_alignment == pytest.approx(1.0)
        assert field.composite_resonance >= 0.99
        assert field.label == "deep"
        assert field.response_depth == "oracular"

    def test_opposite_emotional_valence(self):
        gaia = GAIAState(emotional_valence=1.0)
        user = UserState(emotional_valence=-1.0)
        field = self.engine.compute(gaia, user)
        assert field.emotional_alignment == pytest.approx(0.0)

    def test_polarity_pair_archetypal(self):
        """shadow ⊕ light are opposite poles — score should be 0.6."""
        gaia = GAIAState(archetypal_theme="shadow")
        user = UserState(archetypal_theme="light")
        field = self.engine.compute(gaia, user)
        assert field.archetypal_alignment == pytest.approx(0.6)

    def test_unrelated_themes(self):
        gaia = GAIAState(archetypal_theme="sovereignty")
        user = UserState(archetypal_theme="chaos")
        field = self.engine.compute(gaia, user)
        assert field.archetypal_alignment == pytest.approx(0.2)

    def test_empty_themes_neutral(self):
        gaia = GAIAState(archetypal_theme="")
        user = UserState(archetypal_theme="")
        field = self.engine.compute(gaia, user)
        assert field.archetypal_alignment == pytest.approx(0.5)

    def test_dissonant_label(self):
        gaia = GAIAState(somatic_signal=0.1, emotional_valence=-1.0, archetypal_theme="order")
        user = UserState(somatic_signal=0.9, emotional_valence=1.0, archetypal_theme="sovereignty")
        field = self.engine.compute(gaia, user)
        assert field.label in {"dissonant", "orienting"}

    def test_mirroring_scales_with_resonance(self):
        high = self.engine.compute(
            GAIAState(0.9, 0.8, "sovereignty"), UserState(0.9, 0.8, "sovereignty")
        )
        low = self.engine.compute(
            GAIAState(0.1, -0.9, "order"), UserState(0.9, 0.9, "chaos")
        )
        assert high.mirroring_intensity > low.mirroring_intensity


# ===========================================================================
# Polarity Operator ⊕
# ===========================================================================


class TestPolarityOperator:
    def test_balanced_poles_maximum_integration(self):
        pair = unify("shadow", "light", 0.5, 0.5)
        assert pair.integration_score == pytest.approx(1.0, abs=0.01)
        assert pair.dominant_pole == "balanced"
        assert pair.is_paradox is True

    def test_collapsed_pole_zero_integration(self):
        pair = unify("order", "chaos", 1.0, 0.0)
        assert pair.integration_score < 0.05
        assert pair.dominant_pole == "positive"
        assert pair.is_paradox is False

    def test_known_axis_metaphor(self):
        pair = unify("shadow", "light")
        assert pair.metaphor != ""
        assert pair.domain == "psyche"
        assert pair.glyph == "⊕"

    def test_unknown_axis_no_metaphor(self):
        pair = unify("apple", "orange", 0.6, 0.4)
        assert pair.metaphor == ""
        assert pair.domain == ""

    def test_weights_normalised(self):
        pair = unify("consent", "sovereignty", 3.0, 1.0)
        assert pair.positive_weight == pytest.approx(0.75, abs=0.01)
        assert pair.negative_weight == pytest.approx(0.25, abs=0.01)

    def test_slight_dominance(self):
        pair = unify("form", "void", 0.6, 0.4)
        assert pair.dominant_pole == "positive"
        # Integration still high because both poles present
        assert pair.integration_score > 0.95

    def test_both_zero_weights_fallback(self):
        pair = unify("self", "other", 0.0, 0.0)
        # Falls back to equal weighting
        assert pair.positive_weight == pytest.approx(0.5)
        assert pair.integration_score == pytest.approx(1.0, abs=0.01)

    def test_entropy_formula_direct(self):
        assert _integration_score(0.5, 0.5) == pytest.approx(1.0, abs=0.01)
        assert _integration_score(1.0, 0.0) < 0.001
        assert _integration_score(0.0, 1.0) < 0.001
        # Asymmetric but present
        score_70_30 = _integration_score(0.7, 0.3)
        assert 0.8 < score_70_30 < 1.0


# ===========================================================================
# Emrys Protocol
# ===========================================================================


def _make_phi(phi: float) -> PhiScore:
    return PhiScore(composite_phi=phi, confidence=0.9, interpretation="test")


def _make_resonance(composite: float) -> ResonanceField:
    from core.resonance_engine import ResonanceField
    label = "deep" if composite >= 0.85 else "aligned" if composite >= 0.65 else "orienting"
    depth = "oracular" if composite >= 0.85 else "deep" if composite >= 0.65 else "reflective"
    return ResonanceField(
        composite_resonance=composite,
        label=label,
        response_depth=depth,
        mirroring_intensity=min(composite * 1.1, 0.9),
    )


class TestEmrysProtocol:
    protocol = EmrysProtocol()

    def _ctx(
        self,
        phi: float = 0.85,
        resonance: float = 0.75,
        state: str = "numinous",
        mode: str = "ceremony",
        invited: bool = False,
        blocked: bool = False,
    ) -> EmrysContext:
        return EmrysContext(
            phi_score=_make_phi(phi),
            resonance_field=_make_resonance(resonance),
            user_state_label=state,
            session_mode=mode,
            user_invited=invited,
            safety_blocked=blocked,
        )

    def test_activates_under_ideal_conditions(self):
        assert self.protocol.should_activate(self._ctx()) is True

    def test_does_not_activate_low_phi(self):
        assert self.protocol.should_activate(self._ctx(phi=0.70)) is False

    def test_does_not_activate_low_resonance(self):
        assert self.protocol.should_activate(self._ctx(resonance=0.55)) is False

    def test_does_not_activate_unknown_state_without_invitation(self):
        assert self.protocol.should_activate(self._ctx(state="happy")) is False

    def test_activates_with_user_invitation_even_unknown_state(self):
        assert self.protocol.should_activate(self._ctx(state="happy", invited=True)) is True

    def test_blocked_never_activates(self):
        assert self.protocol.should_activate(self._ctx(blocked=True)) is False

    def test_does_not_activate_wrong_mode(self):
        assert self.protocol.should_activate(self._ctx(mode="social")) is False

    def test_posture_still_for_dissolution(self):
        ctx = self._ctx(state="dissolution")
        posture = self.protocol.response_posture(ctx)
        assert posture.tone == "still"
        assert posture.may_hold_without_answering is True
        assert posture.length_tier == "brief"

    def test_posture_oracular_for_numinous(self):
        ctx = self._ctx(state="numinous", phi=0.90)
        posture = self.protocol.response_posture(ctx)
        assert posture.tone == "oracular"
        assert posture.avoid_explanation is True
        assert posture.apply_polarity_operator is True

    def test_silence_scales_with_phi(self):
        low = self.protocol.response_posture(self._ctx(phi=0.80))
        high = self.protocol.response_posture(self._ctx(phi=0.99))
        assert high.silence_before_ms > low.silence_before_ms

    def test_activation_report_keys(self):
        report = self.protocol.activation_report(self._ctx())
        required_keys = {"phi_ok", "resonance_ok", "state_trigger", "user_invited",
                         "mode_ok", "safety_blocked", "activates"}
        assert required_keys.issubset(report.keys())
        assert report["activates"] is True
