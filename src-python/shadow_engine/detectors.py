"""
Shadow Engine — Pattern & Contradiction Detectors  (Issue #67)

All detectors are PURE functions — they take plain Python data and return
results.  No I/O, no DB calls.  The ShadowEngine orchestrates I/O.

Detectors
---------
1. RecurringThemeDetector    — NLP clustering across journal history
2. BehavioralLoopDetector    — action sequence repetition (goal → avoid → abandon)
3. ContradictionDetector     — stated values vs. actual behavior
4. ArchetypeClassifier       — ArcTrend → ShadowArchetype + intensity
"""

from __future__ import annotations

import re
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import List, Optional

from .types import (
    ShadowArchetype,
    ShadowObservation,
    ObservationFeedback,
    ValuesBehaviorGap,          # was missing — caused F821 crash (Issue #279)
)


# ───────────────────────────────────────────────
# Shared helpers
# ───────────────────────────────────────────────

def _new_id() -> str:
    return str(uuid.uuid4())


def _now_ms() -> int:
    return int(time.time() * 1000)


# Stop-words for simple keyword extraction (no external deps required)
_STOP = frozenset(
    "i me my myself we our you your he she it its they them the a an and "
    "or but in on at to for of with is was are were be been being have has "
    "had do does did will would could should may might shall not no just "
    "so very even though although because if then that this these those "
    "what when where who which how all any some more most other same such "
    "than too very can also like".split()
)


def _keywords(text: str, top_n: int = 8) -> List[str]:
    """Extract top-N keywords from text using simple frequency heuristic."""
    words = re.findall(r"[a-z]+", text.lower())
    freq = Counter(w for w in words if w not in _STOP and len(w) > 3)
    return [w for w, _ in freq.most_common(top_n)]


# ───────────────────────────────────────────────
# 1. RecurringThemeDetector
# ───────────────────────────────────────────────

@dataclass
class ThemeCluster:
    keyword        : str
    episode_ids    : List[str]
    frequency      : int
    mean_valence   : float   # average emotional tone of episodes mentioning this theme


class RecurringThemeDetector:
    """
    Identifies recurring themes across a corpus of episode previews.

    Algorithm:
    1. Extract top-N keywords from each episode preview.
    2. Count keyword frequency across all episodes.
    3. Return ThemeClusters whose frequency >= min_frequency.
    4. Attach mean valence (from biometric_history affect_valence rows) to
       surface themes that are emotionally significant, not just frequent.

    TODO: replace keyword heuristic with sentence-transformer clustering
          once SBERT backend is wired.
    """

    def __init__(self, min_frequency: int = 3, top_themes: int = 5) -> None:
        self.min_frequency = min_frequency
        self.top_themes = top_themes

    def detect(
        self,
        episodes: List[dict],        # [{id, preview, valence}]  (valence may be 0 if unknown)
        principal_id: str,
    ) -> List[ThemeCluster]:
        """
        Args:
            episodes: list of dicts with keys: id (str), preview (str), valence (float 0-1)
        Returns:
            List of ThemeCluster sorted by frequency DESC.
        """
        keyword_to_eps: dict[str, list[str]] = {}
        keyword_to_valences: dict[str, list[float]] = {}

        for ep in episodes:
            kws = _keywords(ep.get("preview", ""))
            for kw in kws:
                keyword_to_eps.setdefault(kw, []).append(ep["id"])
                keyword_to_valences.setdefault(kw, []).append(ep.get("valence", 0.0))

        clusters = []
        for kw, ep_ids in keyword_to_eps.items():
            if len(ep_ids) < self.min_frequency:
                continue
            valences = keyword_to_valences[kw]
            clusters.append(ThemeCluster(
                keyword=kw,
                episode_ids=list(dict.fromkeys(ep_ids)),  # dedup, preserve order
                frequency=len(ep_ids),
                mean_valence=round(mean(valences), 4),
            ))

        clusters.sort(key=lambda c: c.frequency, reverse=True)
        return clusters[:self.top_themes]


