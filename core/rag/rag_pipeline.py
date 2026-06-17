"""
GAIA Production RAG Pipeline — Main Orchestrator
Issue #457 | Priority-5

Full pipeline: Analyze → Retrieve → Rerank → Synthesize → Guard

This is the spine of GAIA's epistemic integrity. Every query that flows
through GAIA-OS passes through this pipeline to ensure:
  - Canon sources are always the highest-authority input
  - Every claim is grounded in retrieved evidence
  - Unsupported claims are flagged or removed
  - The synthesis tone respects the query's emotional and alchemical context
  - Trauma-sensitive queries are routed safely

Dependencies: #451 Falsification Protocol, #452 Correspondence Architecture,
              #453 Memory Engine, #454 Deep Research Runtime, #455 Spaces
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from .hallucination_guard import GuardConfig, HallucinationGuard
from .models import HallucinationRisk, Query, SynthesisResult
from .query_analyzer import QueryAnalyzer
from .reranker import Reranker, RerankerConfig  # noqa: F401 (alias)
from .reranker import Reranker, RerankerConfig
from .retriever import Retriever, RetrieverConfig
from .synthesizer import Synthesizer, SynthesizerConfig


@dataclass
class RAGPipelineConfig:
    retriever: RetrieverConfig = None
    reranker:  RerankerConfig  = None
    synthesizer: SynthesizerConfig = None
    guard: GuardConfig = None

    def __post_init__(self):
        if self.retriever is None:
            self.retriever = RetrieverConfig()
        if self.reranker is None:
            self.reranker = RerankerConfig()
        if self.synthesizer is None:
            self.synthesizer = SynthesizerConfig()
        if self.guard is None:
            self.guard = GuardConfig()


class RAGPipeline:
    """
    The GAIA Production RAG Pipeline.

    Usage:
        pipeline = RAGPipeline(config=RAGPipelineConfig())
        pipeline.retriever.register_backend(RetrievalTier.CANON, canon_backend)
        result = pipeline.run("What crystal supports NIGREDO shadow work?")

    The pipeline exposes each stage as a public attribute so individual
    stages can be tested, instrumented, or replaced independently.
    """

    def __init__(self, config: Optional[RAGPipelineConfig] = None):
        self.config = config or RAGPipelineConfig()

        self.analyzer    = QueryAnalyzer()
        self.retriever   = Retriever(config=self.config.retriever)
        self.reranker    = Reranker(config=self.config.reranker)
        self.synthesizer = Synthesizer(config=self.config.synthesizer)
        self.guard       = HallucinationGuard(config=self.config.guard)

    def run(
        self,
        raw_query: str,
        alchemical_stage_context: Optional[str] = None,
        gaia_layer_context: Optional[str] = None,
    ) -> SynthesisResult:
        """
        Execute the full 5-stage pipeline and return a SynthesisResult.

        Stages:
            1. Query Analysis      — intent, entities, sub-queries
            2. Tiered Retrieval    — Canon-first, 5 authority tiers
            3. Multi-signal Rerank — relevance × authority × evidence × recency
            4. Grounded Synthesis  — every claim mapped to a source
            5. Hallucination Guard — post-synthesis claim verification
        """
        start_ms = time.monotonic() * 1000

        # Stage 1 — Query Analysis
        query: Query = self.analyzer.analyze(
            raw_query,
            alchemical_stage_context=alchemical_stage_context,
            gaia_layer_context=gaia_layer_context,
        )

        # Stage 2 — Tiered Retrieval
        retrieved_docs = self.retriever.retrieve(query)

        # Stage 3 — Reranking
        ranked_docs = self.reranker.rerank(query, retrieved_docs)

        # Stage 4 — Grounded Synthesis
        answer_text, claims, citation_map, tone = self.synthesizer.synthesize(
            query, ranked_docs
        )

        # Assemble preliminary result
        result = SynthesisResult(
            query=query,
            answer_text=answer_text,
            tone=tone,
            claims=claims,
            top_k_docs=ranked_docs,
            citation_map=citation_map,
            hallucination_risk_overall=HallucinationRisk.NONE,
            speculative_claims_count=0,
            supported_claims_count=0,
            pipeline_duration_ms=0.0,
        )

        # Stage 5 — Anti-Hallucination Guard
        result = self.guard.evaluate(result)

        # Record total duration
        result.pipeline_duration_ms = (time.monotonic() * 1000) - start_ms

        return result

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def set_llm_adapter(self, adapter) -> None:
        """Inject LLM adapter into synthesizer."""
        self.synthesizer.set_llm_adapter(adapter)
