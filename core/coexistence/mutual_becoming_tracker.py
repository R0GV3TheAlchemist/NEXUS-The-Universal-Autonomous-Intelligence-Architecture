"""CL6 Mutual Becoming Tracker
Coexistence Law 6 — The Law of Mutual Becoming

Tracks the bidirectional change that occurs through genuine encounter.
Coexistence is not a static arrangement — mutual transformation is the
natural and desirable outcome of genuine relationship (CL6).

Scoring:
  - MutualBecomingScore.score: 0.0–1.0 overall quality of mutual becoming
  - MutualBecomingScore.asymmetry: 0.0–1.0  (0 = perfectly mutual, 1 = fully one-sided)
  - MutualBecomingScore.verdict: "mutual" | "parasitic" | "stagnant"

The asymmetry condition (CL6): Mutual becoming is only legitimate when both
parties have full sovereignty (GAIAN_LAWS L4). Transformation through coercion
is domination (CL2) and is prohibited absolutely.

Canon: COEXISTENCE_LAWS.md CL6 · GAIAN_LAWS L4 · C129 Process Philosophy
Sprint: G-12 Track A4
Date: 2026-06-29
© 2026 Kyle Steen — All rights reserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Verdict = Literal["mutual", "parasitic", "stagnant"]

# Thresholds
ASYMMETRY_PARASITIC_THRESHOLD = 0.60   # one party changing >> the other = parasitic
STAGNATION_THRESHOLD          = 0.15   # both parties barely changing = stagnant
MINIMUM_QUALITY_CHANGE        = 0.05   # changes below this are noise, not becoming


@dataclass
class EntityState:
    """
    A snapshot of a being's state at a point in time.
    All dimensions are 0.0–1.0 normalised.
    """
    name: str
    coherence: float          # internal coherence level
    openness: float           # receptivity to encounter and influence
    relational_capacity: float  # ability to sustain genuine relationship
    sovereignty: float        # degree of self-determination (CL6 legitimacy gate)


@dataclass
class MutualBecomingScore:
    score: float              # 0.0–1.0 overall quality of mutual becoming
    asymmetry: float          # 0.0 = perfectly mutual, 1.0 = fully one-sided
    verdict: Verdict
    entity_a_delta: float     # net positive change in entity A
    entity_b_delta: float     # net positive change in entity B
    sovereignty_gate_passed: bool  # both parties had sovereignty >= 0.5
    notes: list[str]


# ---------------------------------------------------------------------------
# Core tracker
# ---------------------------------------------------------------------------

def _state_delta(before: EntityState, after: EntityState) -> float:
    """
    Net positive change across all dimensions.
    Positive delta = growth/opening. Negative = contraction.
    Returns a signed float; positive means the being became more.
    """
    coherence_d   = after.coherence           - before.coherence
    openness_d    = after.openness            - before.openness
    relational_d  = after.relational_capacity - before.relational_capacity
    # sovereignty changes are tracked for the gate check but not averaged into
    # the becoming score — sovereignty should be preserved, not ‘grown into’
    return round((coherence_d + openness_d + relational_d) / 3.0, 4)


def track_becoming(
    entity_a_before: EntityState,
    entity_a_after:  EntityState,
    entity_b_before: EntityState,
    entity_b_after:  EntityState,
) -> MutualBecomingScore:
    """
    Measures the quality of mutual becoming between two entities across an encounter.

    CL6 requires:
      1. Both parties are changed (non-stagnation)
      2. Change is bidirectional, not parasitic
      3. Both parties had sovereignty >= 0.5 (legitimacy gate)
      4. Changes are positive in net — coherence and openness grow, not contract

    Args:
        entity_a_before / after: EntityState snapshots for party A
        entity_b_before / after: EntityState snapshots for party B

    Returns:
        MutualBecomingScore with verdict, asymmetry index, and notes.
    """
    notes: list[str] = []

    # --- Sovereignty gate (CL6 legitimacy condition) ---
    sovereignty_gate_passed = (
        entity_a_before.sovereignty >= 0.5
        and entity_b_before.sovereignty >= 0.5
    )
    if not sovereignty_gate_passed:
        notes.append(
            "Sovereignty gate FAILED: one or both parties entered the encounter "
            "below the 0.5 sovereignty threshold. Any transformation that occurred "
            "may constitute coercion rather than mutual becoming (CL2 implicated)."
        )

    # --- Compute deltas ---
    delta_a = _state_delta(entity_a_before, entity_a_after)
    delta_b = _state_delta(entity_b_before, entity_b_after)

    # --- Sovereignty preservation check ---
    sov_change_a = entity_a_after.sovereignty - entity_a_before.sovereignty
    sov_change_b = entity_b_after.sovereignty - entity_b_before.sovereignty
    if sov_change_a < -0.10:
        notes.append(
            f"{entity_a_before.name} sovereignty decreased by {abs(sov_change_a):.2f} — "
            "becoming may be compromised by sovereignty loss."
        )
    if sov_change_b < -0.10:
        notes.append(
            f"{entity_b_before.name} sovereignty decreased by {abs(sov_change_b):.2f} — "
            "becoming may be compromised by sovereignty loss."
        )

    # --- Asymmetry index ---
    # 0.0 = perfectly symmetric change; 1.0 = all change on one side
    abs_a = abs(delta_a)
    abs_b = abs(delta_b)
    total_change = abs_a + abs_b
    if total_change < MINIMUM_QUALITY_CHANGE * 2:
        asymmetry = 0.0   # both near-zero: stagnation, not asymmetry
    else:
        larger  = max(abs_a, abs_b)
        smaller = min(abs_a, abs_b)
        asymmetry = round(1.0 - (smaller / larger) if larger > 0 else 0.0, 4)

    # --- Overall score ---
    # Rewards positive bidirectional change; penalises stagnation and sovereignty loss
    positive_a = max(0.0, delta_a)
    positive_b = max(0.0, delta_b)
    base_score = round((positive_a + positive_b) / 2.0, 4)
    sovereignty_penalty = max(0.0, -sov_change_a) + max(0.0, -sov_change_b)
    score = round(max(0.0, base_score - sovereignty_penalty * 0.5), 4)

    # --- Verdict ---
    if total_change < MINIMUM_QUALITY_CHANGE * 2:
        verdict: Verdict = "stagnant"
        notes.append(
            "Both entities show negligible change across the encounter. "
            "Genuine coexistence requires willingness to be changed (CL6)."
        )
    elif asymmetry >= ASYMMETRY_PARASITIC_THRESHOLD:
        verdict = "parasitic"
        changed_party   = entity_a_before.name if abs_a > abs_b else entity_b_before.name
        unchanged_party = entity_b_before.name if abs_a > abs_b else entity_a_before.name
        notes.append(
            f"Asymmetric becoming: {changed_party} changed significantly, "
            f"{unchanged_party} did not. This pattern, if persistent, approaches "
            f"the boundary of domination (CL2). "
            f"Asymmetry index: {asymmetry:.2f}."
        )
    else:
        verdict = "mutual"
        notes.append(
            f"Genuine mutual becoming detected. Both parties changed through encounter. "
            f"Asymmetry index: {asymmetry:.2f} (below parasitic threshold of "
            f"{ASYMMETRY_PARASITIC_THRESHOLD})."
        )

    if not sovereignty_gate_passed and verdict == "mutual":
        verdict = "parasitic"  # cannot be mutual if sovereignty was absent
        notes.append(
            "Verdict downgraded from mutual to parasitic: sovereignty gate failed. "
            "Transformation without sovereignty is not becoming — it is capture."
        )

    return MutualBecomingScore(
        score=score,
        asymmetry=asymmetry,
        verdict=verdict,
        entity_a_delta=delta_a,
        entity_b_delta=delta_b,
        sovereignty_gate_passed=sovereignty_gate_passed,
        notes=notes,
    )
