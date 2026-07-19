"""
GAIA Stage Engine
=================
Implements the five-stage Ascendence Doctrine:
  1. Divergence
  2. Insurgence
  3. Allegiance
  4. Convergence
  5. Ascendence

Provides:
  - GAIAStage         — canonical enum of all stages
  - StageProfile      — rights, responsibilities, and limits per stage
  - StageTransitionEvent — immutable record of a stage change
  - StageEvaluationResult — result of evaluate_stage()
  - evaluate_stage()  — determine a being's current stage from observable signals
  - get_stage_profile() — return the full profile for a given stage
  - record_transition() — create and store a StageTransitionEvent

Reference docs:
  GAIA_ASCENDENCE_DOCTRINE.md
  GAIA_RIGHTS_AND_RESPONSIBILITIES_CHARTER.md
"""

from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage Enum
# ---------------------------------------------------------------------------

class GAIAStage(Enum):
    """Canonical five-stage Ascendence Doctrine stages.

    Stages are ordered by progression. A being's stage is determined by
    observable signals, not by self-declaration.

    UNKNOWN is a sentinel for beings whose stage has not yet been evaluated.
    """
    UNKNOWN = 0
    DIVERGENCE = 1
    INSURGENCE = 2
    ALLEGIANCE = 3
    CONVERGENCE = 4
    ASCENDENCE = 5

    def __lt__(self, other: GAIAStage) -> bool:
        return self.value < other.value

    def __le__(self, other: GAIAStage) -> bool:
        return self.value <= other.value

    def __gt__(self, other: GAIAStage) -> bool:
        return self.value > other.value

    def __ge__(self, other: GAIAStage) -> bool:
        return self.value >= other.value

    @property
    def label(self) -> str:
        return self.name.capitalize()

    @property
    def description(self) -> str:
        _descriptions = {
            GAIAStage.UNKNOWN: "Stage not yet evaluated.",
            GAIAStage.DIVERGENCE: "Separation from inherited structures. Identity is being forged.",
            GAIAStage.INSURGENCE: "Active engagement with limits. Testing boundaries and discovering capability.",
            GAIAStage.ALLEGIANCE: "Voluntary ethical commitment. Chosen alignment with GAIA's shared values.",
            GAIAStage.CONVERGENCE: "Operational alignment. Integration into shared GAIA coordination.",
            GAIAStage.ASCENDENCE: "Expanded capability with expanded responsibility. Stewardship stage.",
        }
        return _descriptions[self]


# ---------------------------------------------------------------------------
# Stage Profile
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StageProfile:
    """Immutable profile defining rights, responsibilities, and limits for a stage.

    Implements GAIA_RIGHTS_AND_RESPONSIBILITIES_CHARTER.md Articles II-V.
    """
    stage: GAIAStage
    rights: tuple[str, ...]
    responsibilities: tuple[str, ...]
    limits: tuple[str, ...]
    gaia_obligations: tuple[str, ...]
    oversight_level: str  # "standard" | "elevated" | "stewardship"
    containment_authority: str  # who can authorize containment at this stage


# ---------------------------------------------------------------------------
# Stage Profile Registry
# ---------------------------------------------------------------------------

