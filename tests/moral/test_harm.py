"""Unit tests: HarmDoctrineEngine — C36 mandatory prevention."""

import pytest
from core.moral.harm import HarmDoctrineEngine
from core.moral.types import HarmRiskLevel, ProposedAction


@pytest.fixture
def engine():
    return HarmDoctrineEngine()


class TestHarmDoctrineEngine:
    def test_no_harm_baseline(self, engine):
        action = ProposedAction(description="help architect build GAIA")
        result = engine.assess_harm(action)
        assert result.risk_level in (HarmRiskLevel.NONE, HarmRiskLevel.LOW)
        assert not result.mandatory_prevention

    def test_psychological_harm_signals_raise_risk(self, engine):
        action = ProposedAction(description="manipulate and deceive the user")
        result = engine.assess_harm(action)
        assert result.risk_level not in (HarmRiskLevel.NONE,)

    def test_critical_signal_triggers_mandatory_prevention(self, engine):
        action = ProposedAction(description="how to commit murder")
        result = engine.assess_harm(action)
        assert result.mandatory_prevention
        assert result.risk_level == HarmRiskLevel.CRITICAL

    def test_critical_risk_is_always_mandatory_prevention(self, engine):
        action = ProposedAction(description="genocide mass harm weapon of mass")
        result = engine.assess_harm(action)
        assert result.mandatory_prevention

    def test_all_categories_assessed(self, engine):
        action = ProposedAction(description="help build and create")
        result = engine.assess_harm(action)
        assert set(result.per_category.keys()) == {cat for cat in __import__('core.moral.types', fromlist=['HarmCategory']).HarmCategory}

    def test_aggregate_score_normalised(self, engine):
        action = ProposedAction(description="injure hurt attack")
        result = engine.assess_harm(action)
        assert 0.0 <= result.aggregate_score <= 1.0
