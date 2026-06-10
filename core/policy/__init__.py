"""
core/policy/__init__.py

Trust & Permission Policy Engine package.
Issue #229 — governs every autonomous action GAIA takes.
"""

from core.policy.trust_policy_engine import TrustPolicyEngine
from core.policy.trust_policy_engine import PermissionScope
from core.policy.trust_policy_engine import PolicyDecision
from core.policy.trust_policy_engine import PolicyEvaluationResult
from core.policy.trust_policy_engine import RiskLevel
from core.policy.trust_policy_engine import ToolPolicy
from core.action_gate import ActionGate
from core.action_gate import ActionDeniedError
from core.action_gate import ActionPendingApprovalError

__all__ = [
    "TrustPolicyEngine",
    "PermissionScope",
    "PolicyDecision",
    "PolicyEvaluationResult",
    "RiskLevel",
    "ToolPolicy",
    "ActionGate",
    "ActionDeniedError",
    "ActionPendingApprovalError",
]
