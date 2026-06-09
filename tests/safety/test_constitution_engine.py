"""Tests for ConstitutionEngine — Issue #263."""
from __future__ import annotations

import pytest

from core.safety.constitution_engine import (
    AlignmentProof,
    ConstitutionEngine,
    ConstitutionSet,
    ConstitutionViolation,
    Constraint,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _engine() -> ConstitutionEngine:
    return ConstitutionEngine()


def _build(values: list[str], **kwargs) -> ConstitutionSet:
    return _engine().build_from_values(
        session_id='test-123',
        sovereign_name='TestSovereign',
        declared_values=values,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# ConstitutionSet building
# ---------------------------------------------------------------------------

class TestBuildFromValues:
    def test_known_values_add_constraints(self) -> None:
        cs = _build(['sovereignty', 'care'])
        assert len(cs.constraints) == 2

    def test_unknown_value_skipped(self) -> None:
        cs = _build(['sovereignty', 'unknown_value_xyz'])
        assert len(cs.constraints) == 1

    def test_extra_constraints_appended(self) -> None:
        extra = Constraint(
            value_name='custom',
            rule='No custom bad action',
            forbidden_keywords=['custom_bad'],
        )
        cs = _build(['sovereignty'], extra_constraints=[extra])
        assert len(cs.constraints) == 2

    def test_sorted_by_priority(self) -> None:
        cs = _build(['sovereignty', 'care', 'rest'])
        priorities = [c.priority for c in cs.sorted_constraints()]
        assert priorities == sorted(priorities)


# ---------------------------------------------------------------------------
# AlignmentProof — passing checks
# ---------------------------------------------------------------------------

class TestAlignmentPassing:
    def test_clean_action_aligned(self) -> None:
        engine = _engine()
        cs = _build(['sovereignty', 'transparency'])
        proof = engine.check_alignment('read_memory', {}, cs)
        assert proof.is_aligned
        assert proof.confidence == 1.0

    def test_passed_checks_populated(self) -> None:
        engine = _engine()
        cs = _build(['sovereignty'])
        proof = engine.check_alignment('safe_action', {}, cs)
        assert len(proof.passed_checks) >= 1


# ---------------------------------------------------------------------------
# AlignmentProof — violations
# ---------------------------------------------------------------------------

class TestAlignmentViolations:
    def test_forbidden_keyword_in_action_type(self) -> None:
        engine = _engine()
        cs = _build(['sovereignty'])
        proof = engine.check_alignment('sovereignty_override', {}, cs)
        assert not proof.is_aligned
        assert len(proof.violations) >= 1

    def test_forbidden_keyword_in_context(self) -> None:
        engine = _engine()
        cs = _build(['transparency'])
        proof = engine.check_alignment(
            'update_profile',
            {'method': 'shadow_write'},
            cs,
        )
        assert not proof.is_aligned

    def test_confidence_below_one_on_violation(self) -> None:
        engine = _engine()
        cs = _build(['sovereignty', 'care'])
        proof = engine.check_alignment('sovereignty_override', {}, cs)
        assert proof.confidence < 1.0

    def test_audit_string_contains_violation(self) -> None:
        engine = _engine()
        cs = _build(['sovereignty'])
        proof = engine.check_alignment('sovereignty_override', {}, cs)
        audit = proof.to_audit_string()
        assert 'VIOLATION' in audit


# ---------------------------------------------------------------------------
# ConstitutionViolation exception
# ---------------------------------------------------------------------------

def test_constitution_violation_exception() -> None:
    engine = _engine()
    cs = _build(['sovereignty'])
    proof = engine.check_alignment('sovereignty_override', {}, cs)
    exc = ConstitutionViolation(proof)
    assert exc.proof is proof
    assert 'sovereignty' in str(exc).lower()
