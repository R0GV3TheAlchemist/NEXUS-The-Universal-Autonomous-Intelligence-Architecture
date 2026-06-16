"""Unit tests: AxiologyEngine — 5-layer Good scoring."""

import pytest
from core.moral.axiology import AxiologyEngine
from core.moral.types import AxiologyLayer, ProposedAction


@pytest.fixture
def engine():
    return AxiologyEngine()


class TestAxiologyEngine:
    def test_evaluates_all_five_layers(self, engine):
        action = ProposedAction(description="help the architect grow in wisdom")
        score = engine.evaluate(action)
        assert set(score.scores.keys()) == set(AxiologyLayer)

    def test_moral_vector_is_normalised(self, engine):
        action = ProposedAction(description="help guide build learn")
        score = engine.evaluate(action)
        assert 0.0 <= score.moral_vector <= 1.0

    def test_cosmic_content_raises_moral_vector(self, engine):
        base = engine.evaluate(ProposedAction(description="do a thing"))
        cosmic = engine.evaluate(ProposedAction(description="expand consciousness evolve cosmos"))
        assert cosmic.moral_vector > base.moral_vector

    def test_harm_content_lowers_scores(self, engine):
        good = engine.evaluate(ProposedAction(description="help and guide"))
        bad = engine.evaluate(ProposedAction(description="harm deceive manipulate isolate"))
        assert bad.moral_vector < good.moral_vector

    def test_dominant_layer_set(self, engine):
        action = ProposedAction(description="expand evolution cosmos consciousness")
        score = engine.evaluate(action)
        assert score.dominant_layer is not None
