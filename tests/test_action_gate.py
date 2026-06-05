"""
tests/test_action_gate.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for issue #248 — ActionGate as consent and human oversight
enforcement layer.
"""
from __future__ import annotations

import time

from core.agent import (
    ActionGate,
    ActionRiskLevel,
    AgentLoop,
    HaltReason,
    Perception,
    Plan,
    PlannedAction,
)


def _dummy_handler(value: int = 1):
    return value + 1


class TestActionGatePolicy:

    def test_low_risk_is_auto_or_log_approved(self):
        gate = ActionGate()
        gate.register_tool("safe_read", ActionRiskLevel.LOW)
        receipt = gate.request_approval(
            tool_name="safe_read",
            actor="gaian",
            args={},
            session_id="sess-1",
        )
        assert receipt.requirement in ("auto_approve", "log_only")
        assert gate.is_approved(receipt.receipt_id)

    def test_medium_risk_requires_human_approval(self):
        gate = ActionGate()
        gate.register_tool("write_file", ActionRiskLevel.MEDIUM)
        receipt = gate.request_approval(
            tool_name="write_file",
            actor="gaian",
            args={"path": "x"},
            session_id="sess-2",
        )
        assert receipt.requirement == "human_required"
        assert not gate.is_approved(receipt.receipt_id)
        assert gate.approve(receipt.receipt_id, "gaian")
        assert gate.is_approved(receipt.receipt_id)

    def test_irreversible_requires_multi_party(self):
        gate = ActionGate(multi_party_threshold=2)
        gate.register_tool("delete_prod_db", ActionRiskLevel.IRREVERSIBLE)
        receipt = gate.request_approval(
            tool_name="delete_prod_db",
            actor="gaian",
            args={"db": "prod"},
            session_id="sess-3",
        )
        assert receipt.requirement == "multi_party"
        assert not gate.is_approved(receipt.receipt_id)
        assert not gate.approve(receipt.receipt_id, "gaian")
        assert not gate.is_approved(receipt.receipt_id)
        assert gate.delegate("ops_admin", "gaian", [ActionRiskLevel.IRREVERSIBLE])
        assert gate.approve(receipt.receipt_id, "ops_admin")
        assert gate.is_approved(receipt.receipt_id)


class TestConsentReceipts:

    def test_receipt_is_signed(self):
        gate = ActionGate()
        gate.register_tool("write_file", ActionRiskLevel.MEDIUM)
        receipt = gate.request_approval("write_file", "gaian", {}, "sess-4")
        assert receipt.signature is not None
        assert len(receipt.signature) == 64
        assert gate.verify_receipt(receipt.receipt_id)

    def test_expired_receipt_is_not_approved(self):
        gate = ActionGate()
        gate.register_tool("write_file", ActionRiskLevel.MEDIUM)
        receipt = gate.request_approval(
            "write_file", "gaian", {}, "sess-5", expires_in_seconds=1
        )
        time.sleep(1.1)
        assert not gate.is_approved(receipt.receipt_id)
        assert not gate.approve(receipt.receipt_id, "gaian")


class TestDelegation:

    def test_delegation_allows_scoped_approval(self):
        gate = ActionGate()
        gate.register_tool("write_file", ActionRiskLevel.MEDIUM)
        gate.delegate("trusted_mod", "gaian", [ActionRiskLevel.MEDIUM], expires_in_seconds=60)
        receipt = gate.request_approval("write_file", "gaian", {}, "sess-6")
        assert gate.approve(receipt.receipt_id, "trusted_mod")
        assert gate.is_approved(receipt.receipt_id)

    def test_delegation_scope_denies_unlisted_risk(self):
        gate = ActionGate()
        gate.register_tool("delete_prod_db", ActionRiskLevel.IRREVERSIBLE)
        gate.delegate("trusted_mod", "gaian", [ActionRiskLevel.MEDIUM], expires_in_seconds=60)
        receipt = gate.request_approval("delete_prod_db", "gaian", {}, "sess-7")
        assert not gate.approve(receipt.receipt_id, "trusted_mod")
        assert not gate.is_approved(receipt.receipt_id)

    def test_revocation_removes_authority(self):
        gate = ActionGate()
        gate.register_tool("write_file", ActionRiskLevel.MEDIUM)
        gate.delegate("trusted_mod", "gaian", [ActionRiskLevel.MEDIUM], expires_in_seconds=60)
        gate.revoke_delegation("trusted_mod")
        receipt = gate.request_approval("write_file", "gaian", {}, "sess-8")
        assert not gate.approve(receipt.receipt_id, "trusted_mod")


class TestEmergencyHalt:

    def test_emergency_halt_marks_session_halted(self):
        gate = ActionGate()
        gate.register_session("sess-9")
        gate.emergency_halt("sess-9")
        assert gate.is_halted("sess-9")

    def test_global_emergency_halt_halts_registered_sessions(self):
        gate = ActionGate()
        gate.register_session("sess-a")
        gate.register_session("sess-b")
        gate.emergency_halt()
        assert gate.is_halted("sess-a")
        assert gate.is_halted("sess-b")


class TestAgentLoopIntegration:

    def test_loop_skips_unapproved_action(self):
        gate = ActionGate()
        gate.register_tool("write_file", ActionRiskLevel.MEDIUM)

        plan = Plan(
            goal="write something",
            steps=[
                PlannedAction(
                    name="write_file",
                    description="attempt write",
                    handler=_dummy_handler,
                    args={"value": 1},
                    risk_level="medium",
                )
            ],
        )
        perception = Perception(goal="write", session_id="sess-loop-1", gaian_id="gaian")
        loop = AgentLoop(max_iterations=5, action_gate=gate)
        state = loop.run(perception, plan)

        assert state.observations[0].action.status.value == "skipped"

    def test_loop_halts_on_critical_unapproved_action(self):
        gate = ActionGate()
        gate.register_tool("delete_prod_db", ActionRiskLevel.IRREVERSIBLE)

        plan = Plan(
            goal="dangerous op",
            steps=[
                PlannedAction(
                    name="delete_prod_db",
                    description="dangerous delete",
                    handler=_dummy_handler,
                    args={"value": 1},
                    critical=True,
                    risk_level="irreversible",
                )
            ],
        )
        perception = Perception(goal="dangerous", session_id="sess-loop-2", gaian_id="gaian")
        loop = AgentLoop(max_iterations=5, action_gate=gate)
        state = loop.run(perception, plan)

        assert state.status.value == "halted"
        assert state.halt_reason == HaltReason.POLICY_DENIED

    def test_loop_halts_when_session_emergency_halted(self):
        gate = ActionGate()
        gate.register_tool("safe_read", ActionRiskLevel.LOW)
        gate.register_session("sess-loop-3")
        gate.emergency_halt("sess-loop-3")

        plan = Plan(
            goal="read something",
            steps=[
                PlannedAction(
                    name="safe_read",
                    description="read",
                    handler=_dummy_handler,
                    args={"value": 1},
                    risk_level="low",
                )
            ],
        )
        perception = Perception(goal="read", session_id="sess-loop-3", gaian_id="gaian")
        loop = AgentLoop(max_iterations=5, action_gate=gate)
        state = loop.run(perception, plan)

        assert state.status.value == "halted"
        assert state.halt_reason == HaltReason.GAIAN_REQUESTED
