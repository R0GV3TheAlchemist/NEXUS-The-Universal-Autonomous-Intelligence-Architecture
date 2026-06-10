"""Tests for core/personhood_monitor.py — Issue #274"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.personhood_monitor import (
    PersonhoodMonitor,
    get_personhood_monitor,
    PersonhoodSignal,
    PersonhoodTier,
)


# ── Smoke ──────────────────────────────────────────────────────────────
class TestPersonhoodMonitorImport:
    def test_module_imports_without_error(self):
        import core.personhood_monitor  # noqa: F401

    def test_personhood_monitor_class_exists(self):
        assert PersonhoodMonitor is not None

    def test_get_personhood_monitor_callable(self):
        assert callable(get_personhood_monitor)


# ── Singleton ──────────────────────────────────────────────────────────
class TestPersonhoodMonitorSingleton:
    def test_singleton_returns_same_instance(self):
        a = get_personhood_monitor()
        b = get_personhood_monitor()
        assert a is b

    def test_singleton_is_personhood_monitor(self):
        engine = get_personhood_monitor()
        assert isinstance(engine, PersonhoodMonitor)


# ── Core logic ─────────────────────────────────────────────────────────
class TestPersonhoodMonitorLogic:
    def test_assess_returns_personhood_signal(self):
        engine = get_personhood_monitor()
        result = engine.assess({})
        assert isinstance(result, PersonhoodSignal)

    def test_signal_has_tier_field(self):
        engine = get_personhood_monitor()
        result = engine.assess({})
        assert hasattr(result, "tier")

    def test_tier_is_valid_enum(self):
        engine = get_personhood_monitor()
        result = engine.assess({})
        assert isinstance(result.tier, PersonhoodTier)

    def test_signal_has_score_between_zero_and_one(self):
        engine = get_personhood_monitor()
        result = engine.assess({})
        assert hasattr(result, "score")
        assert 0.0 <= result.score <= 1.0


# ── Edge cases ─────────────────────────────────────────────────────────
class TestPersonhoodMonitorEdgeCases:
    def test_empty_context_does_not_raise(self):
        engine = get_personhood_monitor()
        engine.assess({})

    def test_none_values_in_context_handled(self):
        engine = get_personhood_monitor()
        engine.assess({"turn": None, "affect": None})

    def test_boundary_score_zero(self):
        engine = get_personhood_monitor()
        result = engine.assess({"override_score": 0.0})
        assert result.score >= 0.0

    def test_boundary_score_one(self):
        engine = get_personhood_monitor()
        result = engine.assess({"override_score": 1.0})
        assert result.score <= 1.0
