"""
core/policy/policy_models.py

Data models for the Trust & Permission Policy Engine.
Every access decision GAIA makes is grounded in an explicit, inspectable rule.

Canon Reference: C-SENTINEL Article 4, C02 (Consent & Autonomy)
Issue:          #220
Version:        1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class PolicyEffect(Enum):
    """
    The outcome of a policy evaluation.
    ALLOW  — the request is permitted.
    DENY   — the request is forbidden.
    ESCALATE — insufficient trust; requires elevated review.
    """
    ALLOW    = "allow"
    DENY     = "deny"
    ESCALATE = "escalate"


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

@dataclass
class PolicyRequest:
    """
    A single access request to be evaluated by the policy engine.

    Attributes:
        actor_id:    Identifier of the requesting entity (Gaian, agent, service).
        role:        Role of the actor (e.g. 'admin', 'member', 'guest').
        scope:       Resource scope being accessed (e.g. 'admin', 'memory', 'sensitive').
        action:      Action being attempted (e.g. 'read', 'write', 'delete').
        trust_level: Float 0.0–1.0 reflecting actor trustworthiness at time of request.
        context:     Arbitrary key-value metadata for context-aware rule matching.
    """
    actor_id:    str
    role:        str
    scope:       str
    action:      str
    trust_level: float
    context:     dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.trust_level <= 1.0:
            raise ValueError(
                f"trust_level must be between 0.0 and 1.0, got {self.trust_level}"
            )


# ---------------------------------------------------------------------------
# Rule
# ---------------------------------------------------------------------------

@dataclass
class PolicyRule:
    """
    A declarative policy rule.

    A rule matches a request when ALL specified conditions are satisfied:
      - role is in the allowed roles list (if specified)
      - scope is in the allowed scopes list (if specified)
      - action is in the allowed actions list (if specified)
      - trust_level meets the minimum threshold
      - context_matcher returns True (if provided)

    Empty lists are treated as wildcards (match any value).
    """
    name:            str
    effect:          PolicyEffect
    roles:           list[str]                           = field(default_factory=list)
    scopes:          list[str]                           = field(default_factory=list)
    actions:         list[str]                           = field(default_factory=list)
    min_trust_level: float                               = 0.0
    context_matcher: Optional[Callable[[dict], bool]]   = None
    reason:          str                                 = ""

    def matches(self, request: PolicyRequest) -> bool:
        """Return True if this rule applies to the given request."""
        if self.roles and request.role not in self.roles:
            return False
        if self.scopes and request.scope not in self.scopes:
            return False
        if self.actions and request.action not in self.actions:
            return False
        if request.trust_level < self.min_trust_level:
            return False
        if self.context_matcher and not self.context_matcher(request.context):
            return False
        return True


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

@dataclass
class PolicyDecision:
    """
    The result of a policy evaluation.

    Every decision includes:
      - effect:            What happens (ALLOW, DENY, ESCALATE).
      - reason:            Plain-language explanation of why.
      - matched_rule:      The rule name that triggered this decision (None = no match).
      - suggested_next_step: What the actor should do next (optional).
      - request:           The original request for full traceability.

    Acceptance Criterion: Each decision includes a human-readable explanation.
    """
    effect:              PolicyEffect
    reason:              str
    matched_rule:        Optional[str]         = None
    suggested_next_step: Optional[str]         = None
    request:             Optional[PolicyRequest] = None

    def to_dict(self) -> dict:
        """Human-readable export for logging and audit."""
        return {
            "effect":              self.effect.value,
            "reason":              self.reason,
            "matched_rule":        self.matched_rule,
            "suggested_next_step": self.suggested_next_step,
            "actor_id":            self.request.actor_id if self.request else None,
            "role":                self.request.role if self.request else None,
            "scope":               self.request.scope if self.request else None,
            "action":              self.request.action if self.request else None,
            "trust_level":         self.request.trust_level if self.request else None,
        }
