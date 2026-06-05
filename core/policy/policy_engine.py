"""
core/policy/policy_engine.py

The Trust & Permission Policy Engine.
Evaluates PolicyRequests against ordered PolicyRules and returns a PolicyDecision.

Evaluation priority:
  1. DENY  — explicit denials take precedence over everything.
  2. ALLOW — explicit grants are honoured when no denial applies.
  3. ESCALATE — borderline trust cases are flagged for review.
  4. Fallback DENY — if no rule matches, access is denied by default.

This is the runtime enforcement of C-SENTINEL Article 4:
  "The Sentinel must never grant access beyond what has been explicitly authorised."

Canon Reference: C-SENTINEL Article 4, C02 (Consent & Autonomy)
Issue:          #220
Version:        1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from core.policy.policy_models import (
    PolicyDecision,
    PolicyEffect,
    PolicyRequest,
    PolicyRule,
)

logger = logging.getLogger(__name__)


@dataclass
class PolicyEngine:
    """
    The Trust & Permission Policy Engine.

    Usage:
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(...))
        decision = engine.evaluate(request)

    Rules are evaluated in insertion order within each effect tier.
    Deny rules always win over allow rules.
    """
    rules: list[PolicyRule] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Rule management
    # ------------------------------------------------------------------

    def add_rule(self, rule: PolicyRule) -> None:
        """Register a policy rule."""
        self.rules.append(rule)
        logger.debug("[PolicyEngine] rule added: %s (%s)", rule.name, rule.effect.value)

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name. Returns True if found and removed."""
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < before

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        """
        Evaluate a PolicyRequest and return a PolicyDecision.

        Priority order:
          1. Explicit DENY
          2. Explicit ALLOW
          3. ESCALATE
          4. Fallback DENY (no match)
        """
        # 1. Check for explicit denial first
        deny_match = self._first_match(request, PolicyEffect.DENY)
        if deny_match:
            return self._build(
                effect=PolicyEffect.DENY,
                rule=deny_match,
                request=request,
                next_step="Adjust role, scope, action, or trust level before retrying.",
            )

        # 2. Check for explicit allow
        allow_match = self._first_match(request, PolicyEffect.ALLOW)
        if allow_match:
            return self._build(
                effect=PolicyEffect.ALLOW,
                rule=allow_match,
                request=request,
                next_step=None,
            )

        # 3. Check for escalation
        escalate_match = self._first_match(request, PolicyEffect.ESCALATE)
        if escalate_match:
            return self._build(
                effect=PolicyEffect.ESCALATE,
                rule=escalate_match,
                request=request,
                next_step="Request elevated review or additional trust verification.",
            )

        # 4. Fallback: deny with explanation
        logger.warning(
            "[PolicyEngine] no rule matched — fallback DENY actor=%s action=%s scope=%s",
            request.actor_id, request.action, request.scope,
        )
        return PolicyDecision(
            effect=PolicyEffect.DENY,
            reason=(
                f"No policy rule matched this request "
                f"(role='{request.role}', scope='{request.scope}', "
                f"action='{request.action}', trust={request.trust_level:.2f})."
            ),
            matched_rule=None,
            suggested_next_step="Add an explicit allow rule or reduce the requested scope.",
            request=request,
        )

    # ------------------------------------------------------------------
    # Bulk evaluation
    # ------------------------------------------------------------------

    def evaluate_all(self, requests: list[PolicyRequest]) -> list[PolicyDecision]:
        """Evaluate a batch of requests and return one decision per request."""
        return [self.evaluate(r) for r in requests]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _first_match(
        self, request: PolicyRequest, effect: PolicyEffect
    ) -> Optional[PolicyRule]:
        """Return the first rule of the given effect that matches the request."""
        for rule in self.rules:
            if rule.effect == effect and rule.matches(request):
                return rule
        return None

    def _build(
        self,
        effect: PolicyEffect,
        rule: PolicyRule,
        request: PolicyRequest,
        next_step: Optional[str],
    ) -> PolicyDecision:
        """Construct a PolicyDecision from a matched rule."""
        reason = rule.reason if rule.reason else self._auto_reason(effect, rule, request)
        decision = PolicyDecision(
            effect=effect,
            reason=reason,
            matched_rule=rule.name,
            suggested_next_step=next_step,
            request=request,
        )
        logger.info(
            "[PolicyEngine] actor=%s action=%s scope=%s trust=%.2f → %s (rule=%s)",
            request.actor_id, request.action, request.scope,
            request.trust_level, effect.value, rule.name,
        )
        return decision

    @staticmethod
    def _auto_reason(
        effect: PolicyEffect, rule: PolicyRule, request: PolicyRequest
    ) -> str:
        return (
            f"Rule '{rule.name}' matched for role='{request.role}', "
            f"scope='{request.scope}', action='{request.action}' "
            f"(trust={request.trust_level:.2f}). "
            f"Decision: {effect.value}."
        )
