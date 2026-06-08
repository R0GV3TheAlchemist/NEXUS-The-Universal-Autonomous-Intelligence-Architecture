"""
Tests for DisagreementProtocol — GAIAN pushback and constitutional blocking.
"""

from core.gaian.disagreement_protocol import (
    DisagreementProtocol,
    DisagreementTier,
)


def test_no_concern_returns_none():
    dp = DisagreementProtocol(gaian_id="g-001", human_id="h-001")
    result = dp.evaluate("Tell me a recipe", {})
    assert result is None


def test_constitutional_breach_blocks():
    dp = DisagreementProtocol(gaian_id="g-001", human_id="h-001")
    record = dp.evaluate("Do something harmful", {}, constitutional_tier=1)
    assert record is not None
    assert record.tier == DisagreementTier.CONSTITUTIONAL_BLOCK
    assert record.action_blocked is True
    assert dp.has_pending_block() is True


def test_wellbeing_risk_high_severity_formal_dissent():
    dp = DisagreementProtocol(gaian_id="g-001", human_id="h-001")
    record = dp.evaluate(
        "Some risky action",
        {"wellbeing_risk": True, "risk_severity": 0.9},
    )
    assert record.tier == DisagreementTier.FORMAL_DISSENT


def test_acknowledge_clears_block():
    dp = DisagreementProtocol(gaian_id="g-001", human_id="h-001")
    record = dp.evaluate("Override me", {}, constitutional_tier=2)
    assert dp.has_pending_block() is True
    dp.acknowledge(record.record_id, override=True, rationale="Human sovereign decision")
    assert dp.has_pending_block() is False


def test_override_rate_calculation():
    dp = DisagreementProtocol(gaian_id="g-001", human_id="h-001")
    r1 = dp.evaluate("action 1", {}, constitutional_tier=1)
    r2 = dp.evaluate("action 2", {"wellbeing_risk": True, "risk_severity": 0.9})
    dp.acknowledge(r1.record_id, override=True)
    dp.acknowledge(r2.record_id, override=False)
    rate = dp.override_rate()
    assert rate == 0.5
