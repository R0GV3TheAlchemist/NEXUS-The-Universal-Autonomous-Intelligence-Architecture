"""tests/test_schumann.py

Test scaffold for src-python/schumann

Covers: SchumannEngine, EarthFieldMonitor, SyncPulse
"""
import pytest

schumann = pytest.importorskip("schumann")


class TestSyncPulse:

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_sync_pulse_confirmed(self):
        from schumann.engine import SyncPulse
        pulse = SyncPulse(frequency=7.83, confidence=0.95, confirmed=True)
        assert pulse.confirmed is True
        assert pulse.frequency == pytest.approx(7.83)

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_sync_pulse_unconfirmed_logs_to_sovereign_memory(self):
        """Unconfirmed SyncPulse must be logged to sovereign memory per spec."""
        from schumann.engine import SyncPulse
        pulse = SyncPulse(frequency=0.0, confidence=0.0, confirmed=False)
        assert pulse.confirmed is False


class TestSchumannEngine:

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_engine_initialises(self):
        from schumann import init_schumann_engine
        engine = init_schumann_engine()
        assert engine is not None

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_acquire_returns_sync_pulse(self):
        from schumann.engine import SchumannEngine
        import numpy as np
        engine = SchumannEngine()
        # Feed synthetic noise — should return a SyncPulse regardless
        raw = np.zeros(1024)
        pulse = engine.acquire(raw)
        assert pulse is not None
