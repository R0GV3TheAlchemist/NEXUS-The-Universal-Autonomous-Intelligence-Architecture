"""
GAIA Deep Research Runtime — Reranker
Issue #454

Scores retrieved sources by:
  - Relevance (semantic token overlap, v1)
  - Authority (source tier)
  - Evidence level (empirical > speculative)
  - Recency (newer for factual; older for traditional)

GAIA Canon sources always score highest on authority.
Falsifiability-aware: sources with stronger evidence levels
rank higher — because honesty matters more than volume.
"""

import math
from datetime import datetime
from typing import List
from core.research.models import (
    RetrievedSource, RankedSource, SourceType, EvidenceLevel
)


# Authority weights — Tier 1 (GAIA Canon) is sovereign
AUTHORITY_WEIGHTS: dict = {
    SourceType.GAIA_CANON: 1.0,
    SourceType.SCIENTIFIC_LITERATURE: 0.85,
    SourceType.TRADITIONAL_SOURCE: 0.65,
    SourceType.GAIAN_OBSERVED: 0.50,
    SourceType.WEB: 0.35,
}

# Evidence weights — empirical knowledge is more stable
EVIDENCE_WEIGHTS: dict = {
    EvidenceLevel.EMPIRICAL: 1.0,
    EvidenceLevel.CROSS_TRADITION: 0.80,
    EvidenceLevel.LINEAGE: 0.65,
    EvidenceLevel.GAIAN_OBSERVED: 0.50,
    EvidenceLevel.SPECULATIVE: 0.25,
}

# Composite score weights
WEIGHT_RELEVANCE = 0.35
WEIGHT_AUTHORITY = 0.30
WEIGHT_EVIDENCE = 0.25
WEIGHT_RECENCY = 0.10


class Reranker:
    """
    Multi-signal reranker for the GAIA Deep Research Runtime.
    Returns sources sorted by composite_score descending.
    """

    def rerank(
        self,
        sources: List[RetrievedSource],
        query: str,
        top_k: int = 10,
    ) -> List[RankedSource]:
        """
        Score and rank all retrieved sources.
        Returns top_k RankedSource objects sorted by composite_score.
        """
        ranked = []
        for source in sources:
            relevance = self._relevance_score(source, query)
            authority = AUTHORITY_WEIGHTS.get(source.source_type, 0.3)
            evidence = EVIDENCE_WEIGHTS.get(source.evidence_level, 0.25)
            recency = self._recency_score(source)

            composite = (
                WEIGHT_RELEVANCE * relevance
                + WEIGHT_AUTHORITY * authority
                + WEIGHT_EVIDENCE * evidence
                + WEIGHT_RECENCY * recency
            )

            ranked.append(RankedSource(
                source=source,
                relevance_score=round(relevance, 4),
                authority_score=round(authority, 4),
                evidence_score=round(evidence, 4),
                recency_score=round(recency, 4),
                composite_score=round(composite, 4),
            ))

        ranked.sort(key=lambda r: r.composite_score, reverse=True)
        return ranked[:top_k]

    def _relevance_score(self, source: RetrievedSource, query: str) -> float:
        """
        v1: Token overlap between query and source content.
        v2: Replace with cosine similarity on embedding vectors.
        """
        query_tokens = set(query.lower().split())
        content_tokens = set((source.title + " " + source.content).lower().split())
        if not query_tokens:
            return 0.0
        overlap = len(query_tokens & content_tokens)
        # Normalised by query length — penalise very short overlap
        score = overlap / math.sqrt(len(query_tokens))
        return min(1.0, score / 3.0)  # Scale to [0, 1]

    def _recency_score(self, source: RetrievedSource) -> float:
        """
        Recency scoring:
        - For GAIA_CANON and TRADITIONAL_SOURCE: older = more authoritative (inverse recency)
        - For SCIENTIFIC_LITERATURE and WEB: newer = better
        - Retrieved_at used as proxy for publication date in v1
        """
        days_old = (datetime.utcnow() - source.retrieved_at).days

        if source.source_type in (SourceType.GAIA_CANON, SourceType.TRADITIONAL_SOURCE):
            # Timeless sources: always score 1.0 for recency dimension
            return 1.0

        # Exponential decay for web/scientific — fresh is better
        # Half-life: 365 days for scientific, 30 days for web
        half_life = 365 if source.source_type == SourceType.SCIENTIFIC_LITERATURE else 30
        lam = math.log(2) / half_life
        return round(math.exp(-lam * days_old), 4)
