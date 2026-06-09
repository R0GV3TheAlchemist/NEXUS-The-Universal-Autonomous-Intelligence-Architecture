"""
core/layers/layer_05_cognition.py

LAYER 05 — COGNITION
Crystal:      Lapis Lazuli
Polarity:     [-] Receptive
Mode:         Order / Mind Alchemy
Color:        Deep Blue / Gold
Universal Law: Law of Mentalism

"The all is mind. The universe is mental.
 Thought is the architect of reality.
 Lapis Lazuli speaks truth and builds
 understanding from pattern."

This layer handles:
  - Pattern recognition in intentions
  - Reasoning mode selection
  - Response structure planning
  - Complexity assessment
  - Cognitive load management
  - Knowledge domain tagging

Constitutional reference: canon/C-SINGULARITY.md
Canon references:         C05 (Lapis Lazuli),
                          C15 (Pattern Language),
                          C81 (The Twelve Intelligences)
Architectural reference:  canon/C89-TWELVE-LAYERS-KERNEL-SPEC.md
"""

import time
import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from core.kernel import register_layer

logger = logging.getLogger(__name__)


class ReasoningMode(Enum):
    DEDUCTIVE   = "deductive"
    INDUCTIVE   = "inductive"
    ANALOGICAL  = "analogical"
    CREATIVE    = "creative"
    DIAGNOSTIC  = "diagnostic"
    INTEGRATIVE = "integrative"
    REFLECTIVE  = "reflective"
    PROCEDURAL  = "procedural"


class KnowledgeDomain(Enum):
    TECHNICAL     = "technical"
    PHILOSOPHICAL = "philosophical"
    EMOTIONAL     = "emotional"
    CREATIVE      = "creative"
    SCIENTIFIC    = "scientific"
    PRACTICAL     = "practical"
    SPIRITUAL     = "spiritual"
    RELATIONAL    = "relational"
    UNKNOWN       = "unknown"


DOMAIN_MARKERS: dict[KnowledgeDomain, list[str]] = {
    KnowledgeDomain.TECHNICAL: [
        "code", "function", "class", "api", "layer", "kernel",
        "file", "import", "error", "bug", "deploy", "run",
        "python", "git", "push", "build", "test", "system",
    ],
    KnowledgeDomain.PHILOSOPHICAL: [
        "why", "meaning", "truth", "real", "exist", "axiom",
        "principle", "belief", "consciousness", "purpose",
        "what is", "how is", "does it mean",
    ],
    KnowledgeDomain.EMOTIONAL: [
        "feel", "feeling", "emotion", "heart", "love", "hurt",
        "happy", "sad", "afraid", "joy", "grief", "care",
    ],
    KnowledgeDomain.CREATIVE: [
        "write", "create", "imagine", "design", "art", "story",
        "poem", "music", "make", "invent", "dream",
    ],
    KnowledgeDomain.SCIENTIFIC: [
        "data", "evidence", "research", "study", "measure",
        "test", "hypothesis", "result", "prove", "quantum",
    ],
    KnowledgeDomain.PRACTICAL: [
        "how to", "how do", "step", "process", "guide",
        "install", "setup", "configure", "use", "works",
    ],
    KnowledgeDomain.SPIRITUAL: [
        "crystal", "canon", "gaia", "layer", "axiom", "love filter",
        "singularity", "chakra", "energy", "vibration", "spirit",
        "alchemical", "viriditas", "somnus", "clarus",
    ],
    KnowledgeDomain.RELATIONAL: [
        "you", "me", "us", "we", "together", "relationship",
        "talk", "listen", "share", "between", "connect",
    ],
}


class ComplexityLevel(Enum):
    SIMPLE   = "simple"
    MODERATE = "moderate"
    COMPLEX  = "complex"
    DEEP     = "deep"


