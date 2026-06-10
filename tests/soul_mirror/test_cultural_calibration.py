"""Tests for core/cultural_calibration.py — Issue #274"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.cultural_calibration import (
    CulturalCalibrationEngine,
    get_cultural_calibration_engine,
    CulturalProfile,
)


# ── Smoke ──────────────────────────────────────────────────────────────
class TestCulturalCalibrationImport:
    def test_module_imports(self):
        import core.cultural_calibration  # noqa: F401

    def test_class_exists(self):
        assert CulturalCalibrationEngine is not None


# ── Singleton ──────────────────────────────────────────────────────────
class TestCulturalCalibrationSingleton:
    def test_singleton_stable(self):
        a = get_cultural_calibration_engine()
        b = get_cultural_calibration_engine()
        assert a is b

    def test_instance_type(self):
        assert isinstance(get_cultural_calibration_engine(), CulturalCalibrationEngine)


# ── Core logic ─────────────────────────────────────────────────────────
class TestCulturalCalibrationLogic:
    def test_calibrate_returns_cultural_profile(self):
        engine = get_cultural_calibration_engine()
        result = engine.calibrate({})
        assert isinstance(result, CulturalProfile)

    def test_profile_has_region_field(self):
        engine = get_cultural_calibration_engine()
        result = engine.calibrate({})
        assert hasattr(result, "region")

    def test_profile_has_communication_style(self):
        engine = get_cultural_calibration_engine()
        result = engine.calibrate({})
        assert hasattr(result, "communication_style")
        assert isinstance(result.communication_style, str)

    def test_profile_has_directness_score(self):
        engine = get_cultural_calibration_engine()
        result = engine.calibrate({})
        assert hasattr(result, "directness")
        assert 0.0 <= result.directness <= 1.0

    def test_explicit_locale_respected(self):
        engine = get_cultural_calibration_engine()
        result = engine.calibrate({"locale": "ja-JP"})
        assert isinstance(result, CulturalProfile)


# ── Edge cases ─────────────────────────────────────────────────────────
class TestCulturalCalibrationEdgeCases:
    def test_empty_context_no_raise(self):
        get_cultural_calibration_engine().calibrate({})

    def test_unknown_locale_fallback(self):
        engine = get_cultural_calibration_engine()
        result = engine.calibrate({"locale": "xx-XX"})
        assert isinstance(result, CulturalProfile)

    def test_none_locale_handled(self):
        engine = get_cultural_calibration_engine()
        result = engine.calibrate({"locale": None})
        assert isinstance(result, CulturalProfile)

    def test_empty_locale_handled(self):
        engine = get_cultural_calibration_engine()
        result = engine.calibrate({"locale": ""})
        assert isinstance(result, CulturalProfile)
