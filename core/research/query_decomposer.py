"""
GAIA Deep Research Runtime — Query Decomposer
Issue #454

Breaks a user query into independent sub-queries.
Extract intent, entities (crystals, layers, archetypes, frequencies),
and expand into 3-5 parallel search vectors.

FrequencyContext-aware: a user in NIGREDO asking about
"how to heal" gets sub-queries tuned toward grounding and
purification. A user in RUBEDO gets sub-queries tuned toward
integration and radiance.
"""

import re
from typing import List, Optional, Dict
from core.research.models import (
    SubQuery, QueryIntent, FrequencyContext
)


# Entity vocabularies drawn from Correspondence Architecture (#452)
CRYSTAL_VOCAB = [
    "black tourmaline", "amethyst", "labradorite", "rose quartz",
    "clear quartz", "obsidian", "malachite", "citrine", "selenite",
    "lapis lazuli", "moonstone", "fluorite", "pyrite", "emerald",
    "turquoise", "rhodonite", "carnelian", "aquamarine", "garnet",
    "tiger's eye", "sodalite", "howlite", "jade", "bloodstone"
]

GAIA_LAYER_VOCAB = [
    "layer 01", "layer 02", "layer 03", "layer 04", "layer 05",
    "layer 06", "layer 07", "layer 08", "layer 09", "layer 10",
    "layer 11", "physical", "energy", "mental", "emotional",
    "will", "shadow", "intuition", "transformation", "soul",
    "akashic", "gaianite"
]

ARCHETYPE_VOCAB = [
    "guardian", "healer", "seeker", "warrior", "sage", "magician",
    "lover", "creator", "ruler", "innocent", "orphan", "jester",
    "caregiver", "destroyer", "empress", "emperor", "hierophant"
]

ALCHEMICAL_VOCAB = [
    "nigredo", "albedo", "citrinitas", "rubedo",
    "calcinatio", "solutio", "coagulatio", "separatio", "viriditas"
]

FREQUENCY_VOCAB = {
    "174": "pain relief", "285": "tissue healing",
    "396": "liberation from fear", "417": "transformation",
    "432": "earth tuning", "528": "DNA repair and detox",
    "639": "relationships", "741": "intuition",
    "852": "spiritual order", "963": "divine connection"
}

# Intent signals
INTENT_SIGNALS: Dict[QueryIntent, List[str]] = {
    QueryIntent.FACTUAL: ["what is", "how does", "define", "explain", "science of", "evidence"],
    QueryIntent.REFLECTIVE: ["why do i", "what am i", "how can i", "my", "myself", "inner"],
    QueryIntent.SYMBOLIC: ["meaning of", "archetype", "symbol", "correspondence", "crystal", "frequency"],
    QueryIntent.RESEARCH: ["research", "compare", "analyse", "study", "investigate", "deep dive"],
    QueryIntent.THERAPEUTIC: ["heal", "detox", "release", "clear", "trauma", "recover", "soothe"],
    QueryIntent.CREATIVE: ["create", "imagine", "design", "vision", "manifest", "dream"],
}

# Alchemical stage → synthesis tone map
STAGE_TONE: Dict[str, str] = {
    "NIGREDO": "grounding",
    "ALBEDO": "clarifying",
    "CITRINITAS": "illuminating",
    "RUBEDO": "integrating",
    "CALCINATIO": "purifying",
    "SOLUTIO": "dissolving",
    "COAGULATIO": "crystallising",
    "SEPARATIO": "discerning",
    "VIRIDITAS": "enlivening",
}


