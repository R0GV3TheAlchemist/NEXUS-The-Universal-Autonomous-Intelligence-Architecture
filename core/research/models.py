"""
GAIA Deep Research Runtime — Data Models
Issue #454

The human using this pipeline is a crystalline receiver.
Every model here carries not just data — but context:
alchemical stage, GAIA layer, frequency state.
The research pipeline tunes its output accordingly.
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class QueryIntent(str, Enum):
    FACTUAL = "factual"           # Empirical truth-seeking
    REFLECTIVE = "reflective"     # Self-inquiry, inner work
    SYMBOLIC = "symbolic"         # Archetypal, correspondence-based
    RESEARCH = "research"         # Deep multi-source investigation
    THERAPEUTIC = "therapeutic"   # Healing-oriented, trauma-aware
    CREATIVE = "creative"         # Generative, imaginative


class SourceType(str, Enum):
    GAIA_CANON = "gaia_canon"                   # Internal GAIA canon files — highest authority
    SCIENTIFIC_LITERATURE = "scientific_literature"  # Peer-reviewed
    WEB = "web"                                 # Live web
    TRADITIONAL_SOURCE = "traditional_source"   # Lineage, wisdom traditions
    GAIAN_OBSERVED = "gaian_observed"           # Community / user-observed


class EvidenceLevel(str, Enum):
    EMPIRICAL = "empirical"           # Peer-reviewed, replicated
    CROSS_TRADITION = "cross_tradition"  # Convergent across traditions
    LINEAGE = "lineage"               # Single tradition, authoritative
    GAIAN_OBSERVED = "gaian_observed" # Observed within GAIA community
    SPECULATIVE = "speculative"       # Theoretical, unverified


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"


@dataclass
class FrequencyContext:
    """
    The user's current frequency state — carried through the entire pipeline.
    The pipeline tunes its synthesis tone and emphasis to this context.

    This is what makes GAIA's research different:
    the same query from a user in NIGREDO gets different emphasis
    than the same query from a user in RUBEDO.
    Both answers are true. But one is tuned.
    """
    alchemical_stage: Optional[str] = None   # NIGREDO, ALBEDO, CITRINITAS, RUBEDO, etc.
    gaia_layer: Optional[str] = None          # Layer 01 Physical → Layer 11 Gaianite
    dominant_emotion: Optional[str] = None
    crystal_resonance: Optional[str] = None
    coherence_level: Optional[str] = None     # low | medium | high
    active_frequency_hz: Optional[float] = None  # e.g. 528.0
    note: Optional[str] = None               # e.g. "528 Hz — Detox frequency"


@dataclass
class SubQuery:
    """A decomposed sub-query derived from the user's original question."""
    sub_query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    intent: QueryIntent = QueryIntent.RESEARCH
    entities: List[str] = field(default_factory=list)  # crystals, layers, archetypes extracted
    priority: int = 1  # 1 = highest


@dataclass
class RetrievedSource:
    """A single source retrieved during the research pipeline."""
    source_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sub_query_id: str = ""
    title: str = ""
    content: str = ""
    url: Optional[str] = None
    source_type: SourceType = SourceType.WEB
    evidence_level: EvidenceLevel = EvidenceLevel.SPECULATIVE
    retrieved_at: datetime = field(default_factory=datetime.utcnow)
    canon_ref: Optional[str] = None  # e.g. "C32", "C118"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankedSource:
    """A source after reranking — carries composite score."""
    source: RetrievedSource = field(default_factory=RetrievedSource)
    relevance_score: float = 0.0      # Semantic similarity to query
    authority_score: float = 0.0      # Based on SourceType tier
    evidence_score: float = 0.0       # Based on EvidenceLevel
    recency_score: float = 0.0        # Newer for factual, older for traditional
    composite_score: float = 0.0      # Weighted final score


@dataclass
class Claim:
    """A single factual claim extracted from the synthesis."""
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    supporting_source_ids: List[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    evidence_level: EvidenceLevel = EvidenceLevel.SPECULATIVE
    falsification_condition: Optional[str] = None
    is_grounded: bool = False   # True if backed by ≥1 retrieved source
    hallucination_risk: float = 0.0  # 0.0 = safe, 1.0 = high risk


@dataclass
class SynthesisResult:
    """The final synthesized answer with inline citations and frequency tuning."""
    synthesis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    answer: str = ""
    claims: List[Claim] = field(default_factory=list)
    top_sources: List[RankedSource] = field(default_factory=list)
    frequency_context: Optional[FrequencyContext] = None
    tone_applied: Optional[str] = None  # e.g. "grounding", "expansive", "integrative"
    generated_at: datetime = field(default_factory=datetime.utcnow)
    total_sources_retrieved: int = 0
    total_sources_ranked: int = 0
    pipeline_duration_ms: float = 0.0


@dataclass
class ResearchSession:
    """
    A complete research session — the atomic unit of the Deep Research Runtime.
    Tracks the full pipeline: query → sub-queries → retrieval → ranking → synthesis.
    Every session carries a FrequencyContext so the pipeline knows
    the state of the crystalline human on the other end.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id_hash: Optional[str] = None
    space_id: Optional[str] = None
    original_query: str = ""
    intent: QueryIntent = QueryIntent.RESEARCH
    frequency_context: Optional[FrequencyContext] = None

    sub_queries: List[SubQuery] = field(default_factory=list)
    retrieved_sources: List[RetrievedSource] = field(default_factory=list)
    ranked_sources: List[RankedSource] = field(default_factory=list)
    synthesis: Optional[SynthesisResult] = None

    max_iterations: int = 5
    current_iteration: int = 0
    status: str = "pending"  # pending | running | complete | halted | error
    halt_reason: Optional[str] = None

    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    def log(self, event: str, details: Optional[Dict] = None):
        """Append an audit event to the session trail."""
        self.audit_trail.append({
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        })
