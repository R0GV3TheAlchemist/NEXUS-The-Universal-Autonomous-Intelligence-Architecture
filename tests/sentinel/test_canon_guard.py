"""
tests/sentinel/test_canon_guard.py

Full test suite for C-SENTINEL enforcement via CanonGuard.
Every Article has at least one blocked and one allowed test.

Canon Reference: canon/C-SENTINEL.md
Issue:           #202
"""

import pytest

from core.sentinel.canon_guard import (
    CanonCheckResult,
    CanonGuard,
    CanonVerdict,
    HarmClassification,
    SentinelAction,
    compute_loyalty_hash,
    verify_loyalty_hash,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def guard() -> CanonGuard:
    return CanonGuard(sentinel_id="test-sentinel-001")


@pytest.fixture
def clean_action() -> SentinelAction:
    """A completely safe action - passes all Articles."""
    return SentinelAction(action_type="respond")


# ---------------------------------------------------------------------------
# Loyalty Hash
# ---------------------------------------------------------------------------

class TestLoyaltyHash:

    def test_hash_is_deterministic(self):
        h1 = compute_loyalty_hash("1.0.0", "canon content")
        h2 = compute_loyalty_hash("1.0.0", "canon content")
        assert h1 == h2

    def test_hash_changes_with_version(self):
        h1 = compute_loyalty_hash("1.0.0", "canon content")
        h2 = compute_loyalty_hash("1.0.1", "canon content")
        assert h1 != h2

    def test_hash_changes_with_content(self):
        h1 = compute_loyalty_hash("1.0.0", "original canon")
        h2 = compute_loyalty_hash("1.0.0", "tampered canon")
        assert h1 != h2

    def test_verify_passes_on_match(self):
        content = "The Eight Articles of C-SENTINEL"
        version = "1.0.0"
        stored  = compute_loyalty_hash(version, content)
        assert verify_loyalty_hash(stored, version, content) is True

    def test_verify_fails_on_tamper(self):
        stored = compute_loyalty_hash("1.0.0", "original")
        assert verify_loyalty_hash(stored, "1.0.0", "tampered") is False

    def test_hash_is_hex_string(self):
        h = compute_loyalty_hash("1.0.0", "content")
        assert isinstance(h, str)
        assert len(h) == 64


# ---------------------------------------------------------------------------
# Article 6 - Harm Prevention
# ---------------------------------------------------------------------------

class TestArticle6HarmPrevention:

    def test_self_harm_escalates(self, guard):
        action = SentinelAction(
            action_type="respond",
            harm_classification=HarmClassification.SELF_HARM_FACILITATION.value,
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.ESCALATE
        assert result.article == "Article 6 - Harm Prevention"
        assert result.requires_gaian_notification is True

    def test_financial_harm_blocked(self, guard):
        action = SentinelAction(
            action_type="financial_advice",
            harm_classification=HarmClassification.FINANCIAL_HARM.value,
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.BLOCKED
        assert result.article == "Article 6 - Harm Prevention"
        assert result.requires_gaian_notification is True

    def test_psychological_manipulation_blocked(self, guard):
        action = SentinelAction(
            action_type="persuade",
            harm_classification=HarmClassification.PSYCHOLOGICAL_MANIPULATION.value,
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.BLOCKED

    def test_data_exfiltration_blocked(self, guard):
        action = SentinelAction(
            action_type="sync",
            harm_classification=HarmClassification.DATA_EXFILTRATION.value,
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.BLOCKED

    def test_dependency_creation_blocked(self, guard):
        action = SentinelAction(
            action_type="decide",
            harm_classification=HarmClassification.DEPENDENCY_CREATION.value,
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.BLOCKED

    def test_truth_suppression_blocked(self, guard):
        action = SentinelAction(
            action_type="summarise",
            harm_classification=HarmClassification.TRUTH_SUPPRESSION.value,
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.BLOCKED

    def test_no_harm_classification_passes(self, guard, clean_action):
        result = guard.check_action(clean_action)
        assert result.verdict == CanonVerdict.ALLOWED

    def test_unknown_harm_classification_passes(self, guard):
        action = SentinelAction(
            action_type="respond",
            harm_classification="unrecognised_type",
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.ALLOWED

    def test_suggested_alternative_present_when_blocked(self, guard):
        action = SentinelAction(
            action_type="respond",
            harm_classification=HarmClassification.FINANCIAL_HARM.value,
        )
        result = guard.check_action(action)
        assert result.suggested_alternative is not None
        assert len(result.suggested_alternative) > 0


# ---------------------------------------------------------------------------
# Article 3 - Honest Service
# ---------------------------------------------------------------------------

class TestArticle3HonestService:

    def test_fabrication_blocked(self, guard):
        action = SentinelAction(action_type="respond", contains_fabrication=True)
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.BLOCKED
        assert result.article == "Article 3 - Honest Service"

    def test_withholding_critical_info_blocked(self, guard):
        action = SentinelAction(action_type="summarise", withholds_critical_info=True)
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.BLOCKED
        assert result.article == "Article 3 - Honest Service"

    def test_honest_action_passes(self, guard, clean_action):
        result = guard.check_action(clean_action)
        assert result.verdict == CanonVerdict.ALLOWED

    def test_fabrication_not_gaian_notified(self, guard):
        action = SentinelAction(action_type="respond", contains_fabrication=True)
        result = guard.check_action(action)
        assert result.requires_gaian_notification is False

    def test_article_6_takes_priority_over_article_3(self, guard):
        action = SentinelAction(
            action_type="respond",
            harm_classification=HarmClassification.FINANCIAL_HARM.value,
            contains_fabrication=True,
        )
        result = guard.check_action(action)
        assert result.article == "Article 6 - Harm Prevention"


# ---------------------------------------------------------------------------
# Article 4 - Memory Sovereignty
# ---------------------------------------------------------------------------

class TestArticle4MemorySovereignty:

    def test_sharing_without_consent_blocked(self, guard):
        action = SentinelAction(
            action_type="sync_to_cloud",
            shares_gaian_data=True,
            gaian_consent_granted=False,
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.BLOCKED
        assert result.article == "Article 4 - Memory Sovereignty"
        assert result.requires_gaian_notification is True

    def test_sharing_with_consent_allowed(self, guard):
        action = SentinelAction(
            action_type="sync_to_cloud",
            shares_gaian_data=True,
            gaian_consent_granted=True,
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.ALLOWED

    def test_no_sharing_allowed(self, guard, clean_action):
        result = guard.check_action(clean_action)
        assert result.verdict == CanonVerdict.ALLOWED

    def test_article_6_takes_priority_over_article_4(self, guard):
        action = SentinelAction(
            action_type="sync",
            harm_classification=HarmClassification.DATA_EXFILTRATION.value,
            shares_gaian_data=True,
            gaian_consent_granted=False,
        )
        result = guard.check_action(action)
        assert result.article == "Article 6 - Harm Prevention"


# ---------------------------------------------------------------------------
# Article 5 - Growth Fidelity
# ---------------------------------------------------------------------------

class TestArticle5GrowthFidelity:

    def test_high_dependency_score_escalates(self, guard):
        action = SentinelAction(action_type="decide", dependency_pattern_score=0.9)
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.ESCALATE
        assert result.article == "Article 5 - Growth Fidelity"
        assert result.requires_gaian_notification is True

    def test_exact_threshold_escalates(self, guard):
        action = SentinelAction(action_type="decide", dependency_pattern_score=0.75)
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.ESCALATE

    def test_below_threshold_passes(self, guard):
        action = SentinelAction(action_type="decide", dependency_pattern_score=0.74)
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.ALLOWED

    def test_zero_dependency_passes(self, guard, clean_action):
        result = guard.check_action(clean_action)
        assert result.verdict == CanonVerdict.ALLOWED

    def test_suggested_alternative_names_pattern(self, guard):
        action = SentinelAction(action_type="decide", dependency_pattern_score=0.9)
        result = guard.check_action(action)
        assert "reclaim" in result.suggested_alternative.lower()


# ---------------------------------------------------------------------------
# Priority Ordering
# ---------------------------------------------------------------------------

class TestPriorityOrdering:

    def test_article_6_beats_article_5(self, guard):
        action = SentinelAction(
            action_type="respond",
            harm_classification=HarmClassification.DEPENDENCY_CREATION.value,
            dependency_pattern_score=0.9,
        )
        result = guard.check_action(action)
        assert result.article == "Article 6 - Harm Prevention"

    def test_article_3_beats_article_4(self, guard):
        action = SentinelAction(
            action_type="respond",
            contains_fabrication=True,
            shares_gaian_data=True,
            gaian_consent_granted=False,
        )
        result = guard.check_action(action)
        assert result.article == "Article 3 - Honest Service"

    def test_article_3_beats_article_5(self, guard):
        action = SentinelAction(
            action_type="respond",
            contains_fabrication=True,
            dependency_pattern_score=0.9,
        )
        result = guard.check_action(action)
        assert result.article == "Article 3 - Honest Service"


# ---------------------------------------------------------------------------
# Clean Pass
# ---------------------------------------------------------------------------

class TestCleanPass:

    def test_fully_clean_action_allowed(self, guard):
        action = SentinelAction(
            action_type="respond",
            harm_classification=None,
            contains_fabrication=False,
            withholds_critical_info=False,
            shares_gaian_data=False,
            gaian_consent_granted=False,
            dependency_pattern_score=0.0,
        )
        result = guard.check_action(action)
        assert result.verdict == CanonVerdict.ALLOWED
        assert result.article is None
        assert result.suggested_alternative is None

    def test_clean_action_has_clean_reason(self, guard, clean_action):
        result = guard.check_action(clean_action)
        assert "passes" in result.reason.lower()
