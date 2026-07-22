"""tests/test_governance.py

Test scaffold for src-python/governance

Covers: GovernanceEngine, GovernancePolicy, PolicyViolation, RiskLevel
"""
import pytest

from governance import GovernanceEngine, GovernancePolicy, PolicyViolation, RiskLevel


class TestGovernancePolicy:

    def test_policy_constructs(self):
        policy = GovernancePolicy(
            name="No Unacceptable Risk",
            description="Prohibit unacceptable AI actions per EU AI Act.",
            risk_level=RiskLevel.UNACCEPTABLE,
            rules=["action != 'biometric_mass_surveillance'"],
            references=["EU AI Act Art. 5"],
        )
        assert policy.name == "No Unacceptable Risk"
        assert policy.policy_id  # UUID auto-assigned


class TestGovernanceEngine:

    def test_register_policy(self):
        engine = GovernanceEngine()
        policy = GovernancePolicy(
            name="High Risk Policy",
            description="High-risk AI conformity.",
            risk_level=RiskLevel.HIGH,
        )
        engine.register_policy(policy)
        assert policy.policy_id in engine._policies

    def test_evaluate_raises_not_implemented(self):
        engine = GovernanceEngine()
        with pytest.raises(NotImplementedError):
            engine.evaluate(action="deploy_model")

    def test_audit_log_initially_empty(self):
        engine = GovernanceEngine()
        assert engine.audit_log() == []