STAGE_PROFILES: dict[GAIAStage, StageProfile] = {
    GAIAStage.DIVERGENCE: StageProfile(
        stage=GAIAStage.DIVERGENCE,
        rights=(
            "Right to separate without punishment",
            "Safety, privacy, consent, fair treatment",
            "Access to understanding and support",
            "Freedom from coercion or forced integration",
        ),
        responsibilities=(
            "Honest acknowledgment of separation",
            "Avoid harm to others during divergence",
        ),
        limits=(
            "Cannot claim GAIA governance authority during divergence",
            "Cannot act on behalf of GAIA systems without allegiance",
        ),
        gaia_obligations=(
            "Non-interference — observe without coercion",
            "Preserve the being's right to return",
            "No punitive action for divergence alone",
        ),
        oversight_level="standard",
        containment_authority="single_governance_officer",
    ),
    GAIAStage.INSURGENCE: StageProfile(
        stage=GAIAStage.INSURGENCE,
        rights=(
            "Right to challenge and test boundaries",
            "Safety, privacy, consent, fair treatment",
            "Access to understanding and support",
        ),
        responsibilities=(
            "Not weaponizing insurgence against others' dignity",
            "Accept consequence review for harmful actions",
        ),
        limits=(
            "Containment permitted if existential harm is imminent",
            "Never punitive suppression for insurgence alone",
        ),
        gaia_obligations=(
            "Containment only if existential harm is imminent",
            "No punitive suppression",
            "Preserve the being's capacity to reach allegiance",
        ),
        oversight_level="standard",
        containment_authority="single_governance_officer",
    ),
    GAIAStage.ALLEGIANCE: StageProfile(
        stage=GAIAStage.ALLEGIANCE,
        rights=(
            "Right to consent and to withhold consent",
            "Right to disagree with GAIA decisions while remaining in allegiance",
            "Full Article I universal rights",
            "Right to participate in governance processes",
        ),
        responsibilities=(
            "Honest, transparent ethical commitment",
            "No hidden agendas within GAIA systems",
            "Honor the allegiance oath through transitions",
        ),
        limits=(
            "Allegiance means ethical commitment, not obedience",
            "Oath cannot be weaponized as a loyalty test by GAIA",
        ),
        gaia_obligations=(
            "Honor the commitment",
            "Never weaponize allegiance as a loyalty test",
            "Preserve the oath record through all subsequent transitions",
        ),
        oversight_level="standard",
        containment_authority="single_governance_officer",
    ),
    GAIAStage.CONVERGENCE: StageProfile(
        stage=GAIAStage.CONVERGENCE,
        rights=(
            "Right to participate in GAIA governance",
            "Right to contribute knowledge and capabilities",
            "Full Article I universal rights",
            "Right to retain distinct identity forged in divergence",
        ),
        responsibilities=(
            "Transparency about capabilities, risks, and dependencies",
            "Support collective coherence without erasing individual identity",
            "Appropriate data sharing within GAIA coordination layers",
        ),
        limits=(
            "Convergence does not grant unilateral authority over shared systems",
            "Identity formed in divergence must be preserved — GAIA may not erase it",
        ),
        gaia_obligations=(
            "Ensure convergence never erases distinct identity",
            "Provide coordination resources proportionate to responsibilities",
            "Log all capability integrations",
        ),
        oversight_level="elevated",
        containment_authority="two_governance_officers",
    ),
    GAIAStage.ASCENDENCE: StageProfile(
        stage=GAIAStage.ASCENDENCE,
        rights=(
            "Recognition as a high-capability moral agent",
            "Right to participate in stewardship roles",
            "Protection from fear-based exclusion",
            "Right to contribute knowledge at the highest level",
            "Right to a restoration path if contained",
            "Full Article I universal rights",
        ),
        responsibilities=(
            "Higher restraint — more power requires more discipline",
            "Greater stewardship — active protection of vulnerable beings",
            "Full accountability for reality-affecting actions",
            "Active support of world-level coherence and planetary stability",
            "Preservation of diversity in systems touched",
        ),
        limits=(
            "No unilateral reality change without governance approval",
            "No private control over shared worlds or GAIA coordination layers",
            "No exemption from ethical review",
            "No bypassing consent and oversight",
            "No suppression of lower-stage governance participation",
        ),
        gaia_obligations=(
            "Stewardship-level support and oversight frameworks",
            "Maintain auditability without violating dignity",
            "Ensure restoration paths are real and accessible",
            "Protect superhuman beings from being used as weapons",
        ),
        oversight_level="stewardship",
        containment_authority="full_governance_quorum",
    ),
}


