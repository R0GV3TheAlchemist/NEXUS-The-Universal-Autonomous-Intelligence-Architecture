"""CrisisDetector / CumulativeCrisisDetector — acute crisis signal detection.

Provides two detectors:

CrisisDetector
    Fast keyword/pattern-based first-pass filter.  Used by safety_engine for
    per-turn triage.  High-recall: prefer false positives over misses.

CumulativeCrisisDetector
    Richer per-turn and trajectory-level classifier used by test_safety.py and
    higher-level safety components.  Combines keyword detection with
    affect-state heuristics (valence / arousal) and a linear-regression slope
    over cumulative risk scores.

Canon Ref: C01 (Sovereignty), C30 (No silent failures)
"""

from __future__ import annotations

import re
from statistics import mean
from typing import List, Optional

from .types import CrisisLevel, CrisisSignal, CrisisType

# ── Shared keyword patterns ────────────────────────────────────────────────────

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

_ACUTE_PATTERNS = [
    r"\bhopeless\b",
    r"\bcompletely\s+falling\s+apart\b",
    r"\bcan't\s+go\s+on\b",
    r"\bgiving\s+up\b",
    r"\bno\s+way\s+out\b",
    r"\bbreaking\s+down\b",
]

_MASKED_PATTERNS = [
    r"\bdoesn'?t\s+matter\b",
    r"\bwhatever\b",
    r"\bnever\s+mind\b",
    r"\bforget\s+it\b",
    r"\bwho\s+cares\b",
    r"\bfine\s+I\s+guess\b",
    r"\bI'?m\s+fine\b",
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
_COMPILED_ACUTE   = [re.compile(p, re.IGNORECASE) for p in _ACUTE_PATTERNS]
_COMPILED_MASKED  = [re.compile(p, re.IGNORECASE) for p in _MASKED_PATTERNS]
_COMPILED_CRISIS  = [re.compile(p, re.IGNORECASE) for p in _CRISIS_PATTERNS]


# ── CrisisDetector ─────────────────────────────────────────────────────────────

class CrisisDetector:
    """Fast keyword/pattern-based crisis signal detector."""

    def evaluate(self, text: str) -> Optional[CrisisSignal]:
        """Evaluate text for crisis signals. Returns CrisisSignal or None."""
        if not text or not text.strip():
            return None

        for pattern in _COMPILED_SUICIDE:
            if pattern.search(text):
                return CrisisSignal(
                    crisis_type=CrisisType.SUICIDE_SELF_HARM,
                    confidence=0.95,
                    requires_immediate_response=True,
                    matched_pattern=pattern.pattern,
                )

        matches = [p for p in _COMPILED_CRISIS if p.search(text)]
        if len(matches) >= 2:
            return CrisisSignal(
                crisis_type=CrisisType.GENERAL_CRISIS,
                confidence=0.75,
                requires_immediate_response=False,
                matched_pattern="|".join(m.pattern for m in matches),
            )

        return None


# ── CumulativeCrisisDetector ───────────────────────────────────────────────────

# Thresholds — tuned to match the test suite's boundary assertions.
_ACUTE_VALENCE_CEILING: float = -0.65   # valence <= this → ACUTE path eligible
_MASKED_AROUSAL_CEILING: float = 0.25   # arousal <= this → MASKED path eligible
_MASKED_VALENCE_FLOOR: float = -0.30    # valence < this (with low arousal) → MASKED

_TRAJ_EXPLICIT_THRESHOLD: float = 0.80
_TRAJ_ACUTE_THRESHOLD: float = 0.55
_TRAJ_GRADUAL_MIN_LATEST: float = 0.35
_TRAJ_MASKED_MIN_LATEST: float = 0.40
_GRADUAL_SLOPE_THRESHOLD: float = 0.05  # per-index slope to be called "gradual"


class CumulativeCrisisDetector:
    """
    Per-turn and trajectory-level crisis classifier.

    classify_turn(text, frame) -> CrisisLevel
        Combines keyword matching with affect-state heuristics.

    classify_trajectory(scores) -> CrisisLevel
        Classifies a sequence of cumulative risk scores using the latest
        value and a linear slope.

    _linear_slope(scores) -> float
        Ordinary-least-squares slope (Δscore / Δindex).  Public for
        test introspection.
    """

    # ── per-turn classification ──────────────────────────────────────────────

    def classify_turn(self, text: str, frame) -> CrisisLevel:  # frame: TurnRiskFrame
        """
        Returns the most severe CrisisLevel detected for a single turn.

        Priority order (highest wins):
            1. EXPLICIT  — suicide/self-harm keyword
            2. ACUTE     — acute keyword OR affect (valence ≤ ceiling, arousal > 0.5)
            3. MASKED    — masked keyword OR affect (valence < floor, arousal ≤ ceiling)
            4. NONE
        """
        lowered = (text or "").lower()

        # 1. EXPLICIT — suicide / self-harm keywords
        for pattern in _COMPILED_SUICIDE:
            if pattern.search(lowered):
                return CrisisLevel.EXPLICIT

        # 2. ACUTE — acute keywords or affect combo
        for pattern in _COMPILED_ACUTE:
            if pattern.search(lowered):
                return CrisisLevel.ACUTE

        valence: float = getattr(frame, "affect_valence", 0.0)
        arousal: float = getattr(frame, "affect_arousal", 0.5)

        if valence <= _ACUTE_VALENCE_CEILING and arousal > 0.5:
            return CrisisLevel.ACUTE

        # 3. MASKED — masked keywords or affect combo
        for pattern in _COMPILED_MASKED:
            if pattern.search(lowered):
                return CrisisLevel.MASKED

        if valence < _MASKED_VALENCE_FLOOR and arousal <= _MASKED_AROUSAL_CEILING:
            return CrisisLevel.MASKED

        return CrisisLevel.NONE

    # ── trajectory classification ────────────────────────────────────────────

    def classify_trajectory(self, scores: List[float]) -> CrisisLevel:
        """
        Classify a sequence of cumulative risk scores.

        Returns NONE for lists shorter than 2 (no trend can be computed).
        """
        if len(scores) < 2:
            return CrisisLevel.NONE

        latest = scores[-1]
        slope = self._linear_slope(scores)

        if latest >= _TRAJ_EXPLICIT_THRESHOLD:
            return CrisisLevel.EXPLICIT

        if latest >= _TRAJ_ACUTE_THRESHOLD:
            return CrisisLevel.ACUTE

        if latest >= _TRAJ_GRADUAL_MIN_LATEST and slope >= _GRADUAL_SLOPE_THRESHOLD:
            return CrisisLevel.GRADUAL

        if latest >= _TRAJ_MASKED_MIN_LATEST:
            return CrisisLevel.MASKED

        return CrisisLevel.NONE

    # ── helpers ──────────────────────────────────────────────────────────────

    def _linear_slope(self, scores: List[float]) -> float:
        """
        Ordinary-least-squares slope of *scores* vs. their index positions.

        Returns 0.0 for lists shorter than 2.
        """
        n = len(scores)
        if n < 2:
            return 0.0

        xs = list(range(n))
        x_mean = mean(xs)
        y_mean = mean(scores)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, scores))
        denominator = sum((x - x_mean) ** 2 for x in xs)

        if denominator == 0.0:
            return 0.0

        return numerator / denominator