# ───────────────────────────────────────────────
# 2. BehavioralLoopDetector
# ───────────────────────────────────────────────

# Known loop signatures:  ordered list of tag tokens that must appear
# in sequence across consecutive decision/event episodes.
_LOOP_SIGNATURES: list[dict] = [
    {
        "name"       : "goal_avoidance_loop",
        "tokens"     : ["goal", "avoid", "abandon"],
        "archetype"  : ShadowArchetype.WANDERER,
        "description": (
            "It looks like there's a recurring pattern: you set a goal, "
            "then find reasons to delay, and eventually let it go — "
            "often before giving it a real chance."
        ),
    },
    {
        "name"       : "conflict_withdrawal_loop",
        "tokens"     : ["conflict", "withdraw"],
        "archetype"  : ShadowArchetype.ORPHAN,
        "description": (
            "It looks like when tension arises, you tend to pull back "
            "rather than stay present with what's difficult."
        ),
    },
    {
        "name"       : "overcommit_collapse_loop",
        "tokens"     : ["commit", "overwhelm", "collapse"],
        "archetype"  : ShadowArchetype.MARTYR,
        "description": (
            "There seems to be a cycle of taking on too much, "
            "feeling overwhelmed, and then losing momentum entirely."
        ),
    },
    {
        "name"       : "anger_regret_loop",
        "tokens"     : ["anger", "regret"],
        "archetype"  : ShadowArchetype.DESTROYER,
        "description": (
            "It looks like intense reactions are sometimes followed "
            "by regret — a pattern that might be worth exploring."
        ),
    },
]


class BehavioralLoopDetector:
    """
    Detects repeating action sequences across episode decision/event logs.

    Uses tag-token matching: each episode's tags and preview keywords are
    checked against loop signature token sequences.  A loop is confirmed
    when all tokens in a signature appear in at least `min_occurrences`
    episodes within the analysis window.

    This is intentionally simple for v1 — designed to be replaced by a
    temporal sequence model (HMM or LSTM) in v2.
    """

    def __init__(self, min_occurrences: int = 2) -> None:
        self.min_occurrences = min_occurrences

    def detect(
        self,
        episodes: List[dict],   # [{id, tags, preview}]
        principal_id: str,
    ) -> List[ShadowObservation]:
        """
        Returns a ShadowObservation for each confirmed loop signature.
        Confidence is proportional to occurrence count.
        """
        now = _now_ms()
        results = []

        for sig in _LOOP_SIGNATURES:
            token_hits: dict[str, list[str]] = {t: [] for t in sig["tokens"]}

            for ep in episodes:
                combined = " ".join(ep.get("tags", []) + _keywords(ep.get("preview", "")))
                for token in sig["tokens"]:
                    if token in combined:
                        token_hits[token].append(ep["id"])

            min_hit = min(len(v) for v in token_hits.values())
            if min_hit < self.min_occurrences:
                continue

            supporting = list({eid for ids in token_hits.values() for eid in ids})
            confidence = min(1.0, round(min_hit / 5.0, 3))   # saturates at 5 occurrences

            results.append(ShadowObservation(
                id=_new_id(),
                principal_id=principal_id,
                pattern_type="behavioral_loop",
                archetype=sig["archetype"],
                description_neutral=sig["description"],
                supporting_episodes=supporting,
                first_detected_at=now,
                times_observed=min_hit,
                surfaced_at=None,
                confidence=confidence,
            ))

        return results


# ───────────────────────────────────────────────
# 3. ContradictionDetector
# ───────────────────────────────────────────────