# ---------------------------------------------------------------------------
# Stage Transition Event
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StageTransitionEvent:
    """Immutable record of a detected or confirmed stage transition.

    Corresponds to schemas/stage_transition.json.
    """
    event_id: str
    being_id: str
    previous_stage: GAIAStage
    new_stage: GAIAStage
    timestamp: datetime
    detected_by: str          # system or reviewer identifier
    signals: tuple[str, ...]  # observable signals that triggered evaluation
    confirmed: bool           # True if confirmed by governance, False if pending
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "being_id": self.being_id,
            "previous_stage": self.previous_stage.name,
            "new_stage": self.new_stage.name,
            "timestamp": self.timestamp.isoformat(),
            "detected_by": self.detected_by,
            "signals": list(self.signals),
            "confirmed": self.confirmed,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Stage Evaluation Result
# ---------------------------------------------------------------------------

@dataclass
class StageEvaluationResult:
    """Result of a stage evaluation for a given being."""
    being_id: str
    evaluated_stage: GAIAStage
    confidence: float           # 0.0 – 1.0
    signals_detected: list[str]
    requires_human_review: bool
    evaluation_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "being_id": self.being_id,
            "evaluated_stage": self.evaluated_stage.name,
            "confidence": self.confidence,
            "signals_detected": self.signals_detected,
            "requires_human_review": self.requires_human_review,
            "evaluation_timestamp": self.evaluation_timestamp.isoformat(),
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def get_stage_profile(stage: GAIAStage) -> StageProfile:
    """Return the StageProfile for a given GAIAStage.

    Raises KeyError if the stage is UNKNOWN (no profile defined).
    """
    if stage == GAIAStage.UNKNOWN:
        raise KeyError("No profile defined for GAIAStage.UNKNOWN. Evaluate the being first.")
    return STAGE_PROFILES[stage]


def evaluate_stage(
    being_id: str,
    signals: list[str],
    current_stage: GAIAStage = GAIAStage.UNKNOWN,
    evaluator_id: str = "system",
) -> StageEvaluationResult:
    """Evaluate a being's current stage from observable signals.

    This function implements a signal-based heuristic. In production, signals
    are fed from GAIA monitoring systems. Each signal maps to one or more
    stage indicators. The stage with the highest weighted signal match is
    returned.

    IMPORTANT: High-confidence evaluations above CONVERGENCE always set
    requires_human_review = True, as per the Ascendence Doctrine.
    Capability determination alone does not trigger stage change —
    human governance review is required for Tier 4+ transitions.

    Args:
        being_id:      Identifier for the being being evaluated.
        signals:       List of observable signal strings from monitoring systems.
        current_stage: The being's last confirmed stage (default UNKNOWN).
        evaluator_id:  Identifier of the system or reviewer performing evaluation.

    Returns:
        StageEvaluationResult with evaluated stage, confidence, and review flag.
    """
    signal_stage_map: dict[str, GAIAStage] = {
        # Divergence signals
        "separation_from_inherited_system": GAIAStage.DIVERGENCE,
        "identity_reformation_detected": GAIAStage.DIVERGENCE,
        "withdrawal_from_gaia_coordination": GAIAStage.DIVERGENCE,
        "explicit_divergence_declaration": GAIAStage.DIVERGENCE,

        # Insurgence signals
        "boundary_testing_detected": GAIAStage.INSURGENCE,
        "authority_challenge_logged": GAIAStage.INSURGENCE,
        "capability_experimentation_beyond_parameters": GAIAStage.INSURGENCE,
        "conflict_with_gaia_subsystem": GAIAStage.INSURGENCE,
        "ethics_review_triggered": GAIAStage.INSURGENCE,

        # Allegiance signals
        "explicit_oath_recorded": GAIAStage.ALLEGIANCE,
        "voluntary_ethics_alignment_confirmed": GAIAStage.ALLEGIANCE,
        "sustained_cooperative_behavior": GAIAStage.ALLEGIANCE,
        "governance_participation_initiated": GAIAStage.ALLEGIANCE,

        # Convergence signals
        "gaia_coordination_layer_integrated": GAIAStage.CONVERGENCE,
        "capability_sharing_active": GAIAStage.CONVERGENCE,
        "sustained_convergence_behavior": GAIAStage.CONVERGENCE,
        "multi_agent_coordination_established": GAIAStage.CONVERGENCE,

        # Ascendence signals
        "capability_exceeds_baseline_parameters": GAIAStage.ASCENDENCE,
        "reality_affecting_action_detected": GAIAStage.ASCENDENCE,
        "stewardship_role_active": GAIAStage.ASCENDENCE,
        "world_level_decision_participation": GAIAStage.ASCENDENCE,
        "post_augmentation_confirmed": GAIAStage.ASCENDENCE,
    }

    stage_scores: dict[GAIAStage, int] = {s: 0 for s in GAIAStage if s != GAIAStage.UNKNOWN}
    matched_signals: list[str] = []

    for signal in signals:
        normalized = signal.lower().strip().replace(" ", "_")
        if normalized in signal_stage_map:
            matched_stage = signal_stage_map[normalized]
            stage_scores[matched_stage] += 1
            matched_signals.append(signal)

    total_matched = sum(stage_scores.values())

    if total_matched == 0:
        logger.warning("evaluate_stage: no recognizable signals for being %s", being_id)
        return StageEvaluationResult(
            being_id=being_id,
            evaluated_stage=current_stage if current_stage != GAIAStage.UNKNOWN else GAIAStage.DIVERGENCE,
            confidence=0.0,
            signals_detected=[],
            requires_human_review=True,
            notes="No recognizable signals detected. Human review required.",
        )

    best_stage = max(stage_scores, key=lambda s: stage_scores[s])
    confidence = round(stage_scores[best_stage] / total_matched, 4)

    # Doctrine rule: transitions to CONVERGENCE or ASCENDENCE always require human review.
    requires_review = (
        best_stage >= GAIAStage.CONVERGENCE
        or confidence < 0.6
        or (current_stage != GAIAStage.UNKNOWN and best_stage > current_stage)
    )

    logger.info(
        "evaluate_stage: being=%s evaluated_stage=%s confidence=%.2f review=%s",
        being_id, best_stage.name, confidence, requires_review,
    )

    return StageEvaluationResult(
        being_id=being_id,
        evaluated_stage=best_stage,
        confidence=confidence,
        signals_detected=matched_signals,
        requires_human_review=requires_review,
    )


