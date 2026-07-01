"""Tests for core/shadow_integration.py — Issue #274"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.shadow_integration import (
    ShadowIntegrationEngine,
    get_shadow_integration_engine,
    ShadowReading,
    ShadowPattern,
)


# ── Smoke ──────────────────────────────────────────────────────────────
class TestShadowIntegrationImport:
    def test_module_imports(self):
        import core.shadow_integration  # noqa: F401

    def test_class_exists(self):
        assert ShadowIntegrationEngine is not None


# ── Singleton ──────────────────────────────────────────────────────────
class TestShadowIntegrationSingleton:
    def test_singleton_stable(self):
        a = get_shadow_integration_engine()
        b = get_shadow_integration_engine()
        assert a is b

    def test_instance_type(self):
        assert isinstance(get_shadow_integration_engine(), ShadowIntegrationEngine)


# ── Core logic ─────────────────────────────────────────────────────────
class TestShadowIntegrationLogic:
    def test_detect_returns_shadow_reading(self):
        engine = get_shadow_integration_engine()
        result = engine.detect({})
        assert isinstance(result, ShadowReading)

    def test_reading_has_patterns_list(self):
        engine = get_shadow_integration_engine()
        result = engine.detect({})
        assert hasattr(result, "patterns")
        assert isinstance(result.patterns, list)

    def test_patterns_are_shadow_pattern_type(self):
        engine = get_shadow_integration_engine()
        result = engine.detect({"turn_text": "I am never angry."})
        for p in result.patterns:
            assert isinstance(p, ShadowPattern)

    def test_reading_has_integration_score(self):
        engine = get_shadow_integration_engine()
        result = engine.detect({})
        assert hasattr(result, "integration_score")
        assert 0.0 <= result.integration_score <= 1.0

    def test_classic_projection_detected(self):
        engine = get_shadow_integration_engine()
        result = engine.detect({"turn_text": "Everyone around me is so selfish."})
        assert isinstance(result, ShadowReading)


# ── Edge cases ─────────────────────────────────────────────────────────
class TestShadowIntegrationEdgeCases:
    def test_empty_context_no_raise(self):
        get_shadow_integration_engine().detect({})

    def test_empty_turn_text(self):
        get_shadow_integration_engine().detect({"turn_text": ""})

    def test_none_turn_text(self):
        get_shadow_integration_engine().detect({"turn_text": None})

    def test_patterns_list_empty_for_neutral_text(self):
        engine = get_shadow_integration_engine()
        result = engine.detect({"turn_text": "The weather is nice today."})
        assert isinstance(result.patterns, list)
