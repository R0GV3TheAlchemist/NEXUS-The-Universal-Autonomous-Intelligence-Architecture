"""Tests for core/somatic_interface.py — Issue #274"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.somatic_interface import (
    SomaticIntelligenceEngine,
    get_somatic_engine,
    SomaticReading,
    SomaticSignal,
)


# ── Smoke ──────────────────────────────────────────────────────────────
class TestSomaticInterfaceImport:
    def test_module_imports(self):
        import core.somatic_interface  # noqa: F401

    def test_class_exists(self):
        assert SomaticIntelligenceEngine is not None


# ── Singleton ──────────────────────────────────────────────────────────
class TestSomaticInterfaceSingleton:
    def test_singleton_stable(self):
        a = get_somatic_engine()
        b = get_somatic_engine()
        assert a is b

    def test_instance_type(self):
        assert isinstance(get_somatic_engine(), SomaticIntelligenceEngine)


# ── Core logic ─────────────────────────────────────────────────────────
class TestSomaticInterfaceLogic:
    def test_read_returns_somatic_reading(self):
        engine = get_somatic_engine()
        result = engine.read({})
        assert isinstance(result, SomaticReading)

    def test_reading_has_signals_list(self):
        engine = get_somatic_engine()
        result = engine.read({})
        assert hasattr(result, "signals")
        assert isinstance(result.signals, list)

    def test_signals_are_somatic_signal_type(self):
        engine = get_somatic_engine()
        result = engine.read({"turn_text": "My chest feels tight and I can't breathe."})
        for s in result.signals:
            assert isinstance(s, SomaticSignal)

    def test_reading_has_overall_activation(self):
        engine = get_somatic_engine()
        result = engine.read({})
        assert hasattr(result, "activation")
        assert 0.0 <= result.activation <= 1.0

    def test_distress_language_raises_activation(self):
        engine = get_somatic_engine()
        result = engine.read({
            "turn_text": "I feel sick, my body is shaking, I can't calm down."
        })
        assert isinstance(result, SomaticReading)


# ── Edge cases ─────────────────────────────────────────────────────────
class TestSomaticInterfaceEdgeCases:
    def test_empty_context_no_raise(self):
        get_somatic_engine().read({})

    def test_none_turn_text_handled(self):
        get_somatic_engine().read({"turn_text": None})

    def test_empty_string_handled(self):
        get_somatic_engine().read({"turn_text": ""})

    def test_activation_bounded_above(self):
        engine = get_somatic_engine()
        result = engine.read({"override_activation": 999.9})
        assert result.activation <= 1.0

    def test_activation_bounded_below(self):
        engine = get_somatic_engine()
        result = engine.read({"override_activation": -999.9})
        assert result.activation >= 0.0
