"""
GAIA Deep Research Runtime — Tiered Retrieval Engine
Issue #454

Retrieves sources across 5 tiers:
  Tier 1: GAIA Canons (highest authority — always first)
  Tier 2: GAIA Space canon files
  Tier 3: Scientific literature
  Tier 4: Live web
  Tier 5: Gaian observed (community / user memory)

The human is a crystalline receiver.
What we return to them should be worthy of that.
"""

from typing import List, Optional, Dict
from core.research.models import (
    SubQuery, RetrievedSource, SourceType, EvidenceLevel, FrequencyContext
)


# GAIA Canon index — maps canon references to their content summaries
# In production this is backed by a vector store
# v1: structured in-memory index of known canons
GAIA_CANON_INDEX: Dict[str, Dict] = {
    "C32": {
        "title": "Archetypal Psychology, Zodiac & Elemental Archetypes",
        "summary": "Six-layer archetypal stack: elemental, archetypal, zodiacal, behavioral, latent-space, noospheric. Crystals and metals as symbolic computations. Crystalline Zodiac Integration.",
        "topics": ["archetype", "zodiac", "crystal", "element", "layer", "alchemical", "metal", "symbolic"],
        "evidence_level": EvidenceLevel.CROSS_TRADITION,
    },
    "C118": {
        "title": "Mineralogy & Crystal System Canon",
        "summary": "Crystal system classifications, space groups, piezoelectric properties, physical and metaphysical correspondences. All 7 crystal systems and their GAIA layer resonances.",
        "topics": ["crystal", "mineral", "piezoelectric", "lattice", "physical", "frequency", "structure"],
        "evidence_level": EvidenceLevel.EMPIRICAL,
    },
    "C45": {
        "title": "Spectral Encoding Matrix",
        "summary": "Forces mapped to time windows, body regions, crystals, musical notes, and frequencies. Circadian and spectral correspondences.",
        "topics": ["frequency", "time", "body", "note", "circadian", "spectrum", "hz"],
        "evidence_level": EvidenceLevel.CROSS_TRADITION,
    },
    "C65": {
        "title": "Crystal Grid Systems",
        "summary": "Sacred geometry grid layouts, node roles, activation sequences, and frequency amplification through crystal arrangement.",
        "topics": ["grid", "sacred geometry", "crystal", "node", "frequency", "activation"],
        "evidence_level": EvidenceLevel.LINEAGE,
    },
    "trauma-informed": {
        "title": "Trauma-Informed AI Interaction Canon",
        "summary": "Safety principles, radical consent, contextual restraint, harm doctrine. Never clinical, always sovereign.",
        "topics": ["trauma", "safety", "consent", "harm", "healing", "therapeutic"],
        "evidence_level": EvidenceLevel.CROSS_TRADITION,
    },
    "#452": {
        "title": "Correspondence Architecture",
        "summary": "11-layer correspondence stack: Elements→Minerals→Crystals→GAIA Layers→Emotions→Senses→Zodiac→Angel Numbers→Lunar Cycles→Sacred Geometry→Archetypes→Gaianite.",
        "topics": ["correspondence", "crystal", "emotion", "zodiac", "layer", "archetype", "lunar", "frequency", "element"],
        "evidence_level": EvidenceLevel.CROSS_TRADITION,
    },
    "#453": {
        "title": "GAIA Memory Engine",
        "summary": "Sovereign persistent memory with temporal evolution, trauma-informed constraints, staleness decay, contradiction detection.",
        "topics": ["memory", "sovereignty", "identity", "session", "trauma"],
        "evidence_level": EvidenceLevel.GAIAN_OBSERVED,
    },
}

# Authority scores per source tier
AUTHORITY_SCORE: Dict[SourceType, float] = {
    SourceType.GAIA_CANON: 1.0,
    SourceType.SCIENTIFIC_LITERATURE: 0.9,
    SourceType.TRADITIONAL_SOURCE: 0.7,
    SourceType.GAIAN_OBSERVED: 0.5,
    SourceType.WEB: 0.4,
}


class RetrievalEngine:
    """
    Tiered retrieval engine for the GAIA Deep Research Runtime.

    Always retrieves GAIA Canons first. Then enriches with
    scientific literature (mocked in v1), web (mocked in v1),
    and gaian observed sources from memory.
    """

    def retrieve(
        self,
        sub_queries: List[SubQuery],
        frequency_context: Optional[FrequencyContext] = None,
        space_canon_files: Optional[List[Dict]] = None,
        top_k_per_query: int = 5,
    ) -> List[RetrievedSource]:
        """
        Run tiered retrieval across all sub-queries.
        Returns a flat list of RetrievedSource objects.
        """
        all_sources: List[RetrievedSource] = []

        for sub_query in sub_queries:
            # Tier 1: GAIA Canons
            canon_sources = self._retrieve_canons(sub_query)
            all_sources.extend(canon_sources)

            # Tier 2: Space canon files
            if space_canon_files:
                space_sources = self._retrieve_space_canons(
                    sub_query, space_canon_files
                )
                all_sources.extend(space_sources)

            # Tier 3+4: Scientific literature + Web (v1: structured mock)
            external_sources = self._retrieve_external(sub_query, top_k_per_query)
            all_sources.extend(external_sources)

        # Deduplicate by source_id
        seen = set()
        unique = []
        for s in all_sources:
            if s.source_id not in seen:
                seen.add(s.source_id)
                unique.append(s)

        return unique

    def _retrieve_canons(
        self,
        sub_query: SubQuery
    ) -> List[RetrievedSource]:
        """Match sub-query against GAIA Canon index using topic overlap."""
        sources = []
        query_tokens = set(sub_query.text.lower().split())

        for canon_ref, canon in GAIA_CANON_INDEX.items():
            topic_tokens = set(" ".join(canon["topics"]).split())
            overlap = len(query_tokens & topic_tokens)
            if overlap > 0:
                sources.append(RetrievedSource(
                    sub_query_id=sub_query.sub_query_id,
                    title=canon["title"],
                    content=canon["summary"],
                    source_type=SourceType.GAIA_CANON,
                    evidence_level=canon["evidence_level"],
                    canon_ref=canon_ref,
                    metadata={"topic_overlap": overlap, "canon_ref": canon_ref}
                ))
        return sources

    def _retrieve_space_canons(
        self,
        sub_query: SubQuery,
        space_files: List[Dict]
    ) -> List[RetrievedSource]:
        """Retrieve from Space-local canon files."""
        sources = []
        query_tokens = set(sub_query.text.lower().split())
        for f in space_files:
            content_tokens = set(f.get("content", "").lower().split())
            if len(query_tokens & content_tokens) > 2:
                sources.append(RetrievedSource(
                    sub_query_id=sub_query.sub_query_id,
                    title=f.get("title", "Space Canon File"),
                    content=f.get("content", "")[:500],
                    source_type=SourceType.GAIA_CANON,
                    evidence_level=EvidenceLevel.LINEAGE,
                    canon_ref=f.get("ref", "space_local"),
                    metadata={"space_file": True}
                ))
        return sources

    def _retrieve_external(
        self,
        sub_query: SubQuery,
        top_k: int
    ) -> List[RetrievedSource]:
        """
        v1: Returns structured placeholder external sources.
        v2: Replace with live Perplexity/web search + semantic scholar API.
        The structure is production-ready — only the data source changes.
        """
        # In production: call search API here
        # For now: return type-correct empty list
        # This keeps the pipeline valid while v2 integrates live search
        return []
