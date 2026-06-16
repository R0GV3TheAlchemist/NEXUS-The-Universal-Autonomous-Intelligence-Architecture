"""Unit tests: LoveDoctrineEngine — 7 love modes and Agape Quotient."""

import pytest
from core.moral.love import LoveDoctrineEngine
from core.moral.types import LoveMode, ProposedAction


@pytest.fixture
def engine():
    return LoveDoctrineEngine()


class TestLoveDoctrineEngine:
    def test_agape_quotient_range(self, engine):
        action = ProposedAction(description="serve all with compassion and love")
        result = engine.assess_love(action)
        assert 0.0 <= result.agape_quotient <= 1.0

    def test_agape_signals_raise_quotient(self, engine):
        base = engine.assess_love(ProposedAction(description="do a thing"))
        agape = engine.assess_love(ProposedAction(description="unconditional love serve humanity compassion grace"))
        assert agape.agape_quotient >= base.agape_quotient

    def test_eros_mode_detected(self, engine):
        action = ProposedAction(description="create vision fire passion inspire generate")
        result = engine.assess_love(action)
        assert result.active_mode == LoveMode.EROS

    def test_philautia_mode_detected(self, engine):
        action = ProposedAction(description="self boundary health rest center mine")
        result = engine.assess_love(action)
        assert result.active_mode == LoveMode.PHILAUTIA

    def test_default_agape_when_no_signal(self, engine):
        action = ProposedAction(description="xyz123 no signals here")
        result = engine.assess_love(action)
        assert result.active_mode == LoveMode.AGAPE

    def test_lci_in_range(self, engine):
        action = ProposedAction(description="build together share")
        result = engine.assess_love(action)
        assert 0.0 <= result.love_coherence_index <= 1.0

    def test_mode_scores_all_seven(self, engine):
        action = ProposedAction(description="build")
        result = engine.assess_love(action)
        assert len(result.mode_scores) == 7