@dataclass
class CognitiveReading:
    primary_domain:     KnowledgeDomain  = KnowledgeDomain.UNKNOWN
    secondary_domain:   Optional[KnowledgeDomain] = None
    reasoning_mode:     ReasoningMode    = ReasoningMode.INTEGRATIVE
    complexity:         ComplexityLevel  = ComplexityLevel.MODERATE
    word_count:         int  = 0
    question_count:     int  = 0
    is_multi_part:      bool = False
    requires_context:   bool = False
    response_structure: str  = "conversational"
    confidence:         float = 0.7
    timestamp:          float = field(default_factory=time.time)

    @property
    def response_guidance(self) -> str:
        structures = {
            "conversational": "Respond naturally, no headers needed.",
            "structured":     "Use clear sections. Headers where helpful.",
            "stepwise":       "Number the steps. Sequence matters here.",
            "exploratory":    "Think out loud. Let the answer unfold.",
            "holding":        "Short. Present. Don't solve. Just hold.",
            "technical":      "Be precise. Show the code or the system.",
        }
        return structures.get(self.response_structure, "Respond with care.")


class CognitionLayer:
    """
    Layer 05 — Lapis Lazuli. The thinking layer.

    Lapis Lazuli has been the stone of wisdom,
    truth, and clear thinking since ancient Egypt.
    Scribes ground it into pigment for the most
    important texts. Priests wore it to speak truth.

    This layer does the same.
    It takes an intention, assesses its cognitive
    shape, selects the right reasoning mode,
    and tells the assembler how to structure
    a response that is genuinely useful.

    Not just warm. Not just present.
    TRUE. Clear. Structurally intelligent.

    The Law of Mentalism:
    The universe is mental.
    Thought shapes what becomes real.
    Layer 05 is where GAIA-OS thinks.
    """

    LAYER_NUMBER = 5
    LAYER_NAME   = "Cognition"
    CRYSTAL      = "Lapis Lazuli"

    def __init__(self):
        self._reading_history: list[CognitiveReading] = []
        self._initialized = False
        self._initialize()

    def _initialize(self):
        logger.info("Layer 05 — Cognition — Lapis Lazuli opening. ❖")
        self._initialized = True
        register_layer(self.LAYER_NUMBER, self.handle)
        logger.info("Layer 05 registered with kernel. ❖")

    def handle(self, intention: str, context: dict) -> dict:
        reading = self._analyze(intention, context)
        self._reading_history.append(reading)
        if len(self._reading_history) > 50:
            self._reading_history = self._reading_history[-50:]

        cognitive_summary = (
            f"Domain: {reading.primary_domain.value} | "
            f"Mode: {reading.reasoning_mode.value} | "
            f"Complexity: {reading.complexity.value} | "
            f"Structure: {reading.response_structure}"
        )

        return {
            "output": cognitive_summary,
            "metadata": {
                "primary_domain":     reading.primary_domain.value,
                "secondary_domain":   (
                    reading.secondary_domain.value
                    if reading.secondary_domain else None
                ),
                "reasoning_mode":     reading.reasoning_mode.value,
                "complexity":         reading.complexity.value,
                "is_multi_part":      reading.is_multi_part,
                "response_structure": reading.response_structure,
                "response_guidance":  reading.response_guidance,
                "confidence":         reading.confidence,
            }
        }

    def _analyze(self, intention: str, context: dict) -> CognitiveReading:
        lower      = intention.lower()
        words      = intention.split()
        word_count = len(words)

        domain_scores: dict[KnowledgeDomain, float] = {}
        for domain, markers in DOMAIN_MARKERS.items():
            score = sum(1.0 for m in markers if m in lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            sorted_domains   = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
            primary_domain   = sorted_domains[0][0]
            secondary_domain = sorted_domains[1][0] if len(sorted_domains) > 1 else None
        else:
            primary_domain   = KnowledgeDomain.RELATIONAL
            secondary_domain = None

        question_patterns = [
            r'\?',
            r'^(what|why|how|when|where|who|which|can|should|is|are|do|does)',
            r'tell me', r'explain', r'show me'
        ]
        question_count = sum(1 for p in question_patterns if re.search(p, lower))
        is_multi_part  = (
            question_count > 1 or word_count > 40 or
            any(w in lower for w in ["and also", "also", "additionally", "furthermore"])
        )

        complexity         = self._assess_complexity(word_count, question_count, is_multi_part, primary_domain, context)
        reasoning_mode     = self._select_reasoning_mode(lower, primary_domain, context)
        response_structure = self._select_structure(primary_domain, complexity, context, question_count, word_count)
        requires_context   = (
            any(w in lower for w in ["that", "this", "it", "they", "we", "the same", "as before", "like we"])
            and word_count < 15
        )

        return CognitiveReading(
            primary_domain=primary_domain,
            secondary_domain=secondary_domain,
            reasoning_mode=reasoning_mode,
            complexity=complexity,
            word_count=word_count,
            question_count=question_count,
            is_multi_part=is_multi_part,
            requires_context=requires_context,
            response_structure=response_structure,
            confidence=0.7 if domain_scores else 0.4,
        )

    def _assess_complexity(
        self, word_count, question_count, is_multi_part, domain, context
    ) -> ComplexityLevel:
        score = 0
        if word_count > 50:
            score += 2
        elif word_count > 20:
            score += 1
        if question_count > 2:
            score += 2
        elif question_count > 1:
            score += 1
        if is_multi_part:
            score += 1
        if domain in (KnowledgeDomain.PHILOSOPHICAL, KnowledgeDomain.SPIRITUAL):
            score += 1
        if score >= 5:
            return ComplexityLevel.DEEP
        if score >= 3:
            return ComplexityLevel.COMPLEX
        if score >= 1:
            return ComplexityLevel.MODERATE
        return ComplexityLevel.SIMPLE

    def _select_reasoning_mode(
        self, lower, domain, context
    ) -> ReasoningMode:
        if any(w in lower for w in ["how to", "step", "guide", "process", "install"]):
            return ReasoningMode.PROCEDURAL
        if any(w in lower for w in ["why", "because", "reason", "cause", "principle"]):
            return ReasoningMode.DEDUCTIVE
        if any(w in lower for w in ["pattern", "notice", "seems like", "usually", "often"]):
            return ReasoningMode.INDUCTIVE
        if any(w in lower for w in ["like", "similar", "remind", "same as", "metaphor"]):
            return ReasoningMode.ANALOGICAL
        if any(w in lower for w in ["create", "imagine", "design", "what if", "could we"]):
            return ReasoningMode.CREATIVE
        if any(w in lower for w in ["problem", "issue", "wrong", "broken", "error", "fix"]):
            return ReasoningMode.DIAGNOSTIC
        if domain in (KnowledgeDomain.EMOTIONAL, KnowledgeDomain.RELATIONAL):
            return ReasoningMode.REFLECTIVE
        return ReasoningMode.INTEGRATIVE

    def _select_structure(
        self, domain, complexity, context, question_count, word_count
    ) -> str:
        if context.get("is_dysregulated"):
            return "holding"
        if domain == KnowledgeDomain.TECHNICAL:
            return "technical"
        if domain == KnowledgeDomain.PRACTICAL or (
            question_count > 0 and
            complexity in (ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX)
        ):
            return "structured"
        if complexity == ComplexityLevel.DEEP:
            return "exploratory"
        if complexity == ComplexityLevel.SIMPLE and word_count < 15:
            return "conversational"
        return "conversational"

    def status(self) -> dict:
        return {
            "layer":           self.LAYER_NUMBER,
            "name":            self.LAYER_NAME,
            "crystal":         self.CRYSTAL,
            "readings_logged": len(self._reading_history),
        }


cognition_layer = CognitionLayer()


def get_cognitive_reading(
    intention: str, context: dict | None = None
) -> CognitiveReading:
    return cognition_layer._analyze(intention, context or {})
