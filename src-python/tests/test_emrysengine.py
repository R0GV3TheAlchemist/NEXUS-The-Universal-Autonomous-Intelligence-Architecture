"""tests/test_emrysengine.py

Test scaffold for src-python/emrysengine

Covers: EmrysEngine, EmrysConfig, HealthSignal, HealthSeverity,
        init_emrys_engine
"""
import pytest

from emrysengine import EmrysEngine, EmrysConfig, HealthSignal, HealthSeverity, init_emrys_engine


class TestHealthSignal:

    def test_health_signal_constructs(self):
        sig = HealthSignal(
            source="schumann",
            message="7.83 Hz not confirmed",
            severity=HealthSeverity.WARN,
        )
        assert sig.source == "schumann"
        assert sig.severity == HealthSeverity.WARN


class TestEmrysEngine:

    def test_init_via_router(self):
        engine = init_emrys_engine()
        assert engine is not None
        assert isinstance(engine, EmrysEngine)

    def test_init_with_config(self):
        config = EmrysConfig(critical_sources=["mesh", "crisisengine"], auto_restart=True)
        engine = EmrysEngine(config=config)
        assert engine.config.auto_restart is True

    def test_ingest_signal_raises_not_implemented(self):
        engine = EmrysEngine()
        sig = HealthSignal(source="mesh", message="timeout", severity=HealthSeverity.CRITICAL)
        with pytest.raises(NotImplementedError):
            engine.ingest_signal(sig)

    def test_evaluate_system_state_raises_not_implemented(self):
        engine = EmrysEngine()
        with pytest.raises(NotImplementedError):
            engine.evaluate_system_state()

    def test_plan_interventions_raises_not_implemented(self):
        engine = EmrysEngine()
        with pytest.raises(NotImplementedError):
            engine.plan_interventions()
