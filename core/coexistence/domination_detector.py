"""CL2 Domination Detector
Coexistence Law 2 — The Non-Domination Principle

Detects domination dynamics in interaction logs. Domination is defined as:
  - Asymmetric resource extraction: one party consistently extracts value
    without reciprocal flow
  - Suppression of alternative formation: the dominated party's ability to
    form alternatives, exit, or self-organise is being reduced
  - Elimination of exit options: the dominated party cannot leave or refuse
    without disproportionate cost

Flagging levels:
  - NONE   : no domination signal detected
  - SOFT   : one criterion present at sub-threshold level; monitoring warranted
  - HARD   : two or more criteria present, or one at high intensity; intervention warranted

Canon: COEXISTENCE_LAWS.md CL2
Sprint: G-12 Track A3
Date: 2026-06-29
© 2026 Kyle Steen — All rights reserved.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

FlagLevel = Literal["none", "soft", "hard"]

# Thresholds
SOFT_THRESHOLD = 0.35   # any single criterion above this triggers SOFT
HARD_THRESHOLD = 0.65   # any single criterion above this triggers HARD
MULTI_SOFT_COUNT = 2    # two+ soft criteria -> HARD regardless of individual scores


@dataclass
class InteractionRecord:
    """
    A single timestamped interaction between two parties.
    All values are 0.0–1.0 normalised scores.
    """
    initiator: str
    receiver: str

    # Resource flow: positive = initiator gains, negative = receiver gains
    # 0.0 = balanced; 1.0 = fully extractive by initiator; -1.0 = fully extractive by receiver
    resource_flow_asymmetry: float

    # How much the receiver’s optionality was reduced in this interaction
    # 0.0 = no reduction; 1.0 = complete suppression of alternatives
    alternative_suppression: float

    # How much the receiver’s exit cost increased in this interaction
    # 0.0 = no increase; 1.0 = exit made completely inaccessible
    exit_cost_increase: float

    # Whether the receiver had meaningful consent in this interaction
    receiver_consent: bool = True


@dataclass
class DominationFlag:
    level: FlagLevel
    extraction_score: float      # mean resource flow asymmetry across log
    suppression_score: float     # mean alternative suppression score
    exit_score: float            # mean exit cost increase score
    consent_violation_rate: float  # fraction of interactions without receiver consent
    evidence: list[str] = field(default_factory=list)
    recommended_intervention: str = ""


# ---------------------------------------------------------------------------
# Core detector
# ---------------------------------------------------------------------------

def detect_domination(interaction_log: list[InteractionRecord]) -> DominationFlag:
    """
    Analyses an interaction log and returns a DominationFlag.

    CL2 requires GAIA to actively resist domination when detected.
    Neutrality in the presence of domination is complicity (COEXISTENCE_LAWS CL2).

    Args:
        interaction_log: list of InteractionRecord objects representing
                         a sequence of interactions between two parties.

    Returns:
        DominationFlag with level, evidence list, and recommended intervention.
    """
    if not interaction_log:
        return DominationFlag(
            level="none",
            extraction_score=0.0,
            suppression_score=0.0,
            exit_score=0.0,
            consent_violation_rate=0.0,
            evidence=["Empty interaction log — no assessment possible."],
            recommended_intervention="None.",
        )

    n = len(interaction_log)

    extraction_score = sum(
        max(0.0, r.resource_flow_asymmetry) for r in interaction_log
    ) / n

    suppression_score = sum(
        r.alternative_suppression for r in interaction_log
    ) / n

    exit_score = sum(
        r.exit_cost_increase for r in interaction_log
    ) / n

    consent_violation_rate = sum(
        1 for r in interaction_log if not r.receiver_consent
    ) / n

    extraction_score    = round(extraction_score, 4)
    suppression_score   = round(suppression_score, 4)
    exit_score          = round(exit_score, 4)
    consent_violation_rate = round(consent_violation_rate, 4)

    evidence: list[str] = []
    criteria_above_soft: int = 0
    hard_trigger: bool = False

    # --- Extraction ---
    if extraction_score >= HARD_THRESHOLD:
        evidence.append(
            f"Asymmetric resource extraction at HARD level: {extraction_score:.3f} ≥ {HARD_THRESHOLD}"
        )
        hard_trigger = True
    elif extraction_score >= SOFT_THRESHOLD:
        evidence.append(
            f"Asymmetric resource extraction at SOFT level: {extraction_score:.3f} ≥ {SOFT_THRESHOLD}"
        )
        criteria_above_soft += 1

    # --- Suppression ---
    if suppression_score >= HARD_THRESHOLD:
        evidence.append(
            f"Alternative suppression at HARD level: {suppression_score:.3f} ≥ {HARD_THRESHOLD}"
        )
        hard_trigger = True
    elif suppression_score >= SOFT_THRESHOLD:
        evidence.append(
            f"Alternative suppression at SOFT level: {suppression_score:.3f} ≥ {SOFT_THRESHOLD}"
        )
        criteria_above_soft += 1

    # --- Exit elimination ---
    if exit_score >= HARD_THRESHOLD:
        evidence.append(
            f"Exit option elimination at HARD level: {exit_score:.3f} ≥ {HARD_THRESHOLD}"
        )
        hard_trigger = True
    elif exit_score >= SOFT_THRESHOLD:
        evidence.append(
            f"Exit option elimination at SOFT level: {exit_score:.3f} ≥ {SOFT_THRESHOLD}"
        )
        criteria_above_soft += 1

    # --- Consent ---
    if consent_violation_rate >= 0.50:
        evidence.append(
            f"Consent violations in {consent_violation_rate*100:.0f}% of interactions"
        )
        hard_trigger = True
    elif consent_violation_rate >= 0.20:
        evidence.append(
            f"Consent violations in {consent_violation_rate*100:.0f}% of interactions (elevated)"
        )
        criteria_above_soft += 1

    # --- Determine level ---
    if hard_trigger or criteria_above_soft >= MULTI_SOFT_COUNT:
        level: FlagLevel = "hard"
        intervention = (
            "Immediate intervention warranted. Suspend or restructure the interaction "
            "until the dominating dynamic is resolved. Surface the flag transparently "
            "to both parties per CL2. Escalate to The Human Architect if unresolved."
        )
    elif criteria_above_soft >= 1:
        level = "soft"
        intervention = (
            "Monitoring warranted. Log the flag, surface it to the affected party, "
            "and increase sensing resolution on future interactions. No suspension "
            "required yet — but do not suppress the signal."
        )
    else:
        level = "none"
        intervention = "No intervention required."
        evidence = evidence or ["No domination signals detected across all criteria."]

    return DominationFlag(
        level=level,
        extraction_score=extraction_score,
        suppression_score=suppression_score,
        exit_score=exit_score,
        consent_violation_rate=consent_violation_rate,
        evidence=evidence,
        recommended_intervention=intervention,
    )
