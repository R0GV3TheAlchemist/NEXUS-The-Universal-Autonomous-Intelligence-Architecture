"""Memory Retrieval Engine — Canon C17: relevance-ranked memory retrieval.

The retrieval engine is GAIA's ability to recall what is relevant NOW.
It queries across M1 (Episodic), M2 (Semantic), and M3 (Identity)
simultaneously and returns a ranked list of memory records.

Ranking is based on:
  - Tag match score (exact tag matches score highest)
  - Recency (more recent = slightly higher rank, configurable)
  - Confidence (higher confidence = higher rank)
  - Layer priority (M3 > M2 > M1 for identity-relevant queries)

This is the foundation for Canon C499's Context Injection Protocol:
the retrieval engine feeds Layer 4 (Canon Core) and Layer 2 (Gaian Twin)
of the injection stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .layers import MemoryLayer, MemoryRecord, MemoryTag
from .episodic import EpisodicMemoryStore
from .semantic import SemanticMemoryStore
from .identity import IdentityMemoryStore


# Layer priority weights for ranking
_LAYER_WEIGHT: dict[MemoryLayer, float] = {
    MemoryLayer.M3_IDENTITY: 1.0,
    MemoryLayer.M2_SEMANTIC: 0.85,
    MemoryLayer.M1_EPISODIC: 0.70,
    MemoryLayer.M0_SESSION: 0.50,
    MemoryLayer.M4_SHARED: 0.60,
}


@dataclass
class RetrievalQuery:
    """A structured query to the memory retrieval engine."""
    text: str = ""                                    # Natural language query text
    tags: list[MemoryTag] = field(default_factory=list)   # Required tags (OR logic)
    required_tags: list[MemoryTag] = field(default_factory=list)  # Must ALL be present
    layers: list[MemoryLayer] = field(default_factory=list)       # If empty: all layers
    min_confidence: float = 0.0                       # Minimum confidence threshold
    max_results: int = 20                             # Cap on returned records
    recency_weight: float = 0.3                       # 0.0 = ignore recency, 1.0 = recency-only
    include_session_id: Optional[str] = None          # Boost records from a specific session


@dataclass
class RankedMemory:
    """A memory record with its computed relevance score for a specific query."""
    record: MemoryRecord
    score: float = 0.0
    matched_tags: list[MemoryTag] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"<RankedMemory score={self.score:.3f} "
            f"layer={self.record.layer.value} id={self.record.id[:8]}>"
        )


class MemoryRetrievalEngine:
    """Cross-layer relevance-ranked memory retrieval.

    Queries M1, M2, and M3 simultaneously.
    Returns a ranked list of RankedMemory objects.
    """

    def __init__(
        self,
        episodic: EpisodicMemoryStore,
        semantic: SemanticMemoryStore,
        identity: IdentityMemoryStore,
    ) -> None:
        self._episodic = episodic
        self._semantic = semantic
        self._identity = identity

    def retrieve(self, query: RetrievalQuery) -> list[RankedMemory]:
        """Execute a retrieval query. Returns records sorted by score descending."""
        candidates: list[MemoryRecord] = []

        # Gather candidates from requested layers (or all if unspecified)
        active_layers = set(query.layers) if query.layers else {
            MemoryLayer.M1_EPISODIC,
            MemoryLayer.M2_SEMANTIC,
            MemoryLayer.M3_IDENTITY,
        }

        if MemoryLayer.M1_EPISODIC in active_layers:
            candidates += self._episodic.all(active_only=True)
        if MemoryLayer.M2_SEMANTIC in active_layers:
            candidates += self._semantic.all(active_only=True)
        if MemoryLayer.M3_IDENTITY in active_layers and not self._identity.is_terminated:
            candidates += self._identity.all(active_only=True)

        # Apply minimum confidence filter
        if query.min_confidence > 0:
            candidates = [c for c in candidates if c.confidence >= query.min_confidence]

        # Apply required_tags filter (ALL must be present)
        if query.required_tags:
            candidates = [
                c for c in candidates
                if all(t in c.tags for t in query.required_tags)
            ]

        # Score candidates
        ranked = []
        for record in candidates:
            score, matched = self._score(record, query)
            if score > 0 or not query.tags:  # Include all if no tag filter
                ranked.append(RankedMemory(record=record, score=score, matched_tags=matched))

        # Sort by score descending
        ranked.sort(key=lambda x: x.score, reverse=True)

        return ranked[:query.max_results]

    def _score(self, record: MemoryRecord, query: RetrievalQuery) -> tuple[float, list[MemoryTag]]:
        """Compute relevance score for a record against a query."""
        score = 0.0
        matched_tags: list[MemoryTag] = []

        # Layer weight (M3 > M2 > M1)
        layer_weight = _LAYER_WEIGHT.get(record.layer, 0.5)
        score += layer_weight * 0.3

        # Tag matching (OR logic on query.tags)
        if query.tags:
            for tag in query.tags:
                if tag in record.tags:
                    matched_tags.append(tag)
            tag_score = len(matched_tags) / max(len(query.tags), 1)
            score += tag_score * 0.5
        else:
            # No tag filter — use confidence as proxy
            score += record.confidence * 0.4

        # Confidence contribution
        score += record.confidence * 0.1

        # Recency boost
        if query.recency_weight > 0:
            max_age_days = 365.0
            recency = max(0.0, 1.0 - (record.age_days / max_age_days))
            score += recency * query.recency_weight * 0.1

        # Session boost
        if query.include_session_id and record.session_id == query.include_session_id:
            score += 0.1

        return round(score, 4), matched_tags

    def retrieve_by_tags(
        self,
        tags: list[MemoryTag],
        max_results: int = 10,
        min_confidence: float = 0.0,
    ) -> list[RankedMemory]:
        """Convenience method: retrieve by tags only."""
        return self.retrieve(RetrievalQuery(
            tags=tags,
            max_results=max_results,
            min_confidence=min_confidence,
        ))

    def retrieve_breakthroughs(self, max_results: int = 5) -> list[RankedMemory]:
        """Retrieve the most significant breakthrough memories."""
        return self.retrieve_by_tags(
            tags=[MemoryTag.BREAKTHROUGH],
            max_results=max_results,
            min_confidence=0.8,
        )

    def retrieve_preferences(self, max_results: int = 10) -> list[RankedMemory]:
        """Retrieve stated preferences and boundaries."""
        return self.retrieve_by_tags(
            tags=[MemoryTag.PREFERENCE],
            max_results=max_results,
        )