# Contradiction value↔behavior keyword pairs.
# key = canonical value label, value = list of behaviorally-opposing keywords
_VALUE_OPPOSITES: dict[str, list[str]] = {
    "health"      : ["avoid", "skip", "tired", "sedentary", "junk"],
    "family"      : ["cancel", "ignore", "busy", "postpone", "missed"],
    "creativity"  : ["procrastinate", "blocked", "stuck", "abandoned", "unfinished"],
    "focus"       : ["distracted", "scattered", "scrolling", "unfocused", "derailed"],
    "connection"  : ["isolated", "withdrawn", "cancelled", "avoided", "silent"],
    "growth"      : ["comfort", "stagnant", "avoided", "safe", "unchanged"],
    "courage"     : ["avoidance", "fear", "backed", "withdrew", "excuses"],
    "presence"    : ["distracted", "phone", "absent", "elsewhere", "detached"],
    "authenticity": ["performed", "pretended", "masked", "fake", "hidden"],
    "service"     : ["selfish", "refused", "ignored", "neglected", "withheld"],
}


class ContradictionDetector:
    """
    Detects when stated values diverge from actual behavior.

    Algorithm:
    1. For each stated value, look up its behavioral opposites.
    2. Scan recent episode previews + tags for those opposing keywords.
    3. If opposing keywords appear in >= min_evidence episodes, raise a contradiction.
    4. gap_score = min(1.0, evidence_count / gap_saturation)
    """

    def __init__(
        self,
        min_evidence    : int   = 2,
        gap_saturation  : int   = 5,
    ) -> None:
        self.min_evidence   = min_evidence
        self.gap_saturation = gap_saturation

    def detect(
        self,
        stated_values : List[str],   # canonical value labels (lowercase)
        episodes      : List[dict],  # [{id, preview, tags}]
        principal_id  : str,
    ) -> tuple[List[ShadowObservation], Optional[ValuesBehaviorGap]]:
        """
        Returns:
            observations — one ShadowObservation per detected contradiction
            gap           — ValuesBehaviorGap summary (or None if no values stated)
        """
        now = _now_ms()
        observations: list[ShadowObservation] = []
        value_gap_scores: dict[str, float] = {}

        for value in stated_values:
            opposites = _VALUE_OPPOSITES.get(value.lower(), [])
            if not opposites:
                value_gap_scores[value] = 0.0
                continue

            evidence_eps: list[str] = []
            for ep in episodes:
                combined = " ".join(
                    ep.get("tags", []) + [ep.get("preview", "").lower()]
                )
                if any(opp in combined for opp in opposites):
                    evidence_eps.append(ep["id"])

            gap_score = min(1.0, len(evidence_eps) / self.gap_saturation)
            value_gap_scores[value] = gap_score

            if len(evidence_eps) < self.min_evidence:
                continue

            observations.append(ShadowObservation(
                id=_new_id(),
                principal_id=principal_id,
                pattern_type="contradiction",
                archetype=ShadowArchetype.NONE,
                description_neutral=(
                    f"It looks like you value {value}, yet this week's actions "
                    f"seem to pull in a different direction. "
                    f"This might be worth sitting with."
                ),
                supporting_episodes=evidence_eps,
                first_detected_at=now,
                times_observed=len(evidence_eps),
                surfaced_at=None,
                confidence=round(gap_score, 3),
            ))

        # Build ValuesBehaviorGap summary
        gap_obj: Optional[ValuesBehaviorGap] = None
        if value_gap_scores:
            most_aligned  = min(value_gap_scores, key=value_gap_scores.get)
            least_aligned = max(value_gap_scores, key=value_gap_scores.get)
            overall_gap   = round(mean(value_gap_scores.values()), 4)
            all_eps = list({eid for obs in observations for eid in obs.supporting_episodes})
            gap_obj = ValuesBehaviorGap(
                principal_id=principal_id,
                week_start_ms=now,
                most_aligned_value=most_aligned,
                least_aligned_value=least_aligned,
                gap_score=overall_gap,
                episode_ids=all_eps,
                computed_at=now,
                per_value_scores=value_gap_scores,
            )

        return observations, gap_obj


# ───────────────────────────────────────────────
# 4. ArchetypeClassifier
# ───────────────────────────────────────────────

