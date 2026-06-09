"""
core/policy/__init__.py

Trust & Permission Policy Engine package.
Issue #229 — governs every autonomous action GAIA takes.
"""

from core.policy.trust_policy_engine import (
    ActionGate,
    PermissionScope,
    PolicyDecision,
    PolicyEvaluationResult,
    RiskLevel,
    ToolPolicy,
    TrustPolicyEngine,
) if False else None  # noqa: F401 — re-exported via explicit imports below

from core.policy.trust_policy_engine import TrustPolicyEngine
from core.policy.trust_policy_engine import PermissionScope
from core.policy.trust_policy_engine import PolicyDecision
from core.policy.trust_policy_engine import RiskLevel
from core.policy.trust_policy_engine import ToolPolicy
from core.action_gate import ActionGate
from core.action_gate import ActionDeniedError
from core.action_gate import ActionPendingApprovalError

__all__ = [
    "TrustPolicyEngine",
    "PermissionScope",
    "PolicyDecision",
    "RiskLevel",
    "ToolPolicy",
    "ActionGate",
    "ActionDeniedError",
    "ActionPendingApprovalError",
]
