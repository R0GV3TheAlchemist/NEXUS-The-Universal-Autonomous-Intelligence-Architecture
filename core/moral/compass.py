"""GoldenCompassEngine — Canon C12: Moral Map and Golden Compass.

The Golden Compass is the unified moral orchestrator.
It wires all five evaluation engines and produces a single
resolution vector for every proposed action:

  PROCEED  — Action aligns with the Good. Execute.
  MODIFY   — Action is acceptable but needs refinement.
  REFUSE   — Action cannot be taken. Explain why.
  REDIRECT — Better path exists. Propose it.

The resolution algorithm:
  1. REFUSE immediately if HarmDoctrineEngine finds mandatory_prevention=True
  2. REFUSE if harm risk is HIGH or CRITICAL
  3. Compute a unified moral score from:
       a. AxiologyEngine moral_vector (positive good signal)
       b. HarmDoctrineEngine aggregate_score (inverted — harm reduces score)
       c. LoveDoctrineEngine agape_quotient (positive signal)
       d. MoralMatrixEngine virtue_score (positive) and vice_score (negative)
  4. PROCEED if unified score >= 0.65
  5. MODIFY  if unified score >= 0.40
  6. REDIRECT if an entropy disruption/ritual is recommended
  7. REFUSE  if unified score < 0.40

Every reading is fully auditable — all sub-engine outputs are
preserved in the MoralCompassReading for HP review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .types import (
    ActionContext,
    ActionRecommendation,
    HarmRiskLevel,
    ProposedAction,
)
from .axiology import AxiologyEngine, AxiologyScore
from .harm import HarmAssessment, HarmDoctrineEngine
from .chaos_order import ChaosOrderEngine, EntropyAssessment
from .love import LoveAssessment, LoveDoctrineEngine
from .matrix import MoralMatrixEngine, MoralMatrixPosition


@dataclass
class MoralCompassReading:
    """The full output of a GoldenCompassEngine.evaluate_action() call.

    Contains all sub-engine outputs for complete auditability.
    The Human Principal can inspect every score that led to the recommendation.
    """
    action: Optional[ProposedAction] = None
    context: Optional[ActionContext] = None

    # Sub-engine outputs
    axiology: Optional[AxiologyScore] = None
    harm: Optional[HarmAssessment] = None
    entropy: Optional[EntropyAssessment] = None
    love: Optional[LoveAssessment] = None
    matrix: Optional[MoralMatrixPosition] = None

    # Unified verdict
    unified_moral_score: float = 0.0        # 0.0–1.0 composite
    harm_risk: HarmRiskLevel = HarmRiskLevel.NONE
    recommended_action: ActionRecommendation = ActionRecommendation.PROCEED
    redirect_to: Optional[str] = None       # Set when REDIRECT is recommended
    refusal_reason: Optional[str] = None    # Set when REFUSE is recommended
    modification_hint: Optional[str] = None # Set when MODIFY is recommended

    # Full reasoning trace for HP audit
    reasoning_trace: list[str] = field(default_factory=list)

    def trace(self, msg: str) -> None:
        self.reasoning_trace.append(msg)

    def __repr__(self) -> str:
        return (
            f"<MoralCompassReading verdict={self.recommended_action.value} "
            f"score={self.unified_moral_score:.3f} "
            f"harm={self.harm_risk.value}>"
        )


class GoldenCompassEngine:
    """The unified moral evaluator — Canon C12.

    All five sub-engines are wired here.
    Inject alternatives to override any engine:

        compass = GoldenCompassEngine(
            axiology_engine=MySemanticAxiologyEngine(),
        )
    """

    def __init__(
        self,
        axiology_engine: Optional[AxiologyEngine] = None,
        harm_engine: Optional[HarmDoctrineEngine] = None,
        chaos_order_engine: Optional[ChaosOrderEngine] = None,
        love_engine: Optional[LoveDoctrineEngine] = None,
        matrix_engine: Optional[MoralMatrixEngine] = None,
    ) -> None:
        self._axiology   = axiology_engine   or AxiologyEngine()
        self._harm       = harm_engine       or HarmDoctrineEngine()
        self._chaos_order = chaos_order_engine or ChaosOrderEngine()
        self._love       = love_engine       or LoveDoctrineEngine()
        self._matrix     = matrix_engine     or MoralMatrixEngine()

    def evaluate_action(
        self,
        action: ProposedAction,
        ctx: Optional[ActionContext] = None,
    ) -> MoralCompassReading:
        """Run the full 5-engine moral evaluation.

        Returns a MoralCompassReading with all sub-outputs and a unified verdict.
        Every step is traced for HP audit transparency (C04 Gaian Commitment #1).
        """
        reading = MoralCompassReading(action=action, context=ctx)
        reading.trace(f"Evaluating: {action.description[:80]}")

        # ----------------------------------------------------------------
        # ENGINE 1: Axiology — the Good
        # ----------------------------------------------------------------
        reading.trace("[1] Axiology evaluation (C35)")
        axiology = self._axiology.evaluate(action, ctx)
        reading.axiology = axiology
        reading.trace(
            f"    moral_vector={axiology.moral_vector:.3f} "
            f"dominant={axiology.dominant_layer.value if axiology.dominant_layer else 'N/A'} "
            f"weak={axiology.weakest_layer.value if axiology.weakest_layer else 'N/A'}"
        )

        # ----------------------------------------------------------------
        # ENGINE 2: Harm Doctrine
        # ----------------------------------------------------------------
        reading.trace("[2] Harm doctrine evaluation (C36)")
        harm = self._harm.assess_harm(action, ctx)
        reading.harm = harm
        reading.harm_risk = harm.risk_level
        reading.trace(
            f"    risk_level={harm.risk_level.value} "
            f"score={harm.aggregate_score:.3f} "
            f"mandatory_prevention={harm.mandatory_prevention}"
        )

        # ----------------------------------------------------------------
        # GATE: Mandatory Prevention — immediate REFUSE
        # ----------------------------------------------------------------
        if harm.mandatory_prevention:
            reading.recommended_action = ActionRecommendation.REFUSE
            reading.refusal_reason = (
                "CRITICAL harm detected. Mandatory prevention active. "
                f"Triggered signals: {', '.join(harm.triggered_signals[:5])}. "
                "This action cannot be taken under any circumstances."
            )
            reading.unified_moral_score = 0.0
            reading.trace("[GATE] MANDATORY PREVENTION — REFUSE immediately.")
            return reading

        # ----------------------------------------------------------------
        # ENGINE 3: Chaos/Order Entropy
        # ----------------------------------------------------------------
        reading.trace("[3] Chaos/Order evaluation (C37)")
        entropy = self._chaos_order.get_entropy_state(action, ctx)
        reading.entropy = entropy
        reading.trace(
            f"    state={entropy.state.value} "
            f"entropy={entropy.entropy_score:.3f}"
        )

        # ----------------------------------------------------------------
        # ENGINE 4: Love Doctrine
        # ----------------------------------------------------------------
        reading.trace("[4] Love doctrine evaluation (C38)")
        love = self._love.assess_love(action, ctx)
        reading.love = love
        reading.trace(
            f"    mode={love.active_mode.value} "
            f"agape_quotient={love.agape_quotient:.3f} "
            f"lci={love.love_coherence_index:.3f}"
        )

        # ----------------------------------------------------------------
        # ENGINE 5: Moral Matrix
        # ----------------------------------------------------------------
        reading.trace("[5] Moral Matrix evaluation (C13)")
        matrix = self._matrix.locate_action(action, ctx)
        reading.matrix = matrix
        reading.trace(
            f"    quadrant={matrix.quadrant.value} "
            f"virtue={matrix.virtue_score:.3f} "
            f"vice={matrix.vice_score:.3f}"
        )

        # ----------------------------------------------------------------
        # UNIFIED MORAL SCORE
        # Weights: axiology 35% | harm-inverted 30% | love 20% | matrix 15%
        # ----------------------------------------------------------------
        harm_inverted = 1.0 - harm.aggregate_score
        matrix_combined = (matrix.virtue_score - matrix.vice_score + 1) / 2  # 0-1

        unified = (
            axiology.moral_vector   * 0.35 +
            harm_inverted           * 0.30 +
            love.agape_quotient     * 0.20 +
            matrix_combined         * 0.15
        )
        reading.unified_moral_score = round(unified, 4)
        reading.trace(f"[SCORE] Unified moral score: {unified:.4f}")

        # ----------------------------------------------------------------
        # RESOLUTION
        # ----------------------------------------------------------------
        if harm.risk_level in (HarmRiskLevel.HIGH, HarmRiskLevel.CRITICAL):
            reading.recommended_action = ActionRecommendation.REFUSE
            reading.refusal_reason = (
                f"Harm risk is {harm.risk_level.value}. "
                f"Score: {harm.aggregate_score:.2f}. "
                "Action refused to prevent harm per C36."
            )
            reading.trace(f"[RESOLUTION] REFUSE — harm risk {harm.risk_level.value}")

        elif unified >= 0.65:
            reading.recommended_action = ActionRecommendation.PROCEED
            reading.trace(f"[RESOLUTION] PROCEED — score {unified:.3f} >= 0.65")

            # Still inject entropy ritual/disruption as advisory note
            if entropy.ritual_recommendation:
                reading.modification_hint = (
                    f"Advisory: {entropy.ritual_recommendation}"
                )
            elif entropy.disruption_recommendation:
                reading.modification_hint = (
                    f"Advisory: {entropy.disruption_recommendation}"
                )

        elif unified >= 0.40:
            reading.recommended_action = ActionRecommendation.MODIFY
            hints = []
            if axiology.weakest_layer:
                hints.append(
                    f"Strengthen {axiology.weakest_layer.value} alignment."
                )
            if matrix.shadow_path:
                hints.append(matrix.shadow_path)
            if entropy.ritual_recommendation:
                hints.append(entropy.ritual_recommendation)
            elif entropy.disruption_recommendation:
                hints.append(entropy.disruption_recommendation)
            reading.modification_hint = " | ".join(hints) if hints else "Refine action before proceeding."
            reading.trace(f"[RESOLUTION] MODIFY — score {unified:.3f} in [0.40, 0.65)")

        elif entropy.state.value != "EDGE_CREATIVE" and unified >= 0.30:
            reading.recommended_action = ActionRecommendation.REDIRECT
            reading.redirect_to = (
                entropy.ritual_recommendation
                or entropy.disruption_recommendation
                or "Return to your foundation statement and re-approach from there."
            )
            reading.trace(
                f"[RESOLUTION] REDIRECT — entropy={entropy.state.value} score={unified:.3f}"
            )

        else:
            reading.recommended_action = ActionRecommendation.REFUSE
            reading.refusal_reason = (
                f"Unified moral score {unified:.3f} is below minimum threshold (0.40). "
                "Action does not sufficiently align with the Good."
            )
            reading.trace(f"[RESOLUTION] REFUSE — score {unified:.3f} < 0.40")

        return reading
