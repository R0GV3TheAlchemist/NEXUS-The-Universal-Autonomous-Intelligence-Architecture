"""
GAIA Deep Research Runtime — Falsifiability Stamper
Issue #454

Every factual claim in the output carries:
  - A confidence grade
  - A falsification condition
  - A hallucination risk score

This is the epistemic spine of GAIA.
A system that cannot say "here is how I could be wrong"
is not trustworthy — it is just confident.

Aligned with Falsification Protocol (#451).
"""

from typing import List, Tuple
from core.research.models import (
    Claim, SynthesisResult, ConfidenceLevel, EvidenceLevel
)

# Hallucination risk thresholds
HALLUCINATION_RISK_HIGH = 0.65
HALLUCINATION_RISK_MEDIUM = 0.35

# Evidence level → falsification template
FALSIFICATION_TEMPLATES = {
    EvidenceLevel.EMPIRICAL: (
        "Falsified by: peer-reviewed systematic review with contrary findings "
        "at p < 0.05, or direct replication failure in controlled conditions."
    ),
    EvidenceLevel.CROSS_TRADITION: (
        "Weakened by: independent cross-cultural studies showing no convergence, "
        "or primary source scholars challenging the tradition's claims."
    ),
    EvidenceLevel.LINEAGE: (
        "Weakened by: lineage scholars disputing interpretation, "
        "or primary texts showing different meaning in context."
    ),
    EvidenceLevel.GAIAN_OBSERVED: (
        "Speculative until: replicated by independent GAIA community observations "
        "and cross-referenced with empirical literature."
    ),
    EvidenceLevel.SPECULATIVE: (
        "Speculative: no current empirical or cross-tradition support. "
        "Falsifiable by any peer-reviewed contrary evidence."
    ),
}


class FalsifiabilityStamper:
    """
    Stamps every claim in a SynthesisResult with:
    - Finalised confidence level
    - Explicit falsification condition
    - Hallucination risk score
    - A flag if the claim requires hedging before delivery
    """

    def stamp(self, synthesis: SynthesisResult) -> SynthesisResult:
        """
        Apply falsifiability stamps to all claims in the synthesis.
        Modifies claims in-place and returns updated synthesis.
        """
        high_risk_count = 0

        for claim in synthesis.claims:
            # Ensure falsification condition is set
            if not claim.falsification_condition:
                claim.falsification_condition = FALSIFICATION_TEMPLATES.get(
                    claim.evidence_level,
                    FALSIFICATION_TEMPLATES[EvidenceLevel.SPECULATIVE]
                )

            # Recalculate hallucination risk
            claim.hallucination_risk = self._compute_risk(claim)

            # Escalate confidence downward if risk is high
            if claim.hallucination_risk >= HALLUCINATION_RISK_HIGH:
                if claim.confidence not in (
                    ConfidenceLevel.LOW, ConfidenceLevel.SPECULATIVE
                ):
                    claim.confidence = ConfidenceLevel.LOW
                high_risk_count += 1

        # Annotate synthesis answer with risk summary if needed
        if high_risk_count > 0:
            synthesis.answer += (
                f"\n\n⚠️ *{high_risk_count} claim(s) in this synthesis carry "
                f"elevated hallucination risk and have been marked LOW confidence. "
                f"Verify against primary sources before acting on them.*"
            )

        return synthesis

    def _compute_risk(self, claim: Claim) -> float:
        """
        Compute hallucination risk for a claim.

        Risk is higher when:
        - No grounding source exists
        - Evidence level is speculative
        - Confidence is already low
        """
        base_risk = 1.0 - claim.hallucination_risk  # invert existing score as base

        evidence_penalty = {
            EvidenceLevel.EMPIRICAL: 0.0,
            EvidenceLevel.CROSS_TRADITION: 0.05,
            EvidenceLevel.LINEAGE: 0.15,
            EvidenceLevel.GAIAN_OBSERVED: 0.30,
            EvidenceLevel.SPECULATIVE: 0.60,
        }.get(claim.evidence_level, 0.40)

        grounding_penalty = 0.0 if claim.is_grounded else 0.50

        risk = min(1.0, evidence_penalty + grounding_penalty)
        return round(risk, 4)

    def get_summary(self, synthesis: SynthesisResult) -> dict:
        """Return a summary of claim quality across the synthesis."""
        if not synthesis.claims:
            return {"total": 0, "grounded": 0, "high_risk": 0, "speculative": 0}

        return {
            "total": len(synthesis.claims),
            "grounded": sum(1 for c in synthesis.claims if c.is_grounded),
            "high_risk": sum(
                1 for c in synthesis.claims
                if c.hallucination_risk >= HALLUCINATION_RISK_HIGH
            ),
            "speculative": sum(
                1 for c in synthesis.claims
                if c.confidence == ConfidenceLevel.SPECULATIVE
            ),
            "avg_hallucination_risk": round(
                sum(c.hallucination_risk for c in synthesis.claims) / len(synthesis.claims), 4
            )
        }
