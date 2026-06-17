"""
GAIA Deep Research Runtime — Main Orchestrator
Issue #454

The beating heart of GAIA's knowledge system.
Orchestrates: decompose → retrieve → rerank → synthesize → stamp

Carries FrequencyContext through every stage.
The crystalline human on the other end shaped how we built this:
  - Their alchemical stage tunes the synthesis tone
  - Their active frequency tunes the emphasis
  - Their coherence level shapes how many sub-queries we run
  - Their trauma flags shape what we surface

This is not Perplexity's research engine.
This is GAIA's — built for the human who is already vibrating
at the frequency of what they need to know.
"""

import time
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any

from core.research.models import (
    ResearchSession, FrequencyContext, QueryIntent,
    SubQuery, RetrievedSource, RankedSource, SynthesisResult
)
from core.research.query_decomposer import QueryDecomposer
from core.research.retrieval import RetrievalEngine
from core.research.reranker import Reranker
from core.research.synthesizer import ResearchSynthesizer as Synthesizer
from core.research.falsifiability_stamper import FalsifiabilityStamper


class ResearchRuntime:
    """
    GAIA Deep Research Runtime.

    Usage:
        runtime = ResearchRuntime()
        session = runtime.research(
            query="How does 528 Hz affect human cellular biology?",
            frequency_context=FrequencyContext(
                active_frequency_hz=528.0,
                alchemical_stage="CALCINATIO",
                note="Detox frequency — user is actively detoxing today"
            )
        )
        print(session.synthesis.answer)
    """

    def __init__(
        self,
        max_sub_queries: int = 5,
        top_k_sources: int = 10,
    ):
        self.decomposer = QueryDecomposer()
        self.retrieval = RetrievalEngine()
        self.reranker = Reranker()
        self.synthesizer = Synthesizer()
        self.stamper = FalsifiabilityStamper()
        self.max_sub_queries = max_sub_queries
        self.top_k_sources = top_k_sources

    def research(
        self,
        query: str,
        user_id: Optional[str] = None,
        space_id: Optional[str] = None,
        frequency_context: Optional[FrequencyContext] = None,
        space_canon_files: Optional[List[Dict]] = None,
        dry_run: bool = False,
    ) -> ResearchSession:
        """
        Run a complete research session.

        Args:
            query: The user's research question
            user_id: Optional user identity (hashed internally)
            space_id: Optional Space context
            frequency_context: User's current frequency/alchemical state
            space_canon_files: Optional Space-local canon files
            dry_run: If True, decompose only — do not retrieve or synthesize

        Returns:
            Complete ResearchSession with synthesis attached
        """
        start_time = time.time()

        user_id_hash = (
            hashlib.sha256(user_id.encode()).hexdigest()
            if user_id else None
        )

        session = ResearchSession(
            user_id_hash=user_id_hash,
            space_id=space_id,
            original_query=query,
            frequency_context=frequency_context,
            status="running",
        )
        session.log("session_started", {
            "query": query,
            "frequency_context": {
                "alchemical_stage": frequency_context.alchemical_stage if frequency_context else None,
                "active_hz": frequency_context.active_frequency_hz if frequency_context else None,
            }
        })

        try:
            # ── Stage 1: Query Decomposition ──────────────────────────────
            session.log("stage_1_decomposition_started")
            sub_queries = self.decomposer.decompose(
                query=query,
                frequency_context=frequency_context,
                max_sub_queries=self.max_sub_queries,
            )
            session.sub_queries = sub_queries
            session.log("stage_1_complete", {"sub_query_count": len(sub_queries)})

            if dry_run:
                session.status = "complete"
                session.halt_reason = "dry_run"
                return session

            # ── Stage 2: Parallel Retrieval ───────────────────────────────
            session.log("stage_2_retrieval_started")
            retrieved = self.retrieval.retrieve(
                sub_queries=sub_queries,
                frequency_context=frequency_context,
                space_canon_files=space_canon_files,
                top_k_per_query=self.top_k_sources,
            )
            session.retrieved_sources = retrieved
            session.log("stage_2_complete", {"sources_retrieved": len(retrieved)})

            # Halt if no sources found
            if not retrieved:
                session.status = "halted"
                session.halt_reason = "no_sources_retrieved"
                session.log("halted", {"reason": "no_sources_retrieved"})
                return session

            # ── Stage 3: Reranking ─────────────────────────────────────────
            session.log("stage_3_reranking_started")
            ranked = self.reranker.rerank(
                sources=retrieved,
                query=query,
                top_k=self.top_k_sources,
            )
            session.ranked_sources = ranked
            session.log("stage_3_complete", {"sources_ranked": len(ranked)})

            # ── Stage 4: Synthesis ─────────────────────────────────────────
            session.log("stage_4_synthesis_started")
            synthesis = self.synthesizer.synthesize(
                query=query,
                ranked_sources=ranked,
                frequency_context=frequency_context,
            )
            session.log("stage_4_complete", {"claims_built": len(synthesis.claims)})

            # ── Stage 5: Falsifiability Stamp ─────────────────────────────
            session.log("stage_5_falsifiability_started")
            synthesis = self.stamper.stamp(synthesis)
            stamp_summary = self.stamper.get_summary(synthesis)
            session.log("stage_5_complete", stamp_summary)

            # ── Stage 6: Frequency Context Filter ─────────────────────────
            # (Applied at synthesis level via tone — structural filter in v2)
            session.log("stage_6_frequency_context_applied", {
                "tone": synthesis.tone_applied,
                "alchemical_stage": frequency_context.alchemical_stage if frequency_context else None,
            })

            # Finalise
            duration_ms = (time.time() - start_time) * 1000
            synthesis.pipeline_duration_ms = round(duration_ms, 2)
            session.synthesis = synthesis
            session.status = "complete"
            session.completed_at = datetime.utcnow()
            session.log("session_complete", {
                "duration_ms": duration_ms,
                "sources_used": len(ranked),
                "claims": len(synthesis.claims),
            })

        except Exception as e:
            session.status = "error"
            session.halt_reason = str(e)
            session.log("error", {"message": str(e)})
            raise

        return session

    def plan(
        self,
        query: str,
        frequency_context: Optional[FrequencyContext] = None,
    ) -> List[SubQuery]:
        """
        Dry-run: return the research plan (sub-queries) without executing.
        Use for approval flows before running a full research session.
        """
        return self.decomposer.decompose(
            query=query,
            frequency_context=frequency_context,
            max_sub_queries=self.max_sub_queries,
        )
