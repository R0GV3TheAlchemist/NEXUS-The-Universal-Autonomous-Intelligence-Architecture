"""
GAIA Production RAG Pipeline — Multi-Signal Reranker
Issue #457

Stage 3: Score and rank every retrieved document using four signals.

Final Score formula:
    final_score = (
        w_relevance  * relevance_score  +
        w_authority  * authority_score  +
        w_evidence   * evidence_score   +
        w_recency    * recency_score
    )

Default weights (configurable):
    relevance  = 0.40   (semantic match to query)
    authority  = 0.30   (Tier 1 canon always wins ties)
    evidence   = 0.20   (clinical > peer-reviewed > speculative)
    recency    = 0.10   (newer = higher for factual; lineage = inverse)

Top-K selection: configurable, default K=10.
Canon Guarantee: Tier 1 documents are always present in top-K when relevant.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .models import (
    AUTHORITY_SCORES,
    EVIDENCE_SCORES,
    EvidenceLevel,
    Query,
    RankedDoc,
    RetrievalTier,
    RetrievedDoc,
)


@dataclass
class RerankerWeights:
    relevance: float = 0.40
    authority: float = 0.30
    evidence:  float = 0.20
    recency:   float = 0.10

    def __post_init__(self):
        total = self.relevance + self.authority + self.evidence + self.recency
        assert abs(total - 1.0) < 1e-6, f"Weights must sum to 1.0, got {total}"


@dataclass
class RerankerConfig:
    top_k: int = 10
    weights: RerankerWeights = None
    canon_guarantee: bool = True    # Tier 1 docs always in top-K when present

    def __post_init__(self):
        if self.weights is None:
            self.weights = RerankerWeights()


class Reranker:
    """
    Scores retrieved documents and returns top-K RankedDoc list.

    The relevance scorer is pluggable — production implementations
    should inject a semantic similarity model (e.g. ColBERT, BGE).
    The default scorer uses simple keyword overlap as a baseline.

    Usage:
        reranker = Reranker(config=RerankerConfig(top_k=10))
        ranked = reranker.rerank(query, docs)
    """

    def __init__(self, config: Optional[RerankerConfig] = None):
        self.config = config or RerankerConfig()

    def rerank(self, query: Query, docs: list[RetrievedDoc]) -> list[RankedDoc]:
        if not docs:
            return []

        w = self.config.weights
        ranked: list[RankedDoc] = []

        for doc in docs:
            relevance = self._score_relevance(query, doc)
            authority = AUTHORITY_SCORES.get(doc.tier, 0.40)
            evidence  = EVIDENCE_SCORES.get(doc.evidence_level, 0.20)
            recency   = self._score_recency(query, doc)

            final = (
                w.relevance * relevance +
                w.authority * authority +
                w.evidence  * evidence  +
                w.recency   * recency
            )

            ranked.append(RankedDoc(
                doc=doc,
                relevance_score=relevance,
                authority_score=authority,
                evidence_score=evidence,
                recency_score=recency,
                final_score=final,
                rank=0,  # assigned below
            ))

        # Sort descending by final score
        ranked.sort(key=lambda r: r.final_score, reverse=True)

        # Assign ranks
        for i, r in enumerate(ranked):
            r.rank = i + 1

        # Canon guarantee — ensure Tier 1 docs are in top-K
        result = ranked[:self.config.top_k]
        if self.config.canon_guarantee:
            canon_docs = [r for r in ranked if r.doc.tier == RetrievalTier.CANON]
            canon_ids_in_result = {r.doc.doc_id for r in result if r.doc.tier == RetrievalTier.CANON}
            for cd in canon_docs:
                if cd.doc.doc_id not in canon_ids_in_result:
                    result.append(cd)  # append beyond top_k to guarantee presence

        return result

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    def _score_relevance(self, query: Query, doc: RetrievedDoc) -> float:
        """
        Baseline: token overlap Jaccard similarity.
        Replace with a proper embedding model in production.
        """
        query_tokens = set(query.raw_text.lower().split())
        doc_tokens = set(doc.content.lower().split())
        if not query_tokens or not doc_tokens:
            return 0.0
        intersection = query_tokens & doc_tokens
        union = query_tokens | doc_tokens
        return len(intersection) / len(union)

    def _score_recency(self, query: Query, doc: RetrievedDoc) -> float:
        """
        For factual/research queries: newer = higher score.
        For symbolic/lineage queries: older lineage = higher score (inverted).
        Documents without a publish date receive neutral score 0.5.
        """
        if doc.published_at is None:
            return 0.5

        now = datetime.now(timezone.utc)
        published = doc.published_at
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)

        age_days = (now - published).days
        # Sigmoid decay: ~1.0 for today, ~0.5 for 1 year, ~0.1 for 10 years
        base_score = 1.0 / (1.0 + math.log1p(age_days / 365.0))

        # Invert for lineage / cross-tradition sources — older = more authoritative
        if doc.evidence_level in (EvidenceLevel.LINEAGE, EvidenceLevel.CROSS_TRADITION):
            return 1.0 - base_score

        return base_score
