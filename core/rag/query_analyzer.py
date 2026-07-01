"""
GAIA Production RAG Pipeline — Query Analyzer
Issue #457

Stage 1: Analyze every incoming query before any retrieval occurs.

Responsibilities:
  - Classify query intent (factual / reflective / symbolic / research / therapeutic / creative)
  - Extract GAIA-domain entities (crystals, emotions, archetypes, GAIA layers, alchemical stages)
  - Expand the query into 3–5 sub-queries for broader retrieval coverage
  - Flag trauma-sensitive queries for safety routing
  - Inject current alchemical stage and GAIA layer context when available
"""

from __future__ import annotations

import re
from typing import Optional

from .models import GAIAEntity, Query, QueryIntent


# ---------------------------------------------------------------------------
# Intent classification keyword maps
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: dict[QueryIntent, list[str]] = {
    QueryIntent.THERAPEUTIC: [
        "trauma", "grief", "heal", "healing", "anxiety", "depression", "hurt",
        "loss", "wounded", "pain", "recovery", "support", "struggling",
    ],
    QueryIntent.SYMBOLIC: [
        "crystal", "mineral", "archetype", "zodiac", "angel number",
        "correspondence", "element", "alchemical", "lunar", "sacred geometry",
        "layer", "gaia layer", "resonance", "nigredo", "rubedo", "albedo",
    ],
    QueryIntent.REFLECTIVE: [
        "meaning", "purpose", "why am i", "what does it mean", "reflect",
        "contemplat", "journal", "understand myself", "inner", "shadow work",
    ],
    QueryIntent.RESEARCH: [
        "research", "study", "evidence", "science", "literature", "peer",
        "compare", "analysis", "survey", "overview", "history of",
    ],
    QueryIntent.CREATIVE: [
        "write", "create", "generate", "imagine", "story", "poem",
        "ritual", "design", "build", "craft",
    ],
}

# GAIA-domain entity patterns
_GAIA_LAYER_PATTERN = re.compile(
    r"layer\s*(0?[1-9]|1[0-2]|[a-z ]+)",
    re.IGNORECASE,
)
_ALCHEMICAL_STAGES = {
    "nigredo", "albedo", "citrinitas", "rubedo",
    "calcinatio", "solutio", "coagulatio", "separatio",
}
_CRYSTAL_NAMES = {
    "black tourmaline", "obsidian", "selenite", "amethyst", "rose quartz",
    "clear quartz", "citrine", "labradorite", "malachite", "pyrite",
    "carnelian", "moonstone", "lapis lazuli", "fluorite", "hematite",
    "smoky quartz", "emerald", "ruby", "sapphire", "aquamarine",
    # extend from Crystal Matrix v2 (#446) when available
}
_EMOTION_KEYWORDS = {
    "fear", "anger", "joy", "grief", "love", "shame", "guilt",
    "wonder", "awe", "disgust", "sadness", "anxiety", "peace",
}
_TRAUMA_SIGNALS = {
    "trauma", "abuse", "assault", "suicid", "self-harm", "overdose",
    "crisis", "ptsd", "dissociat",
}


class QueryAnalyzer:
    """
    Transforms a raw text query into an enriched Query object.

    Usage:
        analyzer = QueryAnalyzer()
        query = analyzer.analyze("What crystal supports shadow work in NIGREDO?")
    """

    def analyze(
        self,
        raw_text: str,
        alchemical_stage_context: Optional[str] = None,
        gaia_layer_context: Optional[str] = None,
    ) -> Query:
        text_lower = raw_text.lower()

        intent = self._classify_intent(text_lower)
        entities = self._extract_entities(text_lower)
        is_trauma_sensitive = self._detect_trauma(text_lower)
        sub_queries = self._expand_query(raw_text, intent, entities)

        return Query(
            raw_text=raw_text,
            intent=intent,
            entities=entities,
            sub_queries=sub_queries,
            is_trauma_sensitive=is_trauma_sensitive,
            alchemical_stage_context=alchemical_stage_context,
            gaia_layer_context=gaia_layer_context,
        )

    # ------------------------------------------------------------------
    # Intent classification
    # ------------------------------------------------------------------

    def _classify_intent(self, text_lower: str) -> QueryIntent:
        scores: dict[QueryIntent, int] = {intent: 0 for intent in QueryIntent}

        for intent, keywords in _INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[intent] += 1

        # Therapeutic overrides everything if signals present (safety first)
        if scores[QueryIntent.THERAPEUTIC] > 0:
            return QueryIntent.THERAPEUTIC

        best = max(scores, key=lambda k: scores[k])
        if scores[best] == 0:
            return QueryIntent.FACTUAL
        return best

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    def _extract_entities(self, text_lower: str) -> list[GAIAEntity]:
        entities: list[GAIAEntity] = []

        # Crystal names
        for crystal in _CRYSTAL_NAMES:
            if crystal in text_lower:
                entities.append(GAIAEntity("crystal", crystal.title()))

        # Alchemical stages
        for stage in _ALCHEMICAL_STAGES:
            if stage in text_lower:
                entities.append(GAIAEntity("alchemical_stage", stage.upper()))

        # GAIA layers
        for match in _GAIA_LAYER_PATTERN.finditer(text_lower):
            entities.append(GAIAEntity("gaia_layer", match.group(0).strip()))

        # Emotions
        for emotion in _EMOTION_KEYWORDS:
            if emotion in text_lower:
                entities.append(GAIAEntity("emotion", emotion))

        return entities

    # ------------------------------------------------------------------
    # Trauma detection
    # ------------------------------------------------------------------

    def _detect_trauma(self, text_lower: str) -> bool:
        return any(signal in text_lower for signal in _TRAUMA_SIGNALS)

    # ------------------------------------------------------------------
    # Query expansion
    # ------------------------------------------------------------------

    def _expand_query(self, raw: str, intent: QueryIntent, entities: list[GAIAEntity]) -> list[str]:
        sub_queries = [raw]  # always include the original

        crystal_entities = [e for e in entities if e.entity_type == "crystal"]
        stage_entities = [e for e in entities if e.entity_type == "alchemical_stage"]
        layer_entities = [e for e in entities if e.entity_type == "gaia_layer"]

        if crystal_entities:
            crystal = crystal_entities[0].value
            sub_queries.append(f"{crystal} mineral properties scientific")
            sub_queries.append(f"{crystal} GAIA layer correspondence")

        if stage_entities:
            stage = stage_entities[0].value
            sub_queries.append(f"{stage} alchemical stage meaning practices")

        if layer_entities:
            layer = layer_entities[0].value
            sub_queries.append(f"GAIA {layer} crystals elements resonance")

        if intent == QueryIntent.RESEARCH:
            sub_queries.append(f"{raw} peer reviewed scientific evidence")

        if intent == QueryIntent.THERAPEUTIC:
            sub_queries.append(f"{raw} trauma-informed support practices")

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for q in sub_queries:
            if q not in seen:
                seen.add(q)
                unique.append(q)

        return unique[:5]  # cap at 5 sub-queries