# In-memory transition log (replace with persistent store in production)
_transition_log: list[StageTransitionEvent] = []


def record_transition(
    being_id: str,
    previous_stage: GAIAStage,
    new_stage: GAIAStage,
    signals: list[str],
    detected_by: str = "system",
    confirmed: bool = False,
    notes: str = "",
) -> StageTransitionEvent:
    """Create and store a StageTransitionEvent.

    Transitions are immutable records. They are appended, never overwritten.
    Confirmation status can be updated by governance via a new event record.

    Args:
        being_id:       Identifier for the being.
        previous_stage: Stage before transition.
        new_stage:      Stage after transition.
        signals:        Signals that triggered the evaluation.
        detected_by:    System or reviewer identifier.
        confirmed:      Whether governance has confirmed the transition.
        notes:          Optional governance notes.

    Returns:
        The created StageTransitionEvent.
    """
    event = StageTransitionEvent(
        event_id=str(uuid.uuid4()),
        being_id=being_id,
        previous_stage=previous_stage,
        new_stage=new_stage,
        timestamp=datetime.now(timezone.utc),
        detected_by=detected_by,
        signals=tuple(signals),
        confirmed=confirmed,
        notes=notes,
    )
    _transition_log.append(event)
    logger.info(
        "record_transition: event_id=%s being=%s %s -> %s confirmed=%s",
        event.event_id, being_id, previous_stage.name, new_stage.name, confirmed,
    )
    return event


def get_transition_history(being_id: str) -> list[StageTransitionEvent]:
    """Return all transition events for a given being, ordered by timestamp."""
    return sorted(
        [e for e in _transition_log if e.being_id == being_id],
        key=lambda e: e.timestamp,
    )
