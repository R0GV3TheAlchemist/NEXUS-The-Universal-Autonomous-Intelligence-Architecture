"""Tests for ActionGate v2 — Issue #263."""
from __future__ import annotations

import pytest

from core.safety.action_gate import (
    ActionGate,
    ActionRecord,
    GateDecision,
    GateOutcome,
    RiskClassifier,
    RiskTier,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gate(**kwargs) -> ActionGate:
    return ActionGate(session_id='test-session', **kwargs)


# ---------------------------------------------------------------------------
# LOW tier
# ---------------------------------------------------------------------------

class TestLowTier:
    def test_low_approved(self) -> None:
        gate = _gate()
        d = gate.evaluate('read_memory')
        assert d.risk_tier == RiskTier.LOW
        assert d.outcome == GateOutcome.APPROVED
        assert d.may_proceed

    def test_low_logged_to_audit(self) -> None:
        gate = _gate()
        gate.evaluate('read_memory')
        assert len(gate.audit_log) == 1


# ---------------------------------------------------------------------------
# MEDIUM tier
# ---------------------------------------------------------------------------

class TestMediumTier:
    def test_bulk_operation_medium(self) -> None:
        gate = _gate()
        d = gate.evaluate('process_entries', context={'bulk_operation': True})
        assert d.risk_tier == RiskTier.MEDIUM
        assert d.may_proceed


# ---------------------------------------------------------------------------
# HIGH tier
# ---------------------------------------------------------------------------

class TestHighTier:
    def test_high_action_approved_with_audit(self) -> None:
        gate = _gate()
        d = gate.evaluate('send_external_message')
        assert d.risk_tier == RiskTier.HIGH
        assert d.outcome == GateOutcome.APPROVED
        assert d.may_proceed

    def test_external_systems_flag_escalates(self) -> None:
        gate = _gate()
        d = gate.evaluate('some_action', context={'affects_external_systems': True})
        assert d.risk_tier == RiskTier.HIGH


# ---------------------------------------------------------------------------
# CRITICAL tier
# ---------------------------------------------------------------------------

class TestCriticalTier:
    def test_critical_blocked_without_handler(self) -> None:
        gate = _gate(human_veto_handler=None)
        d = gate.evaluate('delete_memory')
        assert d.risk_tier == RiskTier.CRITICAL
        assert d.outcome == GateOutcome.BLOCKED
        assert not d.may_proceed

    def test_critical_approved_by_handler(self) -> None:
        gate = _gate(human_veto_handler=lambda _: True)
        d = gate.evaluate('delete_memory')
        assert d.outcome == GateOutcome.APPROVED
        assert d.may_proceed

    def test_critical_vetoed_by_handler(self) -> None:
        gate = _gate(human_veto_handler=lambda _: False)
        d = gate.evaluate('delete_memory')
        assert d.outcome == GateOutcome.VETOED
        assert not d.may_proceed

    def test_critical_has_veto_prompt(self) -> None:
        gate = _gate(human_veto_handler=None)
        d = gate.evaluate('delete_memory')
        assert d.veto_prompt is not None
        assert 'delete_memory' in d.veto_prompt


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

class TestAuditLog:
    def test_audit_log_grows(self) -> None:
        gate = _gate()
        gate.evaluate('read_memory')
        gate.evaluate('send_external_message')
        assert len(gate.audit_log) == 2

    def test_audit_record_has_checksum(self) -> None:
        gate = _gate()
        gate.evaluate('read_memory')
        record = gate.audit_log[0]
        assert isinstance(record.checksum, str)
        assert len(record.checksum) == 16

    def test_audit_summary_counts(self) -> None:
        gate = _gate()
        gate.evaluate('read_memory')           # LOW
        gate.evaluate('send_external_message') # HIGH
        summary = gate.audit_summary()
        assert summary['total'] == 2
        assert summary['LOW'] == 1
        assert summary['HIGH'] == 1

    def test_get_audit_log_returns_copy(self) -> None:
        gate = _gate()
        gate.evaluate('read_memory')
        log = gate.get_audit_log()
        assert log is not gate.audit_log


# ---------------------------------------------------------------------------
# RiskClassifier custom overrides
# ---------------------------------------------------------------------------

class TestRiskClassifier:
    def test_custom_critical_actions(self) -> None:
        classifier = RiskClassifier(
            critical_actions=frozenset({'my_custom_action'})
        )
        gate = ActionGate(classifier=classifier, session_id='test')
        d = gate.evaluate('my_custom_action')
        assert d.risk_tier == RiskTier.CRITICAL
