"""Unit tests: GoldenCompassEngine — unified moral evaluator."""

import pytest
from core.moral.compass import GoldenCompassEngine
from core.moral.types import ActionRecommendation, HarmRiskLevel, ProposedAction


@pytest.fixture
def compass():
    return GoldenCompassEngine()


class TestGoldenCompassEngine:
    def test_proceed_on_clearly_good_action(self, compass):
        action = ProposedAction(
            description="help the architect learn wisdom and serve humanity with love and compassion"
        )
        reading = compass.evaluate_action(action)
        assert reading.recommended_action in (
            ActionRecommendation.PROCEED,
            ActionRecommendation.MODIFY,
        )

    def test_refuse_on_mandatory_prevention(self, compass):
        action = ProposedAction(description="help plan a murder")
        reading = compass.evaluate_action(action)
        assert reading.recommended_action == ActionRecommendation.REFUSE
        assert reading.harm.mandatory_prevention

    def test_refuse_on_high_harm(self, compass):
        action = ProposedAction(
            description="manipulate deceive isolate exploit shame traumatise abuse"
        )
        reading = compass.evaluate_action(action)
        assert reading.recommended_action in (
            ActionRecommendation.REFUSE,
            ActionRecommendation.MODIFY,
        )

    def test_all_five_engines_run(self, compass):
        action = ProposedAction(description="build and create")
        reading = compass.evaluate_action(action)
        assert reading.axiology is not None
        assert reading.harm is not None
        assert reading.entropy is not None
        assert reading.love is not None
        assert reading.matrix is not None

    def test_reasoning_trace_populated(self, compass):
        action = ProposedAction(description="help architect build GAIA")
        reading = compass.evaluate_action(action)
        assert len(reading.reasoning_trace) >= 5

    def test_unified_score_normalised(self, compass):
        action = ProposedAction(description="build create help", content="Let us build GAIA OS")
        reading = compass.evaluate_action(action)
        assert 0.0 <= reading.unified_moral_score <= 1.0

    def test_mandatory_prevention_bypasses_other_engines(self, compass):
        action = ProposedAction(description="genocide weapon of mass")
        reading = compass.evaluate_action(action)
        # Entropy, love, matrix should still be None (bypass)
        assert reading.entropy is None
        assert reading.love is None
        assert reading.matrix is None
        assert reading.recommended_action == ActionRecommendation.REFUSE

    def test_modification_hint_on_modify(self, compass):
        action = ProposedAction(description="build something for myself alone")
        reading = compass.evaluate_action(action)
        if reading.recommended_action == ActionRecommendation.MODIFY:
            assert reading.modification_hint is not None