class QueryDecomposer:
    """
    Decomposes a user query into parallel sub-queries.
    FrequencyContext shapes which dimensions of the topic are emphasised.
    """

    def decompose(
        self,
        query: str,
        frequency_context: Optional[FrequencyContext] = None,
        max_sub_queries: int = 5
    ) -> List[SubQuery]:
        """
        Decompose query into sub-queries.
        Returns list of SubQuery objects, ordered by priority.
        """
        intent = self._classify_intent(query)
        entities = self._extract_entities(query)
        sub_queries = self._generate_sub_queries(
            query, intent, entities, frequency_context, max_sub_queries
        )
        return sub_queries

    def get_synthesis_tone(
        self,
        frequency_context: Optional[FrequencyContext]
    ) -> str:
        """Determine the synthesis tone from frequency context."""
        if not frequency_context:
            return "balanced"
        if frequency_context.alchemical_stage:
            stage = frequency_context.alchemical_stage.upper()
            tone = STAGE_TONE.get(stage, "balanced")
            # Frequency-specific override
            if frequency_context.active_frequency_hz:
                hz = str(int(frequency_context.active_frequency_hz))
                freq_meaning = FREQUENCY_VOCAB.get(hz)
                if freq_meaning:
                    return f"{tone} ({freq_meaning})"
            return tone
        if frequency_context.dominant_emotion:
            return f"emotionally resonant ({frequency_context.dominant_emotion})"
        return "balanced"

    def _classify_intent(self, query: str) -> QueryIntent:
        q = query.lower()
        scores = {intent: 0 for intent in QueryIntent}
        for intent, signals in INTENT_SIGNALS.items():
            for signal in signals:
                if signal in q:
                    scores[intent] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else QueryIntent.RESEARCH

    def _extract_entities(self, query: str) -> List[str]:
        q = query.lower()
        found = []
        for vocab, label in [
            (CRYSTAL_VOCAB, "crystal"),
            (GAIA_LAYER_VOCAB, "layer"),
            (ARCHETYPE_VOCAB, "archetype"),
            (ALCHEMICAL_VOCAB, "stage"),
        ]:
            for term in vocab:
                if term in q:
                    found.append(f"{label}:{term}")
        # Frequency detection
        for hz in FREQUENCY_VOCAB:
            if hz in query:
                found.append(f"frequency:{hz}Hz")
        return found

    def _generate_sub_queries(
        self,
        query: str,
        intent: QueryIntent,
        entities: List[str],
        frequency_context: Optional[FrequencyContext],
        max_sub_queries: int
    ) -> List[SubQuery]:
        sub_queries = []

        # Primary sub-query: the original question
        sub_queries.append(SubQuery(
            text=query,
            intent=intent,
            entities=entities,
            priority=1
        ))

        # Entity-specific sub-queries
        for entity in entities[:2]:  # Top 2 entities
            kind, name = entity.split(":", 1)
            if kind == "crystal":
                sub_queries.append(SubQuery(
                    text=f"{name} piezoelectric properties scientific research",
                    intent=QueryIntent.FACTUAL,
                    entities=[entity],
                    priority=2
                ))
                sub_queries.append(SubQuery(
                    text=f"{name} correspondence GAIA layer archetype emotion",
                    intent=QueryIntent.SYMBOLIC,
                    entities=[entity],
                    priority=2
                ))
            elif kind == "frequency":
                hz = name.replace("Hz", "")
                sub_queries.append(SubQuery(
                    text=f"{hz} Hz frequency human biology piezoelectric cellular resonance",
                    intent=QueryIntent.FACTUAL,
                    entities=[entity],
                    priority=2
                ))

        # Alchemical context sub-query
        if frequency_context and frequency_context.alchemical_stage:
            stage = frequency_context.alchemical_stage
            sub_queries.append(SubQuery(
                text=f"{query} {stage} alchemical stage integration",
                intent=QueryIntent.SYMBOLIC,
                entities=[f"stage:{stage}"],
                priority=3
            ))

        # Falsifiability sub-query
        sub_queries.append(SubQuery(
            text=f"{query} evidence scientific basis peer reviewed",
            intent=QueryIntent.FACTUAL,
            entities=[],
            priority=4
        ))

        return sub_queries[:max_sub_queries]
