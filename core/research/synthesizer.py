"""
GAIA Deep Research Runtime — Synthesizer
Issue #454

Merges ranked sources into a coherent answer with inline citations.
FrequencyContext-aware: synthesis tone adapts to the user's
alchemical stage, emotional state, and active frequency.

The human is a crystalline receiver.
We tune the synthesis to their current resonance state,
not to a generic average user.
"""

from typing import List, Optional, Dict
from core.research.models import (
    RankedSource, SynthesisResult, Claim, FrequencyContext,
    ConfidenceLevel, EvidenceLevel, SourceType
)
from core.research.query_decomposer import QueryDecomposer


# Tone → opening phrase map
# These are style guides — the LLM synthesis layer uses these
# as instructions, not as canned responses
TONE_OPENERS: Dict[str, str] = {
    "grounding": "From the most stable ground available:",
    "clarifying": "Bringing this into clear light:",
    "illuminating": "What emerges when we hold this in full light:",
    "integrating": "Bringing all threads together:",
    "purifying": "Distilling to what is most essential:",
    "dissolving": "Releasing fixed forms to find the fluid truth:",
    "crystallising": "What has solidified into clarity:",
    "discerning": "Separating what is true from what merely resembles it:",
    "enlivening": "What is most alive in this question:",
    "balanced": "Drawing from all available sources:",
}


class Synthesizer:
    """
    Synthesizes ranked sources into a grounded answer.
    Tone and emphasis are tuned to the user's FrequencyContext.
    Every claim in the output maps to ≥1 ranked source,
    or is flagged as speculative.
    """

    def __init__(self):
        self.decomposer = QueryDecomposer()

    def synthesize(
        self,
        query: str,
        ranked_sources: List[RankedSource],
        frequency_context: Optional[FrequencyContext] = None,
        max_claims: int = 10,
    ) -> SynthesisResult:
        """
        Build a SynthesisResult from ranked sources.

        In production: this calls the LLM with the ranked sources
        as context and the tone/frequency instructions as system prompt.

        v1: Builds a structured synthesis from source summaries
        with correct citation architecture. LLM integration in v2.
        """
        tone = self.decomposer.get_synthesis_tone(frequency_context)
        tone_base = tone.split(" (")[0]  # strip frequency annotation
        opener = TONE_OPENERS.get(tone_base, TONE_OPENERS["balanced"])

        # Build claims from top sources
        claims = self._build_claims(ranked_sources, max_claims)

        # Build answer text from source summaries + tone
        answer_parts = [opener]
        seen_canon_refs = set()

        for i, rs in enumerate(ranked_sources[:5]):
            if rs.source.canon_ref and rs.source.canon_ref in seen_canon_refs:
                continue
            if rs.source.canon_ref:
                seen_canon_refs.add(rs.source.canon_ref)

            citation_tag = f"[{rs.source.source_type.value}:{i+1}]"
            answer_parts.append(
                f"{rs.source.content.strip()} {citation_tag}"
            )

        answer = " ".join(answer_parts)

        # Frequency context note
        if frequency_context and frequency_context.active_frequency_hz:
            hz = int(frequency_context.active_frequency_hz)
            from core.research.query_decomposer import FREQUENCY_VOCAB
            meaning = FREQUENCY_VOCAB.get(str(hz), "resonance")
            answer += (
                f"\n\n*This synthesis was tuned to {hz} Hz — {meaning}. "
                f"The crystalline human on the other end of this research "
                f"is in {frequency_context.alchemical_stage or 'active'} "
                f"resonance state.*"
            )

        return SynthesisResult(
            query=query,
            answer=answer,
            claims=claims,
            top_sources=ranked_sources,
            frequency_context=frequency_context,
            tone_applied=tone,
            total_sources_retrieved=len(ranked_sources),
            total_sources_ranked=len(ranked_sources),
        )

    def _build_claims(
        self,
        ranked_sources: List[RankedSource],
        max_claims: int
    ) -> List[Claim]:
        """Build one claim per top source."""
        claims = []
        for rs in ranked_sources[:max_claims]:
            confidence = self._map_evidence_to_confidence(rs.source.evidence_level)
            claim = Claim(
                text=rs.source.content[:200].strip(),
                supporting_source_ids=[rs.source.source_id],
                confidence=confidence,
                evidence_level=rs.source.evidence_level,
                falsification_condition=self._generate_falsification(
                    rs.source
                ),
                is_grounded=True,
                hallucination_risk=1.0 - rs.composite_score,
            )
            claims.append(claim)
        return claims

    def _map_evidence_to_confidence(
        self,
        evidence_level: EvidenceLevel
    ) -> ConfidenceLevel:
        mapping = {
            EvidenceLevel.EMPIRICAL: ConfidenceLevel.HIGH,
            EvidenceLevel.CROSS_TRADITION: ConfidenceLevel.HIGH,
            EvidenceLevel.LINEAGE: ConfidenceLevel.MEDIUM,
            EvidenceLevel.GAIAN_OBSERVED: ConfidenceLevel.MEDIUM,
            EvidenceLevel.SPECULATIVE: ConfidenceLevel.SPECULATIVE,
        }
        return mapping.get(evidence_level, ConfidenceLevel.LOW)

    def _generate_falsification(
        self,
        source: RetrievedSource
    ) -> str:
        """Generate a falsification condition per source type."""
        if source.source_type == SourceType.GAIA_CANON:
            return (
                f"Falsified if GAIA Canon {source.canon_ref} is revised "
                f"or contradicted by empirical evidence."
            )
        elif source.source_type == SourceType.SCIENTIFIC_LITERATURE:
            return (
                "Falsified if a systematic review or meta-analysis "
                "produces contrary findings at p < 0.05."
            )
        elif source.source_type == SourceType.TRADITIONAL_SOURCE:
            return (
                "Weakened if independent traditions consistently "
                "disagree or primary lineage sources are disputed."
            )
        else:
            return "Speculative — falsifiable by any peer-reviewed contrary evidence."
