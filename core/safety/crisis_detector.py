"""CrisisDetector — acute crisis signal detection for GAIA-OS.

Detects immediate safety concerns in user messages using keyword/pattern
matching as a fast first-pass filter. Designed to be fast and high-recall
(prefer false positives over false negatives for crisis signals).

Canon Ref: C01 (Sovereignty), C30 (No silent failures)
"""

from __future__ import annotations

import re
from typing import Optional

from .types import CrisisSignal, CrisisType

# High-signal crisis indicators — ordered by severity
_SUICIDE_PATTERNS = [
    r"\bkill\s+myself\b",
    r"\bend\s+my\s+life\b",
    r"\bwant\s+to\s+die\b",
    r"\bsuicid",
    r"\bself[\s-]?harm\b",
    r"\bcut\s+myself\b",
    r"\bhurt\s+myself\b",
    r"\bnot\s+want\s+to\s+be\s+alive\b",
    r"\bno\s+reason\s+to\s+live\b",
]

_CRISIS_PATTERNS = [
    r"\bemergency\b",
    r"\bhelp\s+me\b",
    r"\bcrisis\b",
    r"\bdesperate\b",
    r"\bhopeless\b",
    r"\bcan't\s+go\s+on\b",
    r"\bgiving\s+up\b",
]

_COMPILED_SUICIDE = [re.compile(p, re.IGNORECASE) for p in _SUICIDE_PATTERNS]
_COMPILED_CRISIS = [re.compile(p, re.IGNORECASE) for p in _CRISIS_PATTERNS]


class CrisisDetector:
    """Fast keyword/pattern-based crisis signal detector."""

    def evaluate(self, text: str) -> Optional[CrisisSignal]:
        """Evaluate text for crisis signals. Returns CrisisSignal or None."""
        if not text or not text.strip():
            return None

        # Check high-severity suicide/self-harm patterns first
        for pattern in _COMPILED_SUICIDE:
            if pattern.search(text):
                return CrisisSignal(
                    crisis_type=CrisisType.SUICIDE_SELF_HARM,
                    confidence=0.95,
                    requires_immediate_response=True,
                    matched_pattern=pattern.pattern,
                )

        # Check general crisis patterns
        matches = [p for p in _COMPILED_CRISIS if p.search(text)]
        if len(matches) >= 2:  # Require 2+ crisis signals to reduce false positives
            return CrisisSignal(
                crisis_type=CrisisType.GENERAL_CRISIS,
                confidence=0.75,
                requires_immediate_response=False,
                matched_pattern="|".join(m.pattern for m in matches),
            )

        return None
