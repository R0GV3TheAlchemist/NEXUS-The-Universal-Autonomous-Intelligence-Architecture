"""
GAIA-OS Shadow Engine
Pillar: Magnum Opus (Pillar I)
Spec: Issue #67 / docs/knowledge/JUNGIAN_PSYCHOLOGY_SOUL_MIRROR_ENGINE_REPORT.md

The Shadow Engine is the Jungian mirror layer of GAIA-OS.
It detects recurring behavioral patterns, surfaces contradictions between
stated values and actual behavior, and gates all surfacing through
constitutional timing and affect safety checks.

Design principles:
  - Local-first: zero shadow data leaves the device
  - Non-judgmental: all observations phrased in second-person, present tense
  - Timing-aware: never surfaces during low-coherence, grief, or dissonance
  - Feedback-loop: user responses update pattern confidence scores
  - Stage-gated: full activation only at Stage 3 (Crucible)

Dependencies (all local, no external NLP):
  - collections.Counter for theme frequency
  - core.stage_bridge.is_shadow_surface_safe()
  - core.affect_inference.FeelingState
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from core.affect_inference import FeelingState
from core.stage_bridge import is_shadow_surface_safe


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum behavioral alignment rate to NOT flag a contradiction
_CONTRADICTION_THRESHOLD = 0.30

# Minimum alignment score (Schumann) to allow surfacing
_MIN_ALIGNMENT_SCORE = 30.0

# Minimum loop repetitions to flag a behavioral loop
_MIN_LOOP_REPETITIONS = 2

# Stop words excluded from theme clustering
_STOP_WORDS = {
    "i", "me", "my", "we", "the", "a", "an", "and", "or", "but",
    "in", "on", "at", "to", "for", "of", "is", "it", "was", "am",
    "are", "be", "been", "have", "has", "had", "do", "did", "not",
    "that", "this", "with", "he", "she", "they", "so", "if", "as",
    "by", "from", "up", "out", "its", "then", "than", "when", "what",
    "which", "who", "how", "all", "just", "also", "more", "very",
    "will", "would", "could", "should", "get", "got", "feel", "felt",
}

UserResponse = Literal["seen_it", "not_accurate", "this_is_important", ""]


# ---------------------------------------------------------------------------
# ShadowObservation
# ---------------------------------------------------------------------------

@dataclass
class ShadowObservation:
    """
    A single pattern or contradiction surfaced by the Shadow Engine.

    All observations are phrased in second-person, present tense,
    non-judgmental language.

    Fields:
        pattern_type        — 'theme' | 'loop' | 'contradiction'
        description_neutral — human-readable observation text
        supporting_episodes — list of episode IDs or text snippets
        first_detected      — ISO 8601 timestamp
        times_observed      — how many times this pattern appeared
        surfaced_at         — ISO 8601 timestamp when shown to user
        user_response       — user feedback: 'seen_it' | 'not_accurate' |
                              'this_is_important' | '' (not yet responded)
        confidence          — 0.0–1.0 pattern confidence (updated by feedback)
    """
    pattern_type:        Literal["theme", "loop", "contradiction"]
    description_neutral: str
    supporting_episodes: list[str]
    first_detected:      str
    times_observed:      int
    surfaced_at:         str = ""
    user_response:       UserResponse = ""
    confidence:          float = 1.0


# ---------------------------------------------------------------------------
# RecurringThemeDetector
# ---------------------------------------------------------------------------

class RecurringThemeDetector:
    """
    Detects recurring themes across a journal corpus using term frequency.

    Algorithm:
      1. Tokenize all entries, strip stop words and short tokens
      2. Count term frequency across the corpus
      3. Return top-N terms as theme observations, weighted by frequency

    No external NLP required — pure stdlib, local-first.
    """

    def detect(
        self,
        entries: list[str],
        top_n: int = 5,
        min_frequency: int = 2,
    ) -> list[ShadowObservation]:
        """
        Detect recurring themes from a list of journal entry strings.

        Args:
            entries:       List of journal entry text strings
            top_n:         Maximum number of themes to return
            min_frequency: Minimum occurrences to qualify as a theme

        Returns:
            List of ShadowObservation with pattern_type='theme'
        """
        if not entries:
            return []

        counter: Counter[str] = Counter()
        for entry in entries:
            tokens = re.findall(r"\b[a-z]{4,}\b", entry.lower())
            for token in tokens:
                if token not in _STOP_WORDS:
                    counter[token] += 1

        now = _utcnow()
        observations: list[ShadowObservation] = []

        for term, count in counter.most_common(top_n * 3):
            if count < min_frequency:
                break
            if len(observations) >= top_n:
                break

            # Find supporting entries containing this term
            supporting = [
                e[:120] for e in entries if term in e.lower()
            ][:3]

            confidence = min(1.0, count / 10.0)
            desc = (
                f"It looks like '{term}' comes up repeatedly in your reflections. "
                f"This theme has appeared {count} time{'s' if count != 1 else ''} "
                f"across your recent journal entries."
            )

            observations.append(ShadowObservation(
                pattern_type="theme",
                description_neutral=desc,
                supporting_episodes=supporting,
                first_detected=now,
                times_observed=count,
                confidence=confidence,
            ))

        return observations


# ---------------------------------------------------------------------------
# BehavioralLoopDetector
# ---------------------------------------------------------------------------

class BehavioralLoopDetector:
    """
    Detects recurring 3-step behavioral sequences (loops) in goal event logs.

    A behavioral loop is a sequence of labeled actions that repeats
    across the event history. Classic example: 'set → avoid → abandon'.

    Events are labeled strings such as:
        'set', 'start', 'avoid', 'delay', 'abandon', 'complete', 'restart'

    A loop is flagged when the same 3-event sequence appears
    MIN_LOOP_REPETITIONS (2) or more times.
    """

    def detect(
        self,
        events: list[str],
        window: int = 3,
    ) -> list[ShadowObservation]:
        """
        Detect repeating behavioral sequences in a labeled event list.

        Args:
            events: Ordered list of event labels (e.g. ['set', 'avoid', 'abandon', ...])
            window: Sequence length to match (default 3)

        Returns:
            List of ShadowObservation with pattern_type='loop'
        """
        if len(events) < window * _MIN_LOOP_REPETITIONS:
            return []

        # Count all n-gram sequences
        ngram_counts: Counter[tuple[str, ...]] = Counter()
        for i in range(len(events) - window + 1):
            ngram = tuple(events[i:i + window])
            ngram_counts[ngram] += 1

        now = _utcnow()
        observations: list[ShadowObservation] = []

        for ngram, count in ngram_counts.items():
            if count < _MIN_LOOP_REPETITIONS:
                continue

            seq_str = " → ".join(ngram)
            desc = (
                f"It looks like when you {ngram[0]}, you tend to {ngram[1]} "
                f"and then {ngram[2]}. This pattern has appeared {count} times "
                f"in your recent goal history."
            )
            confidence = min(1.0, count / 5.0)

            observations.append(ShadowObservation(
                pattern_type="loop",
                description_neutral=desc,
                supporting_episodes=[seq_str],
                first_detected=now,
                times_observed=count,
                confidence=confidence,
            ))

        return observations


# ---------------------------------------------------------------------------
# ContradictionDetector
# ---------------------------------------------------------------------------

@dataclass
class BehaviorLog:
    """
    Maps stated values to observed behavioral completion rates.

    Example:
        BehaviorLog(alignment_rates={
            "creativity": 0.75,   # 75% of creative goals completed
            "health":     0.10,   # 10% — contradiction
            "family":     0.60,
        })
    """
    alignment_rates: dict[str, float]   # value_name → 0.0-1.0 completion rate


class ContradictionDetector:
    """
    Detects contradictions between stated values and actual behavior.

    A contradiction is flagged when a user-stated value has a behavioral
    alignment rate below _CONTRADICTION_THRESHOLD (30%).

    Also computes a weekly values-behavior gap score (0.0-1.0):
        gap = mean of (1 - alignment_rate) for all stated values
    """

    def detect(
        self,
        values: list[str],
        behavior_log: BehaviorLog,
    ) -> list[ShadowObservation]:
        """
        Flag values with behavioral alignment below threshold.

        Args:
            values:       List of user-stated core values (free text)
            behavior_log: BehaviorLog mapping value names to completion rates

        Returns:
            List of ShadowObservation with pattern_type='contradiction'
        """
        if not values or not behavior_log.alignment_rates:
            return []

        now = _utcnow()
        observations: list[ShadowObservation] = []

        for value in values:
            # Normalize: match value to behavior_log key (case-insensitive)
            key = value.lower().strip()
            rate = behavior_log.alignment_rates.get(key)

            if rate is None:
                continue  # no behavioral data for this value yet

            if rate < _CONTRADICTION_THRESHOLD:
                pct = int(rate * 100)
                desc = (
                    f"You\'ve named '{value}' as a core value, but your recent "
                    f"actions reflect it about {pct}% of the time. "
                    f"There may be a gap worth exploring."
                )
                confidence = 1.0 - rate  # higher confidence when gap is wider

                observations.append(ShadowObservation(
                    pattern_type="contradiction",
                    description_neutral=desc,
                    supporting_episodes=[f"{value}: {pct}% behavioral alignment"],
                    first_detected=now,
                    times_observed=1,
                    confidence=round(confidence, 3),
                ))

        return observations

    def gap_score(self, values: list[str], behavior_log: BehaviorLog) -> float:
        """
        Compute the weekly values-behavior gap score (0.0 = perfect, 1.0 = total gap).
        """
        rates = [
            behavior_log.alignment_rates.get(v.lower().strip(), 0.5)
            for v in values
        ]
        if not rates:
            return 0.0
        return round(1.0 - (sum(rates) / len(rates)), 3)


# ---------------------------------------------------------------------------
# ShadowTimingGate
# ---------------------------------------------------------------------------

class ShadowTimingGate:
    """
    Constitutional timing gate for Shadow Engine surfacing.

    Two conditions must both pass:
      1. is_shadow_surface_safe(stage, feeling) — stage + affect gate
      2. alignment_score >= 30 — Schumann alignment minimum

    Rationale: surfacing shadow observations during low-coherence states
    (high Kp storm, grief, dissonance) or at Stage 1 violates the
    constitutional principle of non-exploitation.
    """

    def is_safe(
        self,
        stage: int,
        feeling: FeelingState,
        alignment_score: float,
    ) -> bool:
        """
        Returns True only when it is safe to surface a shadow observation.

        Args:
            stage:           Current user stage (1-5)
            feeling:         Current FeelingState from AffectInference
            alignment_score: Current Schumann alignment score (0-100)

        Returns:
            bool
        """
        affect_stage_safe = is_shadow_surface_safe(stage, feeling)
        alignment_safe = alignment_score >= _MIN_ALIGNMENT_SCORE
        return affect_stage_safe and alignment_safe


# ---------------------------------------------------------------------------
# ShadowEngine (coordinator)
# ---------------------------------------------------------------------------

class ShadowEngine:
    """
    The Shadow Engine coordinator.

    Runs all detectors, gates candidates through ShadowTimingGate,
    and returns only the observations that are safe to surface.

    User feedback ('seen_it', 'not_accurate', 'this_is_important')
    updates confidence scores on existing observations.

    All observations are local-first. Zero data leaves the device.
    """

    def __init__(self) -> None:
        self._theme_detector = RecurringThemeDetector()
        self._loop_detector = BehavioralLoopDetector()
        self._contradiction_detector = ContradictionDetector()
        self._timing_gate = ShadowTimingGate()
        # In-memory store for this session (persisted externally via Sovereign Memory)
        self._observations: list[ShadowObservation] = []

    def evaluate(
        self,
        *,
        stage: int,
        feeling: FeelingState,
        alignment_score: float,
        journal_entries: list[str],
        goal_events: list[str],
        values: list[str],
        behavior_log: BehaviorLog,
        top_n_themes: int = 3,
    ) -> list[ShadowObservation]:
        """
        Run a full Shadow Engine evaluation cycle.

        If the timing gate does not pass, returns an empty list —
        patterns are detected internally but not surfaced.

        Args:
            stage:           Current user stage
            feeling:         Current FeelingState
            alignment_score: Current Schumann alignment score
            journal_entries: List of recent journal entry strings (up to 90 days)
            goal_events:     Labeled goal event sequence
            values:          User-stated core values
            behavior_log:    BehaviorLog with alignment rates
            top_n_themes:    Max themes to detect

        Returns:
            List of ShadowObservation safe to surface (may be empty)
        """
        # Always detect — even if not surfacing (Stage 2: observe only)
        candidates: list[ShadowObservation] = []
        candidates.extend(self._theme_detector.detect(journal_entries, top_n=top_n_themes))
        candidates.extend(self._loop_detector.detect(goal_events))
        candidates.extend(self._contradiction_detector.detect(values, behavior_log))

        self._observations = candidates

        # Gate: only surface if timing is safe
        if not self._timing_gate.is_safe(stage, feeling, alignment_score):
            return []

        now = _utcnow()
        surfaceable: list[ShadowObservation] = []
        for obs in candidates:
            obs.surfaced_at = now
            surfaceable.append(obs)

        return surfaceable

    def apply_feedback(
        self,
        observation: ShadowObservation,
        response: UserResponse,
    ) -> ShadowObservation:
        """
        Apply user feedback to a ShadowObservation.

        Feedback effects on confidence:
          'seen_it'          — confidence unchanged (acknowledged)
          'not_accurate'     — confidence halved (pattern may be noise)
          'this_is_important'— confidence boosted to 1.0 (user confirms)

        Args:
            observation: The ShadowObservation to update
            response:    User response label

        Returns:
            Updated ShadowObservation
        """
        observation.user_response = response

        if response == "not_accurate":
            observation.confidence = round(observation.confidence * 0.5, 3)
        elif response == "this_is_important":
            observation.confidence = 1.0
        # 'seen_it' leaves confidence unchanged

        return observation

    @property
    def all_observations(self) -> list[ShadowObservation]:
        """All detected observations from the last evaluation cycle."""
        return list(self._observations)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()
