"""Tests for core/subject_side_identity.py — Issue #274"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.subject_side_identity import (
    SubjectSideIdentity,
    get_subject_side_identity,
    IdentityReading,
)


# ── Smoke ──────────────────────────────────────────────────────────────
class TestSubjectSideIdentityImport:
    def test_module_imports_without_error(self):
        import core.subject_side_identity  # noqa: F401

    def test_class_exists(self):
        assert SubjectSideIdentity is not None

    def test_factory_callable(self):
        assert callable(get_subject_side_identity)


# ── Singleton ──────────────────────────────────────────────────────────
class TestSubjectSideIdentitySingleton:
    def test_singleton_returns_same_instance(self):
        a = get_subject_side_identity()
        b = get_subject_side_identity()
        assert a is b

    def test_singleton_is_correct_type(self):
        engine = get_subject_side_identity()
        assert isinstance(engine, SubjectSideIdentity)


# ── Core logic ─────────────────────────────────────────────────────────
class TestSubjectSideIdentityLogic:
    def test_read_returns_identity_reading(self):
        engine = get_subject_side_identity()
        result = engine.read({})
        assert isinstance(result, IdentityReading)

    def test_reading_has_coherence_field(self):
        engine = get_subject_side_identity()
        result = engine.read({})
        assert hasattr(result, "coherence")

    def test_coherence_is_float(self):
        engine = get_subject_side_identity()
        result = engine.read({})
        assert isinstance(result.coherence, float)

    def test_coherence_in_range(self):
        engine = get_subject_side_identity()
        result = engine.read({})
        assert 0.0 <= result.coherence <= 1.0

    def test_reading_has_label(self):
        engine = get_subject_side_identity()
        result = engine.read({})
        assert hasattr(result, "label")
        assert isinstance(result.label, str)


# ── Edge cases ─────────────────────────────────────────────────────────
class TestSubjectSideIdentityEdgeCases:
    def test_empty_context_does_not_raise(self):
        engine = get_subject_side_identity()
        engine.read({})

    def test_none_turn_text_handled(self):
        engine = get_subject_side_identity()
        engine.read({"turn_text": None})

    def test_empty_string_turn_handled(self):
        engine = get_subject_side_identity()
        engine.read({"turn_text": ""})

    def test_very_long_input_handled(self):
        engine = get_subject_side_identity()
        engine.read({"turn_text": "x" * 10_000})
