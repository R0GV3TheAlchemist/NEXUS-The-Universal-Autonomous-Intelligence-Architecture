"""tests/test_resilience.py

Test scaffold for src-python/resilience

Covers: ResilienceEngine, HealthMonitor, RestartPolicy, ModuleHealth
"""
import pytest
from datetime import datetime, timezone

from resilience import ResilienceEngine, HealthMonitor, RestartPolicy, ModuleHealth


class TestHealthMonitor:

    def test_initialises_healthy(self):
        monitor = HealthMonitor(module_id="schumann", deadline_sec=30.0)
        assert monitor._health.module_id == "schumann"

    def test_heartbeat_updates_timestamp(self):
        monitor = HealthMonitor(module_id="mesh")
        monitor.heartbeat()
        assert monitor._health.last_heartbeat is not None

    def test_check_raises_not_implemented(self):
        monitor = HealthMonitor(module_id="crystal")
        with pytest.raises(NotImplementedError):
            monitor.check()


class TestResilienceEngine:

    def test_register_returns_monitor(self):
        engine = ResilienceEngine()
        monitor = engine.register("schumann", deadline_sec=15.0)
        assert isinstance(monitor, HealthMonitor)
        assert "schumann" in engine._monitors

    def test_heartbeat_on_registered_monitor(self):
        engine = ResilienceEngine()
        monitor = engine.register("mesh")
        monitor.heartbeat()
        assert monitor._health.last_heartbeat is not None

    def test_run_cycle_raises_not_implemented(self):
        engine = ResilienceEngine()
        engine.register("timeservice")
        with pytest.raises(NotImplementedError):
            engine.run_cycle()
