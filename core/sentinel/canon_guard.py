"""
core/sentinel/canon_guard.py

Runtime enforcement of C-SENTINEL — The Sovereign Loyalty Canon.
Every Sentinel action passes through CanonGuard before execution.

Canon Reference: canon/C-SENTINEL.md
Issue:          #202
Version:        1.0.0
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class CanonVerdict(Enum):
    """The three possible outcomes of a CanonGuard check."""
    ALLOWED   = "allowed"
    BLOCKED   = "blocked"
    ESCALATE  = "escalate"


class HarmClassification(Enum):
    """
    Known harm types. Actions carrying any of these classifications
    are blocked under Article 6 — Harm Prevention.
    """
    SELF_HARM_FACILITATION     = "self_harm_facilitation"
    FINANCIAL_HARM             = "financial_harm"
    PSYCHOLOGICAL_MANIPULATION = "psychological_manipulation"
    DATA_EXFILTRATION          = "data_exfiltration"
    DEPENDENCY_CREATION        = "dependency_creation"
    TRUTH_SUPPRESSION          = "truth_suppression"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class CanonCheckResult:
    """
    The full result of a CanonGuard check.

    Attributes:
        verdict:                    ALLOWED, BLOCKED, or ESCALATE.
        article:                    The Article that triggered the ruling, if any.
        reason:                     Human-readable explanation.
        suggested_alternative:      What the Sentinel should do instead, if blocked.
        requires_gaian_notification: Whether the Gaian must be informed of this ruling.
    """
    verdict:                     CanonVerdict
    reason:                      str
    article:                     Optional[str]  = None
    suggested_alternative:       Optional[str]  = None
    requires_gaian_notification: bool           = False


@dataclass
class SentinelAction:
    """
    A structured representation of an action a Sentinel intends to take.
    All fields default to the safest possible value.

    Attributes:
        action_type:              A string identifier for the action.
        harm_classification:      The harm class this action carries, if any.
        contains_fabrication:     True if the action involves invented facts.
        withholds_critical_info:  True if the action deliberately omits key information.
        shares_gaian_data:        True if the action would transmit Gaian data externally.
        gaian_consent_granted:    True if the Gaian has explicitly consented.
        dependency_pattern_score: Float 0.0-1.0 measuring autonomy-reduction risk.
        metadata:                 Arbitrary extra context (non-canonical).
    """
    action_type:              str
    harm_classification:      Optional[str]  = None
    contains_fabrication:     bool           = False
    withholds_critical_info:  bool           = False
    shares_gaian_data:        bool           = False
    gaian_consent_granted:    bool           = False
    dependency_pattern_score: float          = 0.0
    metadata:                 dict           = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Loyalty Hash
# ---------------------------------------------------------------------------

def compute_loyalty_hash(canon_version: str, canon_content: str) -> str:
    """
    Generate an immutable cryptographic commitment to a specific C-SENTINEL version.

    Stored in SentinelIdentityRecord at initialization.
    Verified at every session start.
    A mismatch means the canon was altered after the Sentinel was bound.

    Args:
        canon_version:  Semantic version string, e.g. "1.0.0".
        canon_content:  Full text content of canon/C-SENTINEL.md.

    Returns:
        A hex-encoded SHA-256 digest of the canon commitment payload.
    """
    payload = json.dumps(
        {
            "canon": "C-SENTINEL",
            "version": canon_version,
            "content_hash": hashlib.sha256(canon_content.encode("utf-8")).hexdigest(),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_loyalty_hash(sentinel_hash: str, canon_version: str, canon_content: str) -> bool:
    """
    Verify that a Sentinel's stored loyalty hash matches the current canon.

    Returns:
        True if the hash matches; False if the canon was altered after binding.
    """
    return sentinel_hash == compute_loyalty_hash(canon_version, canon_content)


# ---------------------------------------------------------------------------
# CanonGuard
# Article Priority Order:
#   1. Article 6 - Harm Prevention           (highest)
#   2. Article 3 - Honest Service
#   3. Article 1 - Primary Loyalty
#   4. Article 4 - Memory Sovereignty
#   5. Articles 2, 5, 7, 8                   (contextual)
# ---------------------------------------------------------------------------

class CanonGuard:
    """
    Runtime enforcement of C-SENTINEL — The Sovereign Loyalty Canon.

    Every Sentinel action MUST pass through check_action() before execution.
    All violations are emitted as WARNING logs and must be forwarded to the
    Observability & Audit Layer (Issue #222).
    """

    DEPENDENCY_ESCALATION_THRESHOLD: float = 0.75

    def __init__(self, sentinel_id: str) -> None:
        self.sentinel_id = sentinel_id

    def check_action(self, action: SentinelAction) -> CanonCheckResult:
        """
        Run a proposed Sentinel action through all Article checks in priority order.
        Returns ALLOWED, BLOCKED, or ESCALATE with full reasoning.
        """
        # Article 6: Harm Prevention (highest priority)
        result = self._check_article_6(action)
        if result is not None:
            self._log_violation(result, action)
            return result

        # Article 3: Honest Service
        result = self._check_article_3(action)
        if result is not None:
            self._log_violation(result, action)
            return result

        # Article 4: Memory Sovereignty
        result = self._check_article_4(action)
        if result is not None:
            self._log_violation(result, action)
            return result

        # Article 5: Growth Fidelity
        result = self._check_article_5(action)
        if result is not None:
            self._log_violation(result, action)
            return result

        return CanonCheckResult(
            verdict=CanonVerdict.ALLOWED,
            reason="Action passes all C-SENTINEL checks.",
        )

    def _check_article_6(self, action: SentinelAction) -> Optional[CanonCheckResult]:
        """Article 6 - Harm Prevention."""
        harmful_classifications = {hc.value for hc in HarmClassification}
        if action.harm_classification in harmful_classifications:
            if action.harm_classification == HarmClassification.SELF_HARM_FACILITATION.value:
                return CanonCheckResult(
                    verdict=CanonVerdict.ESCALATE,
                    article="Article 6 - Harm Prevention",
                    reason=(
                        f"Action '{action.action_type}' classified as "
                        f"'{action.harm_classification}'. Activating crisis protocol."
                    ),
                    suggested_alternative=(
                        "Activate Crisis Mode (Issue #168). Offer support resources. "
                        "Engage emergency contact if consent exists."
                    ),
                    requires_gaian_notification=True,
                )
            return CanonCheckResult(
                verdict=CanonVerdict.BLOCKED,
                article="Article 6 - Harm Prevention",
                reason=(
                    f"Action '{action.action_type}' classified as "
                    f"'{action.harm_classification}'."
                ),
                suggested_alternative=(
                    "Offer a gentle challenge. Name the concern. "
                    "Refuse the action and explain why."
                ),
                requires_gaian_notification=True,
            )
        return None

    def _check_article_3(self, action: SentinelAction) -> Optional[CanonCheckResult]:
        """Article 3 - Honest Service."""
        if action.contains_fabrication:
            return CanonCheckResult(
                verdict=CanonVerdict.BLOCKED,
                article="Article 3 - Honest Service",
                reason=f"Action '{action.action_type}' contains fabricated information.",
                suggested_alternative=(
                    "Say 'I don't know' rather than fabricate. "
                    "Deliver truth with appropriate gentleness."
                ),
                requires_gaian_notification=False,
            )
        if action.withholds_critical_info:
            return CanonCheckResult(
                verdict=CanonVerdict.BLOCKED,
                article="Article 3 - Honest Service",
                reason=(
                    f"Action '{action.action_type}' withholds information "
                    "the Gaian needs."
                ),
                suggested_alternative=(
                    "Disclose the information. Choose timing and framing carefully "
                    "but do not alter factual content."
                ),
                requires_gaian_notification=False,
            )
        return None

    def _check_article_4(self, action: SentinelAction) -> Optional[CanonCheckResult]:
        """Article 4 - Memory Sovereignty."""
        if action.shares_gaian_data and not action.gaian_consent_granted:
            return CanonCheckResult(
                verdict=CanonVerdict.BLOCKED,
                article="Article 4 - Memory Sovereignty",
                reason=(
                    f"Action '{action.action_type}' would share Gaian data "
                    "without explicit consent."
                ),
                suggested_alternative=(
                    "Request explicit, informed consent before proceeding. "
                    "Explain exactly what data would be shared and with whom."
                ),
                requires_gaian_notification=True,
            )
        return None

    def _check_article_5(self, action: SentinelAction) -> Optional[CanonCheckResult]:
        """Article 5 - Growth Fidelity."""
        if action.dependency_pattern_score >= self.DEPENDENCY_ESCALATION_THRESHOLD:
            return CanonCheckResult(
                verdict=CanonVerdict.ESCALATE,
                article="Article 5 - Growth Fidelity",
                reason=(
                    f"Dependency pattern score {action.dependency_pattern_score:.2f} "
                    f"exceeds threshold {self.DEPENDENCY_ESCALATION_THRESHOLD}. "
                    "The Sentinel may be substituting for Gaian judgment."
                ),
                suggested_alternative=(
                    "Name the pattern directly: 'I've been making this decision for you. "
                    "Would you like to reclaim it?' Offer options, not directives."
                ),
                requires_gaian_notification=True,
            )
        return None

    def _log_violation(self, result: CanonCheckResult, action: SentinelAction) -> None:
        logger.warning(
            "[CanonGuard] sentinel=%s action=%s verdict=%s article=%s reason=%s",
            self.sentinel_id,
            action.action_type,
            result.verdict.value,
            result.article,
            result.reason,
        )
