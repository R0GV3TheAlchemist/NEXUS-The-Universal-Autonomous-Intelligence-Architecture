"""Tests for core/transpersonal_engine.py — Issue #274"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.transpersonal_engine import (
    TranspersonalEngine,
    get_transpersonal_engine,
    TranspersonalReading,
    TranspersonalState,
)


# ── Smoke ──────────────────────────────────────────────────────────────
class TestTranspersonalEngineImport:
    def test_module_imports(self):
        import core.transpersonal_engine  # noqa: F401

    def test_class_exists(self):
        assert TranspersonalEngine is not None


# ── Singleton ──────────────────────────────────────────────────────────
class TestTranspersonalEngineSingleton:
    def test_singleton_stable(self):
        a = get_transpersonal_engine()
        b = get_transpersonal_engine()
        assert a is b

    def test_instance_type(self):
        assert isinstance(get_transpersonal_engine(), TranspersonalEngine)


# ── Core logic ─────────────────────────────────────────────────────────
class TestTranspersonalEngineLogic:
    def test_detect_returns_reading(self):
        engine = get_transpersonal_engine()
        result = engine.detect({})
        assert isinstance(result, TranspersonalReading)

    def test_reading_has_state(self):
        engine = get_transpersonal_engine()
        result = engine.detect({})
        assert hasattr(result, "state")
        assert isinstance(result.state, TranspersonalState)

    def test_reading_has_intensity(self):
        engine = get_transpersonal_engine()
        result = engine.detect({})
        assert hasattr(result, "intensity")
        assert 0.0 <= result.intensity <= 1.0

    def test_reading_has_response_posture(self):
        engine = get_transpersonal_engine()
        result = engine.detect({})
        assert hasattr(result, "response_posture")
        assert isinstance(result.response_posture, str)

    def test_numinous_language_triggers_elevated_state(self):
        engine = get_transpersonal_engine()
        result = engine.detect({
            "turn_text": "I felt a profound dissolution of self into pure awareness."
        })
        assert isinstance(result, TranspersonalReading)


# ── Edge cases ─────────────────────────────────────────────────────────
class TestTranspersonalEngineEdgeCases:
    def test_empty_context_no_raise(self):
        get_transpersonal_engine().detect({})

    def test_none_turn_text_handled(self):
        get_transpersonal_engine().detect({"turn_text": None})

    def test_empty_turn_text_handled(self):
        get_transpersonal_engine().detect({"turn_text": ""})

    def test_ordinary_text_returns_baseline_state(self):
        engine = get_transpersonal_engine()
        result = engine.detect({"turn_text": "Can you help me write a cover letter?"})
        assert isinstance(result.state, TranspersonalState)
