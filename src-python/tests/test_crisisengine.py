"""tests/test_crisisengine.py

Test scaffold for src-python/crisisengine

Covers: CrisisEngine, EngineConfig
"""
import pytest

crisisengine = pytest.importorskip("crisisengine")


class TestCrisisEngine:

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_crisis_engine_initialises(self):
        from crisisengine.engine import CrisisEngine, EngineConfig
        config = EngineConfig()
        engine = CrisisEngine(config=config)
        assert engine is not None

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_trigger_crisis_emits_event(self):
        from crisisengine.engine import CrisisEngine, EngineConfig
        engine = CrisisEngine(config=EngineConfig())
        event = engine.trigger(reason="CRITICAL signal from mesh", source="mesh")
        assert event is not None

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_crisis_respects_gaian_law_vi(self):
        """CrisisEngine must not override sovereign will — Law VI."""
        from crisisengine.engine import CrisisEngine, EngineConfig
        engine = CrisisEngine(config=EngineConfig())
        # override_sovereign must raise or return False
        result = engine.may_override_sovereign()
        assert result is False
