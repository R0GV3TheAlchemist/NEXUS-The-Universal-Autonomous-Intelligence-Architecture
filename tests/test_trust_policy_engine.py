"""
tests/test_trust_policy_engine.py

Test suite for the Trust & Permission Policy Engine.
Verifies all acceptance criteria from issue #229.
"""

import pytest

from core.action_gate import ActionDeniedError, ActionGate, ActionPendingApprovalError
from core.policy.trust_policy_engine import (
    PermissionScope,
    PolicyDecision,
    RiskLevel,
    ToolPolicy,
    TrustPolicyEngine,
)


SESSION_ID = "test-session-001"
AGENT_ID = "test-agent"


# ---------------------------------------------------------------------------
# TrustPolicyEngine unit tests
# ---------------------------------------------------------------------------

class TestTrustPolicyEngine:
    def setup_method(self):
        self.engine = TrustPolicyEngine(session_id=SESSION_ID, agent_id=AGENT_ID)

    def test_known_low_risk_tool_is_allowed(self):
        result = self.engine.evaluate("read_memory")
        assert result.decision == PolicyDecision.ALLOW

    def test_unknown_tool_is_denied(self):
        result = self.engine.evaluate("mystery_tool")
        assert result.decision == PolicyDecision.DENY

    def test_critical_risk_requires_approval(self):
        result = self.engine.evaluate("delete_file")
        assert result.decision == PolicyDecision.REQUIRE_APPROVAL
        assert result.approval_prompt is not None

    def test_high_risk_without_preapproval_requires_approval(self):
        result = self.engine.evaluate("write_file")
        assert result.decision == PolicyDecision.REQUIRE_APPROVAL

    def test_pre_approved_scope_allows_high_risk(self):
        self.engine.pre_approve_scope(PermissionScope.WRITE_FILE)
        result = self.engine.evaluate("write_file")
        assert result.decision == PolicyDecision.ALLOW

    def test_revoke_scope_restores_approval_requirement(self):
        self.engine.pre_approve_scope(PermissionScope.WRITE_FILE)
        self.engine.revoke_scope(PermissionScope.WRITE_FILE)
        result = self.engine.evaluate("write_file")
        assert result.decision == PolicyDecision.REQUIRE_APPROVAL

    def test_audit_log_records_every_decision(self):
        self.engine.evaluate("read_memory")
        self.engine.evaluate("delete_file")
        log = self.engine.get_audit_log()
        assert len(log) == 2
        assert log[0]["tool_name"] == "read_memory"
        assert log[1]["tool_name"] == "delete_file"

    def test_audit_record_has_timestamp_and_decision(self):
        self.engine.evaluate("read_canon")
        log = self.engine.get_audit_log()
        record = log[0]
        assert "timestamp" in record
        assert "decision" in record
        assert record["session_id"] == SESSION_ID
        assert record["agent_id"] == AGENT_ID

    def test_approval_recorded_on_record(self):
        result = self.engine.evaluate("delete_file")
        self.engine.record_approval(result.record_id, approved_by="gaian")
        log = self.engine.get_audit_log()
        assert log[-1]["approved_by"] == "gaian"

    def test_custom_policy_registration(self):
        self.engine.register_policy(ToolPolicy(
            tool_name="custom_tool",
            required_scope=PermissionScope.CALL_EXTERNAL_API,
            risk_level=RiskLevel.LOW,
        ))
        result = self.engine.evaluate("custom_tool")
        assert result.decision == PolicyDecision.ALLOW


# ---------------------------------------------------------------------------
# ActionGate integration tests
# ---------------------------------------------------------------------------

class TestActionGate:
    def setup_method(self):
        self.gate = ActionGate(session_id=SESSION_ID, agent_id=AGENT_ID)

    def test_guard_allows_low_risk_tool(self):
        with self.gate.guard("read_memory"):
            pass  # Should not raise

    def test_guard_raises_on_denied_tool(self):
        with pytest.raises(ActionDeniedError):
            with self.gate.guard("mystery_tool"):
                pass

    def test_guard_raises_pending_approval_for_critical_tool(self):
        with pytest.raises(ActionPendingApprovalError) as exc_info:
            with self.gate.guard("delete_file"):
                pass
        assert exc_info.value.tool_name == "delete_file"
        assert exc_info.value.record_id is not None

    def test_approval_callback_allows_action(self):
        gate = ActionGate(
            session_id=SESSION_ID,
            agent_id=AGENT_ID,
            approval_callback=lambda tool, prompt: True,
        )
        with gate.guard("delete_file"):
            pass  # Callback returns True — should not raise

    def test_approval_callback_deny_raises(self):
        gate = ActionGate(
            session_id=SESSION_ID,
            agent_id=AGENT_ID,
            approval_callback=lambda tool, prompt: False,
        )
        with pytest.raises(ActionDeniedError):
            with gate.guard("delete_file"):
                pass

    def test_pre_approve_scope_via_gate(self):
        self.gate.pre_approve_scope(PermissionScope.WRITE_FILE)
        with self.gate.guard("write_file", {"path": "canon/test.md"}):
            pass  # Should not raise

    def test_audit_log_accessible_via_gate(self):
        with self.gate.guard("read_memory"):
            pass
        log = self.gate.get_audit_log()
        assert len(log) >= 1
        assert log[0]["decision"] == "allow"
