"""Tests for core/individuation_engine.py (and core/individuation.py) — Issue #274"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.individuation_engine import (
    IndividuationEngine,
    get_individuation_engine,
    IndividuationScore,
)


# ── Smoke ──────────────────────────────────────────────────────────────
class TestIndividuationEngineImport:
    def test_module_imports_without_error(self):
        import core.individuation_engine  # noqa: F401

    def test_individuation_module_imports(self):
        import core.individuation  # noqa: F401

    def test_class_exists(self):
        assert IndividuationEngine is not None


# ── Singleton ──────────────────────────────────────────────────────────
class TestIndividuationEngineSingleton:
    def test_singleton_stable(self):
        a = get_individuation_engine()
        b = get_individuation_engine()
        assert a is b

    def test_instance_type(self):
        assert isinstance(get_individuation_engine(), IndividuationEngine)


# ── Core logic ─────────────────────────────────────────────────────────
class TestIndividuationEngineLogic:
    def test_score_returns_individuation_score(self):
        engine = get_individuation_engine()
        result = engine.score({})
        assert isinstance(result, IndividuationScore)

    def test_score_has_numeric_value(self):
        engine = get_individuation_engine()
        result = engine.score({})
        assert hasattr(result, "value")
        assert isinstance(result.value, float)

    def test_score_value_in_range(self):
        engine = get_individuation_engine()
        result = engine.score({})
        assert 0.0 <= result.value <= 1.0

    def test_score_has_stage_label(self):
        engine = get_individuation_engine()
        result = engine.score({})
        assert hasattr(result, "stage")
        assert isinstance(result.stage, str)
        assert len(result.stage) > 0


# ── Edge cases ─────────────────────────────────────────────────────────
class TestIndividuationEngineEdgeCases:
    def test_empty_context_no_raise(self):
        get_individuation_engine().score({})

    def test_missing_shadow_key_handled(self):
        get_individuation_engine().score({"shadow_active": None})

    def test_high_integration_context(self):
        result = get_individuation_engine().score({"integration_level": 1.0})
        assert result.value <= 1.0

    def test_zero_integration_context(self):
        result = get_individuation_engine().score({"integration_level": 0.0})
        assert result.value >= 0.0
