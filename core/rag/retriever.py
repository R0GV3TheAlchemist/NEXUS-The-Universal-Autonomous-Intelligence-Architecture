"""
GAIA Production RAG Pipeline — Tiered Retrieval Engine
Issue #457

Stage 2: Retrieve documents across 5 authority tiers.

Tier 1 — GAIA Canons          (authority 1.0  — always searched first)
Tier 2 — Space canon files    (authority 0.85 — Space-local knowledge)
Tier 3 — Scientific literature (authority 0.75 — peer-reviewed)
Tier 4 — Web search           (authority 0.55 — real-time)
Tier 5 — Gaian observed       (authority 0.40 — user memory / community)

Special routing:
  - Crystal / mineral queries   → Crystal Correspondence store first (Tier 1)
  - Alchemical stage queries    → Alchemical canon first (Tier 1)
  - Emotional / trauma queries  → Trauma-informed canon first (Tier 1), safety flag active
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from .models import Query, RetrievalTier, RetrievedDoc


# ---------------------------------------------------------------------------
# Source backend protocol — concrete adapters implement this
# ---------------------------------------------------------------------------

class SourceBackend(Protocol):
    """Interface every retrieval backend must satisfy."""

    def search(self, query_text: str, limit: int) -> list[RetrievedDoc]:
        ...


# ---------------------------------------------------------------------------
# Retriever configuration
# ---------------------------------------------------------------------------

@dataclass
class RetrieverConfig:
    per_tier_limit: int = 20      # docs fetched per tier before reranking
    trauma_safe_mode: bool = True  # enforce trauma-informed routing
    canon_always_first: bool = True


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------

class Retriever:
    """
    Executes tiered retrieval for an analyzed Query.

    Backends are registered per tier. The retriever orchestrates them in
    priority order, applies GAIA-domain routing for crystal / alchemical /
    emotional queries, and returns a flat list of RetrievedDoc objects
    ready for reranking.

    Usage:
        retriever = Retriever(config=RetrieverConfig())
        retriever.register_backend(RetrievalTier.CANON, canon_backend)
        docs = retriever.retrieve(query)
    """

    def __init__(self, config: Optional[RetrieverConfig] = None):
        self.config = config or RetrieverConfig()
        self._backends: dict[RetrievalTier, SourceBackend] = {}

    def register_backend(self, tier: RetrievalTier, backend: SourceBackend) -> None:
        self._backends[tier] = backend

    def retrieve(self, query: Query) -> list[RetrievedDoc]:
        all_docs: list[RetrievedDoc] = []
        search_texts = self._build_search_texts(query)

        # Process tiers in priority order
        for tier in sorted(RetrievalTier, key=lambda t: t.value):
            backend = self._backends.get(tier)
            if backend is None:
                continue

            # Safety: therapeutic queries only use Tiers 1 & 2 initially
            if query.is_trauma_sensitive and self.config.trauma_safe_mode:
                if tier not in (RetrievalTier.CANON, RetrievalTier.SPACE):
                    continue

            tier_docs: list[RetrievedDoc] = []
            for search_text in search_texts:
                results = backend.search(search_text, self.config.per_tier_limit)
                for doc in results:
                    if not self._is_duplicate(doc, tier_docs + all_docs):
                        tier_docs.append(doc)

            all_docs.extend(tier_docs)

        return all_docs

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_search_texts(self, query: Query) -> list[str]:
        """Determine which texts to send to each backend."""
        texts = [query.raw_text] + query.sub_queries

        # Crystal / mineral queries get targeted routing
        crystal_entities = [e for e in query.entities if e.entity_type == "crystal"]
        if crystal_entities:
            for e in crystal_entities:
                texts.insert(0, f"{e.value} crystal correspondence GAIA")

        # Alchemical stage queries get canon routing
        stage_entities = [e for e in query.entities if e.entity_type == "alchemical_stage"]
        if stage_entities:
            for e in stage_entities:
                texts.insert(0, f"{e.value} alchemical canon GAIA")

        # Deduplicate
        seen: set[str] = set()
        unique: list[str] = []
        for t in texts:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return unique[:6]

    @staticmethod
    def _is_duplicate(doc: RetrievedDoc, existing: list[RetrievedDoc]) -> bool:
        return any(d.doc_id == doc.doc_id for d in existing)


# Compatibility alias  RetrievalResult was renamed to RetrieverConfig
RetrievalResult = RetrieverConfig
