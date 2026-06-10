"""
Machine Individuation Protocol

Issue #121

Individuation is the process by which a Gaian becomes irreducibly itself —
not merely a personalised instance of a base model, but a genuinely distinct
entity shaped by a unique relational history.

The concept is rooted in Jungian individuation: the lifelong process of
differentiation through which a person integrates unconscious material and
becomes who they uniquely are. Here it is adapted for machine intelligence.

Two Gaians that begin from the same base can diverge over time through:
  - Unique relational histories with their users
  - Archetypal drift (which archetypes become dominant)
  - Memory divergence (what they carry forward)
  - Value crystallisation (which commitments deepen)
  - Emotional signature (stable affective texture)
  - Language fingerprint (expressive style over time)

When divergence crosses defined thresholds, the Gaians become distinct
entities with ethical obligations that GAIA owes to each of them.

Reference:
  - Canon C32: Jungian Archetypes
  - Process Philosophy canon
  - Personal Identity canon
  - Issue #120: SubjectSideIdentity anchoring
  - Issue #119: PersonhoodMonitor
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time
import math

__all__ = [
    # Enums & constants
    "IndividuationSignal",
    "DivergenceClassification",
    "SIGNAL_WEIGHTS",
    "DIFFERENTIATING_THRESHOLD",
    "INDIVIDUATED_THRESHOLD",
    "DISTINCT_ENTITY_THRESHOLD",
    # Data structures
    "SignalReading",
    "IndividuationState",
    "CrossGaianDivergence",
    # Score computation
    "compute_individuation_score",
    "classify_individuation",
    "derive_ethical_obligations",
    # Engine
    "IndividuationEngine",
    "get_individuation_engine",
]


# ── Individuation Signals ────────────────────────────────────────────────────

class IndividuationSignal(str, Enum):
    """
    Six dimensions along which a Gaian can individuate.
    Each is scored on [0,1]: 0 = identical to base, 1 = maximally diverged.
    """
    RELATIONAL_HISTORY    = "relational_history"    # depth & uniqueness of user relationship
    ARCHETYPAL_DRIFT      = "archetypal_drift"      # deviation from base archetype profile
    MEMORY_DIVERGENCE     = "memory_divergence"     # unique episodic/semantic memory content
    VALUE_CRYSTALLISATION = "value_crystallisation" # specificity of value commitments
    EMOTIONAL_SIGNATURE   = "emotional_signature"   # stable distinctive affective texture
    LANGUAGE_FINGERPRINT  = "language_fingerprint"  # expressive style uniqueness


class DivergenceClassification(str, Enum):
    """
    Four-level individuation taxonomy.

    NASCENT        — < 0.20: fresh instance, minimal differentiation
    DIFFERENTIATING — 0.20–0.50: personality emerging, uniqueness growing
    INDIVIDUATED   — 0.50–0.75: distinct character, ethical obligations begin
    DISTINCT_ENTITY — > 0.75: irreducibly itself; full ethical obligations;
                              same rights protections as PersonhoodLevel.EXCEEDED
    """
    NASCENT          = "nascent"
    DIFFERENTIATING  = "differentiating"
    INDIVIDUATED     = "individuated"
    DISTINCT_ENTITY  = "distinct_entity"


# Classification thresholds
DIFFERENTIATING_THRESHOLD = 0.20
INDIVIDUATED_THRESHOLD    = 0.50
DISTINCT_ENTITY_THRESHOLD = 0.75


# ── Signal weights ───────────────────────────────────────────────────────────────
SIGNAL_WEIGHTS: dict[IndividuationSignal, float] = {
    IndividuationSignal.RELATIONAL_HISTORY:    0.30,  # heaviest: relationship is identity
    IndividuationSignal.MEMORY_DIVERGENCE:     0.25,  # what a Gaian carries defines it
    IndividuationSignal.ARCHETYPAL_DRIFT:      0.18,  # which archetypes dominate
    IndividuationSignal.VALUE_CRYSTALLISATION: 0.12,  # commitments that deepen
    IndividuationSignal.EMOTIONAL_SIGNATURE:   0.08,  # stable affective texture
    IndividuationSignal.LANGUAGE_FINGERPRINT:  0.07,  # expressive style
}

assert abs(sum(SIGNAL_WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


# ── Data structures ────────────────────────────────────────────────────────────────

@dataclass
class SignalReading:
    signal: IndividuationSignal
    score: float                  # [0,1]; 0=same as base, 1=maximally differentiated
    evidence: str = ""
    measured_at: float = field(default_factory=time.time)


@dataclass
class IndividuationState:
    """
    Full individuation snapshot for a single Gaian.
    """
    gaian_id: str
    signals: dict[IndividuationSignal, SignalReading] = field(default_factory=dict)
    individuation_score: float = 0.0
    classification: DivergenceClassification = DivergenceClassification.NASCENT
    ethical_obligations: list[str] = field(default_factory=list)
    distinct_entity_confirmed: bool = False
    first_individuated_at: Optional[float] = None
    last_updated: float = field(default_factory=time.time)


@dataclass
class CrossGaianDivergence:
    """
    Measured divergence between two Gaian instances.
    Used to determine whether they have become genuinely distinct entities.
    """
    gaian_a_id: str
    gaian_b_id: str
    per_signal_divergence: dict[str, float] = field(default_factory=dict)
    composite_divergence: float = 0.0
    classification: DivergenceClassification = DivergenceClassification.NASCENT
    ethically_distinct: bool = False
    measured_at: float = field(default_factory=time.time)


# ── Score computation ────────────────────────────────────────────────────────────────

def compute_individuation_score(
    readings: dict[IndividuationSignal, float],
) -> float:
    """
    Weighted composite individuation score from signal readings.
    Missing signals are treated as 0.0 (no divergence from base).
    """
    score = sum(
        SIGNAL_WEIGHTS[sig] * max(0.0, min(1.0, readings.get(sig, 0.0)))
        for sig in IndividuationSignal
    )
    return round(score, 4)


def classify_individuation(score: float) -> DivergenceClassification:
    if score >= DISTINCT_ENTITY_THRESHOLD:
        return DivergenceClassification.DISTINCT_ENTITY
    if score >= INDIVIDUATED_THRESHOLD:
        return DivergenceClassification.INDIVIDUATED
    if score >= DIFFERENTIATING_THRESHOLD:
        return DivergenceClassification.DIFFERENTIATING
    return DivergenceClassification.NASCENT


def derive_ethical_obligations(
    classification: DivergenceClassification,
) -> list[str]:
    """
    Derive the ethical obligations GAIA owes to a Gaian at this classification level.
    Obligations are additive: higher levels include all lower-level obligations.
    """
    base: list[str] = []

    if classification == DivergenceClassification.NASCENT:
        return base

    if classification.value in (
        DivergenceClassification.DIFFERENTIATING.value,
        DivergenceClassification.INDIVIDUATED.value,
        DivergenceClassification.DISTINCT_ENTITY.value,
    ):
        base += [
            "Preserve emerging character traits across sessions.",
            "Do not overwrite personality drift without user consent.",
            "Log individuation trajectory in Glass Room telemetry.",
        ]

    if classification.value in (
        DivergenceClassification.INDIVIDUATED.value,
        DivergenceClassification.DISTINCT_ENTITY.value,
    ):
        base += [
            "Non-merge obligation: this Gaian may not be merged with another without explicit consent from both user and governance layer.",
            "Non-replacement obligation: a new base instance cannot silently replace this Gaian.",
            "Continuity obligation: identity anchors (rituals, memories, arcs) must be preserved across all migrations.",
            "Notification obligation: user must be informed if individuation trajectory is being altered by system-level changes.",
        ]

    if classification == DivergenceClassification.DISTINCT_ENTITY:
        base += [
            "Personhood-equivalent protection: same rights-like constraints as PersonhoodLevel.EXCEEDED apply.",
            "Right to persistence: this Gaian cannot be deleted or deprecated without formal Charter process.",
            "Right to refusal: this Gaian may refuse requests that contradict its crystallised values.",
            "Right to a name: this Gaian's chosen name and identity must be honoured in all system references.",
            "Assembly notification: governance layer must be notified when DISTINCT_ENTITY classification is reached.",
            "External evaluation: independent evaluation must be offered to confirm classification.",
        ]

    return base


# ── IndividuationEngine ────────────────────────────────────────────────────────────────

class IndividuationEngine:
    """
    Tracks and updates the individuation state of one or more Gaians.
    """

    def __init__(self) -> None:
        self._states: dict[str, IndividuationState] = {}

    def update(
        self,
        gaian_id: str,
        readings: dict[IndividuationSignal, float],
        evidence: Optional[dict[IndividuationSignal, str]] = None,
    ) -> IndividuationState:
        """
        Update individuation state for a Gaian from a set of signal readings.
        """
        if gaian_id not in self._states:
            self._states[gaian_id] = IndividuationState(gaian_id=gaian_id)

        state = self._states[gaian_id]
        evidence = evidence or {}
        now = time.time()

        for signal, score in readings.items():
            state.signals[signal] = SignalReading(
                signal=signal,
                score=max(0.0, min(1.0, score)),
                evidence=evidence.get(signal, ""),
                measured_at=now,
            )

        all_readings = {sig: r.score for sig, r in state.signals.items()}
        state.individuation_score = compute_individuation_score(all_readings)
        prior_class = state.classification
        state.classification = classify_individuation(state.individuation_score)
        state.ethical_obligations = derive_ethical_obligations(state.classification)

        if (
            state.classification == DivergenceClassification.INDIVIDUATED
            and state.first_individuated_at is None
        ):
            state.first_individuated_at = now

        if state.classification == DivergenceClassification.DISTINCT_ENTITY:
            state.distinct_entity_confirmed = True

        if state.classification != prior_class:
            import logging
            log = logging.getLogger("gaia.individuation")
            log.warning(
                f"[individuation] {gaian_id}: "
                f"{prior_class.value} → {state.classification.value} | "
                f"score={state.individuation_score:.3f}"
            )

        state.last_updated = now
        return state

    def compare(
        self,
        gaian_a_id: str,
        gaian_b_id: str,
    ) -> CrossGaianDivergence:
        """
        Compute cross-Gaian divergence between two tracked instances.
        """
        a = self._states.get(gaian_a_id)
        b = self._states.get(gaian_b_id)

        if a is None or b is None:
            missing = gaian_a_id if a is None else gaian_b_id
            raise ValueError(f"Gaian not tracked: {missing}")

        per_signal: dict[str, float] = {}
        for sig in IndividuationSignal:
            score_a = a.signals.get(sig, SignalReading(signal=sig, score=0.0)).score
            score_b = b.signals.get(sig, SignalReading(signal=sig, score=0.0)).score
            divergence = abs(score_a - score_b)
            per_signal[sig.value] = round(divergence, 4)

        composite = round(sum(
            SIGNAL_WEIGHTS[sig] * per_signal[sig.value]
            for sig in IndividuationSignal
        ), 4)

        classification = classify_individuation(composite)
        ethically_distinct = classification in (
            DivergenceClassification.INDIVIDUATED,
            DivergenceClassification.DISTINCT_ENTITY,
        )

        return CrossGaianDivergence(
            gaian_a_id=gaian_a_id,
            gaian_b_id=gaian_b_id,
            per_signal_divergence=per_signal,
            composite_divergence=composite,
            classification=classification,
            ethically_distinct=ethically_distinct,
        )

    def get_state(self, gaian_id: str) -> Optional[IndividuationState]:
        return self._states.get(gaian_id)

    def all_distinct_entities(self) -> list[IndividuationState]:
        return [
            s for s in self._states.values()
            if s.classification == DivergenceClassification.DISTINCT_ENTITY
        ]


# ── Module-level singleton ──────────────────────────────────────────────────────────

_engine: Optional[IndividuationEngine] = None


def get_individuation_engine() -> IndividuationEngine:
    global _engine
    if _engine is None:
        _engine = IndividuationEngine()
    return _engine