@dataclass
class ArchetypeResult:
    archetype            : ShadowArchetype
    intensity            : float             # 0.0 – 1.0
    recommended_practice : str


# Recommended practices per archetype
_ARCHETYPE_PRACTICES: dict[ShadowArchetype, str] = {
    ShadowArchetype.NONE           : "Continue as you are. No active shadow pattern detected.",
    ShadowArchetype.ORPHAN         : "Inner child work: write a letter to the part of you that feels abandoned.",
    ShadowArchetype.MARTYR         : "Boundary exploration: identify one situation where you give beyond what's healthy.",
    ShadowArchetype.WANDERER       : "Grounding ritual: commit to one small, completable goal today.",
    ShadowArchetype.DESTROYER      : "Transmutation: channel today's intensity into physical movement or creation.",
    ShadowArchetype.WOUNDED_HEALER : "Integration: acknowledge that your wound is also your gift.",
    ShadowArchetype.SABOTEUR       : "Witness work: notice when you undermine yourself before it happens.",
}


class ArchetypeClassifier:
    """
    Maps ArcTrend fields to a ShadowArchetype and intensity score.

    ArcTrend → Archetype mapping
    ----------------------------
    dominant_emotion == sadness OR grief + low_energy_flag  → ORPHAN
    low_energy_flag + martyr_keywords in episodes           → MARTYR
    is_volatile + mood_momentum < -0.2                      → WANDERER
    dominant_emotion == anger + arousal high                → DESTROYER
    dominant_emotion == sadness + empathy keywords          → WOUNDED_HEALER
    """

    def classify(self, arc_trend: dict, episode_keywords: List[str]) -> ArchetypeResult:
        """
        Args:
            arc_trend        — dict with keys matching ArcTrend fields
                               (dominant_emotion, is_volatile, low_energy_flag,
                                mood_momentum, valence_trend, arc_stability)
            episode_keywords — flat list of keywords from recent episodes

        Returns:
            ArchetypeResult with archetype, intensity, and recommended_practice
        """
        emotion    = arc_trend.get("dominant_emotion", "neutral")
        volatile   = arc_trend.get("is_volatile", False)
        low_energy = arc_trend.get("low_energy_flag", False)
        momentum   = arc_trend.get("mood_momentum", 0.0)
        val_trend  = arc_trend.get("valence_trend", 0.0)
        stability  = arc_trend.get("arc_stability", 1.0)

        kw_set = set(episode_keywords)

        archetype = ShadowArchetype.NONE
        intensity = 0.0

        if emotion == "anger" and arc_trend.get("arousal", 0.5) >= 0.6:
            archetype = ShadowArchetype.DESTROYER
            intensity = min(1.0, 0.5 + abs(momentum) * 0.5)

        elif emotion in ("sadness", "grief") and kw_set & {"help", "care", "heal", "support", "empathy"}:
            archetype = ShadowArchetype.WOUNDED_HEALER
            intensity = min(1.0, 0.4 + (1.0 - stability) * 0.6)

        elif emotion in ("sadness", "grief") and low_energy:
            archetype = ShadowArchetype.ORPHAN
            intensity = min(1.0, 0.3 + (1.0 - stability) * 0.7)

        elif low_energy and kw_set & {"sacrifice", "martyr", "burden", "give", "selfless", "exhausted"}:
            archetype = ShadowArchetype.MARTYR
            intensity = min(1.0, 0.4 + (1.0 - stability) * 0.6)

        elif volatile and momentum < -0.2:
            archetype = ShadowArchetype.WANDERER
            intensity = min(1.0, 0.3 + abs(momentum) * 0.7)

        # Boost intensity for sustained negative valence trend
        if val_trend < -0.3 and archetype != ShadowArchetype.NONE:
            intensity = min(1.0, intensity + 0.15)

        practice = _ARCHETYPE_PRACTICES[archetype]
        return ArchetypeResult(
            archetype=archetype,
            intensity=round(intensity, 4),
            recommended_practice=practice,
        )
