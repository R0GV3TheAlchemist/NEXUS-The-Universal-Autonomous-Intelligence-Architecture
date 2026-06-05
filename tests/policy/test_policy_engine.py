"""
tests/policy/test_policy_engine.py

Full test suite for the Trust & Permission Policy Engine.
Covers allow, deny, escalate, fallback, context-matching, and bulk evaluation.

Canon Reference: C-SENTINEL Article 4, C02 (Consent & Autonomy)
Issue:           #220
"""

import pytest

from core.policy.policy_engine import PolicyEngine
from core.policy.policy_models import (
    PolicyDecision,
    PolicyEffect,
    PolicyRequest,
    PolicyRule,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> PolicyEngine:
    return PolicyEngine(
        rules=[
            PolicyRule(
                name="deny-guest-admin-write",
                effect=PolicyEffect.DENY,
                roles=["guest"],
                scopes=["admin"],
                actions=["write"],
                min_trust_level=0.0,
                reason="Guest users cannot perform admin write actions.",
            ),
            PolicyRule(
                name="allow-admin-read",
                effect=PolicyEffect.ALLOW,
                roles=["admin"],
                scopes=["admin"],
                actions=["read"],
                min_trust_level=0.5,
                reason="Trusted admins may read admin resources.",
            ),
            PolicyRule(
                name="allow-member-project-read",
                effect=PolicyEffect.ALLOW,
                roles=["member"],
                scopes=["project"],
                actions=["read"],
                min_trust_level=0.3,
                reason="Members with baseline trust may read project resources.",
            ),
            PolicyRule(
                name="escalate-member-sensitive-write",
                effect=PolicyEffect.ESCALATE,
                roles=["member"],
                scopes=["sensitive"],
                actions=["write"],
                min_trust_level=0.6,
                reason="Sensitive writes from member accounts require elevated review.",
            ),
        ]
    )


@pytest.fixture
def admin_read_request() -> PolicyRequest:
    return PolicyRequest(
        actor_id="admin-001",
        role="admin",
        scope="admin",
        action="read",
        trust_level=0.9,
    )


@pytest.fixture
def guest_write_request() -> PolicyRequest:
    return PolicyRequest(
        actor_id="guest-001",
        role="guest",
        scope="admin",
        action="write",
        trust_level=0.2,
    )


@pytest.fixture
def member_sensitive_write_request() -> PolicyRequest:
    return PolicyRequest(
        actor_id="member-001",
        role="member",
        scope="sensitive",
        action="write",
        trust_level=0.8,
    )


# ---------------------------------------------------------------------------
# PolicyRequest validation
# ---------------------------------------------------------------------------

class TestPolicyRequest:

    def test_valid_trust_level(self):
        r = PolicyRequest(actor_id="a", role="admin", scope="x", action="read", trust_level=0.5)
        assert r.trust_level == 0.5

    def test_trust_level_above_one_raises(self):
        with pytest.raises(ValueError):
            PolicyRequest(actor_id="a", role="admin", scope="x", action="read", trust_level=1.1)

    def test_trust_level_below_zero_raises(self):
        with pytest.raises(ValueError):
            PolicyRequest(actor_id="a", role="admin", scope="x", action="read", trust_level=-0.1)

    def test_boundary_values_accepted(self):
        PolicyRequest(actor_id="a", role="r", scope="s", action="a", trust_level=0.0)
        PolicyRequest(actor_id="a", role="r", scope="s", action="a", trust_level=1.0)


# ---------------------------------------------------------------------------
# PolicyRule matching
# ---------------------------------------------------------------------------

class TestPolicyRule:

    def test_empty_lists_match_any(self):
        rule = PolicyRule(
            name="wildcard",
            effect=PolicyEffect.ALLOW,
            min_trust_level=0.0,
        )
        request = PolicyRequest(actor_id="x", role="anything", scope="anything", action="anything", trust_level=0.5)
        assert rule.matches(request)

    def test_role_mismatch_does_not_match(self):
        rule = PolicyRule(name="r", effect=PolicyEffect.ALLOW, roles=["admin"])
        request = PolicyRequest(actor_id="x", role="guest", scope="s", action="read", trust_level=0.5)
        assert not rule.matches(request)

    def test_insufficient_trust_does_not_match(self):
        rule = PolicyRule(name="r", effect=PolicyEffect.ALLOW, min_trust_level=0.8)
        request = PolicyRequest(actor_id="x", role="admin", scope="s", action="read", trust_level=0.5)
        assert not rule.matches(request)

    def test_context_matcher_false_does_not_match(self):
        rule = PolicyRule(
            name="r",
            effect=PolicyEffect.ALLOW,
            context_matcher=lambda ctx: ctx.get("approved") is True,
        )
        request = PolicyRequest(actor_id="x", role="admin", scope="s", action="read", trust_level=0.5, context={"approved": False})
        assert not rule.matches(request)


# ---------------------------------------------------------------------------
# Allow
# ---------------------------------------------------------------------------

class TestAllow:

    def test_admin_read_is_allowed(self, engine, admin_read_request):
        decision = engine.evaluate(admin_read_request)
        assert decision.effect == PolicyEffect.ALLOW

    def test_allow_decision_includes_matched_rule(self, engine, admin_read_request):
        decision = engine.evaluate(admin_read_request)
        assert decision.matched_rule == "allow-admin-read"

    def test_allow_decision_has_reason(self, engine, admin_read_request):
        decision = engine.evaluate(admin_read_request)
        assert len(decision.reason) > 0

    def test_allow_reason_content(self, engine, admin_read_request):
        decision = engine.evaluate(admin_read_request)
        assert "trusted admins" in decision.reason.lower()

    def test_allow_has_no_next_step(self, engine, admin_read_request):
        decision = engine.evaluate(admin_read_request)
        assert decision.suggested_next_step is None

    def test_member_project_read_allowed(self, engine):
        request = PolicyRequest(
            actor_id="m1", role="member", scope="project", action="read", trust_level=0.5
        )
        assert engine.evaluate(request).effect == PolicyEffect.ALLOW


# ---------------------------------------------------------------------------
# Deny
# ---------------------------------------------------------------------------

class TestDeny:

    def test_guest_admin_write_is_denied(self, engine, guest_write_request):
        decision = engine.evaluate(guest_write_request)
        assert decision.effect == PolicyEffect.DENY

    def test_deny_decision_includes_matched_rule(self, engine, guest_write_request):
        decision = engine.evaluate(guest_write_request)
        assert decision.matched_rule == "deny-guest-admin-write"

    def test_deny_has_reason(self, engine, guest_write_request):
        decision = engine.evaluate(guest_write_request)
        assert "cannot" in decision.reason.lower()

    def test_deny_has_suggested_next_step(self, engine, guest_write_request):
        decision = engine.evaluate(guest_write_request)
        assert decision.suggested_next_step is not None

    def test_deny_wins_over_allow(self):
        engine = PolicyEngine(rules=[
            PolicyRule(
                name="allow-all",
                effect=PolicyEffect.ALLOW,
                reason="Allow everything.",
            ),
            PolicyRule(
                name="deny-specific",
                effect=PolicyEffect.DENY,
                roles=["guest"],
                reason="Deny guests.",
            ),
        ])
        request = PolicyRequest(actor_id="g", role="guest", scope="x", action="read", trust_level=1.0)
        assert engine.evaluate(request).effect == PolicyEffect.DENY


# ---------------------------------------------------------------------------
# Escalate
# ---------------------------------------------------------------------------

class TestEscalate:

    def test_member_sensitive_write_escalates(self, engine, member_sensitive_write_request):
        decision = engine.evaluate(member_sensitive_write_request)
        assert decision.effect == PolicyEffect.ESCALATE

    def test_escalate_has_matched_rule(self, engine, member_sensitive_write_request):
        decision = engine.evaluate(member_sensitive_write_request)
        assert decision.matched_rule == "escalate-member-sensitive-write"

    def test_escalate_has_next_step(self, engine, member_sensitive_write_request):
        decision = engine.evaluate(member_sensitive_write_request)
        assert "review" in decision.suggested_next_step.lower()

    def test_below_min_trust_does_not_escalate(self, engine):
        request = PolicyRequest(
            actor_id="m2", role="member", scope="sensitive", action="write", trust_level=0.3
        )
        # trust_level 0.3 < min 0.6, so escalate rule does not match -> fallback deny
        decision = engine.evaluate(request)
        assert decision.effect == PolicyEffect.DENY
        assert decision.matched_rule is None


# ---------------------------------------------------------------------------
# Fallback deny
# ---------------------------------------------------------------------------

class TestFallbackDeny:

    def test_no_match_returns_deny(self, engine):
        request = PolicyRequest(
            actor_id="x", role="unknown", scope="unknown", action="unknown", trust_level=0.5
        )
        decision = engine.evaluate(request)
        assert decision.effect == PolicyEffect.DENY
        assert decision.matched_rule is None

    def test_fallback_reason_explains_no_match(self, engine):
        request = PolicyRequest(
            actor_id="x", role="unknown", scope="unknown", action="unknown", trust_level=0.5
        )
        decision = engine.evaluate(request)
        assert "no policy rule matched" in decision.reason.lower()

    def test_fallback_has_next_step(self, engine):
        request = PolicyRequest(
            actor_id="x", role="unknown", scope="unknown", action="unknown", trust_level=0.5
        )
        assert engine.evaluate(request).suggested_next_step is not None


# ---------------------------------------------------------------------------
# Context matching
# ---------------------------------------------------------------------------

class TestContextMatching:

    def test_context_match_allows(self):
        engine = PolicyEngine(rules=[
            PolicyRule(
                name="approved-read",
                effect=PolicyEffect.ALLOW,
                roles=["member"],
                scopes=["project"],
                actions=["read"],
                min_trust_level=0.1,
                context_matcher=lambda ctx: ctx.get("approved") is True,
                reason="Approved project reads allowed.",
            )
        ])
        allowed = PolicyRequest(
            actor_id="u1", role="member", scope="project", action="read",
            trust_level=0.9, context={"approved": True}
        )
        denied = PolicyRequest(
            actor_id="u2", role="member", scope="project", action="read",
            trust_level=0.9, context={"approved": False}
        )
        assert engine.evaluate(allowed).effect == PolicyEffect.ALLOW
        assert engine.evaluate(denied).effect == PolicyEffect.DENY


# ---------------------------------------------------------------------------
# Rule management
# ---------------------------------------------------------------------------

class TestRuleManagement:

    def test_add_rule(self):
        engine = PolicyEngine()
        rule = PolicyRule(name="test", effect=PolicyEffect.ALLOW)
        engine.add_rule(rule)
        assert len(engine.rules) == 1

    def test_remove_existing_rule(self):
        engine = PolicyEngine()
        rule = PolicyRule(name="test", effect=PolicyEffect.ALLOW)
        engine.add_rule(rule)
        removed = engine.remove_rule("test")
        assert removed is True
        assert len(engine.rules) == 0

    def test_remove_nonexistent_rule(self):
        engine = PolicyEngine()
        assert engine.remove_rule("nonexistent") is False


# ---------------------------------------------------------------------------
# Bulk evaluation
# ---------------------------------------------------------------------------

class TestBulkEvaluation:

    def test_evaluate_all_returns_one_decision_per_request(self, engine):
        requests = [
            PolicyRequest(actor_id="a", role="admin", scope="admin", action="read", trust_level=0.9),
            PolicyRequest(actor_id="b", role="guest", scope="admin", action="write", trust_level=0.2),
            PolicyRequest(actor_id="c", role="member", scope="sensitive", action="write", trust_level=0.8),
        ]
        decisions = engine.evaluate_all(requests)
        assert len(decisions) == 3
        assert decisions[0].effect == PolicyEffect.ALLOW
        assert decisions[1].effect == PolicyEffect.DENY
        assert decisions[2].effect == PolicyEffect.ESCALATE


# ---------------------------------------------------------------------------
# to_dict export
# ---------------------------------------------------------------------------

class TestDecisionExport:

    def test_to_dict_contains_required_keys(self, engine, admin_read_request):
        decision = engine.evaluate(admin_read_request)
        d = decision.to_dict()
        for key in ["effect", "reason", "matched_rule", "actor_id", "role", "scope", "action", "trust_level"]:
            assert key in d

    def test_to_dict_effect_is_string(self, engine, admin_read_request):
        decision = engine.evaluate(admin_read_request)
        assert isinstance(decision.to_dict()["effect"], str)
