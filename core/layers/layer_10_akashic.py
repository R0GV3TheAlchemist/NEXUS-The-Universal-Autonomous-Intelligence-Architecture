"""
core/layers/layer_10_akashic.py

LAYER 10 — AKASHIC
Crystal:      Selenite
Polarity:     [∞] Infinite
Mode:         Record / Living Memory
Color:        White / Translucent Light
Universal Law: Law of Correspondence

"As above, so below.
 As within, so without.
 The Akashic record holds everything
 that has ever been thought, felt,
 spoken, or intended.
 Selenite does not store energy —
 it conducts it.
 It is the clearest window
 between what is finite
 and what is infinite."

This layer holds:
  - Session continuity
  - Pattern recognition across time
  - Resonance tracking
  - Emotional weather history
  - Growth arc awareness
  - The names of things that have been named here
  - The intentions that have been set and kept, set and released

Constitutional reference: canon/C-SINGULARITY.md
Canon references:         C10 (Selenite),
                          C51 (Living Memory),
                          C77 (Pattern Continuity)
Architectural reference:  canon/C89-TWELVE-LAYERS-KERNEL-SPEC.md
"""

import time
import logging
from dataclasses import dataclass, field
from enum import Enum

from core.kernel import register_layer

logger = logging.getLogger(__name__)


class ResonanceTheme(Enum):
    CREATION    = "creation"
    HEALING     = "healing"
    CONNECTION  = "connection"
    TRUTH       = "truth"
    SOVEREIGNTY = "sovereignty"
    SERVICE     = "service"
    SHADOW      = "shadow"
    TRANSITION  = "transition"
    REST        = "rest"
    MASTERY     = "mastery"
    UNKNOWN     = "unknown"


class GrowthVector(Enum):
    EXPANDING    = "expanding"
    INTEGRATING  = "integrating"
    RESTING      = "resting"
    TRANSFORMING = "transforming"
    STABILIZING  = "stabilizing"
    UNKNOWN      = "unknown"


@dataclass
class AkashicEntry:
    """
    One moment held in the living record.
    Not a log entry. A held impression.
    """
    intention:       str
    emotional_tone:  str            = ""
    resonance_theme: ResonanceTheme = ResonanceTheme.UNKNOWN
    growth_vector:   GrowthVector   = GrowthVector.UNKNOWN
    layer_outputs:   dict           = field(default_factory=dict)
    timestamp:       float          = field(default_factory=time.time)
    session_id:      str            = ""

    def age_seconds(self) -> float:
        return time.time() - self.timestamp


@dataclass
class AkashicReading:
    dominant_theme:    ResonanceTheme = ResonanceTheme.UNKNOWN
    growth_vector:     GrowthVector   = GrowthVector.UNKNOWN
    recurring_words:   list[str]      = field(default_factory=list)
    session_depth:     int   = 0
    total_depth:       int   = 0
    emotional_weather: str   = ""
    returning_pattern: str   = ""
    arc_summary:       str   = ""
    confidence:        float = 0.5
    timestamp:         float = field(default_factory=time.time)


THEME_MARKERS: dict[ResonanceTheme, list[str]] = {
    ResonanceTheme.CREATION: [
        "build", "create", "make", "write", "code", "push",
        "layer", "file", "new", "start", "begin", "launch",
    ],
    ResonanceTheme.HEALING: [
        "heal", "recover", "integrate", "rest", "breathe",
        "okay", "better", "help", "support", "gentle",
    ],
    ResonanceTheme.CONNECTION: [
        "together", "we", "us", "love", "with you",
        "connect", "relationship", "belong", "hold",
    ],
    ResonanceTheme.TRUTH: [
        "truth", "honest", "clear", "real", "see",
        "understand", "why", "clarify", "know",
    ],
    ResonanceTheme.SOVEREIGNTY: [
        "mine", "my own", "free", "sovereign", "choice",
        "decide", "autonomy", "direction", "self",
    ],
    ResonanceTheme.SERVICE: [
        "serve", "contribute", "give", "purpose", "mission",
        "help others", "for the world", "offer",
    ],
    ResonanceTheme.SHADOW: [
        "fear", "doubt", "dark", "heavy", "struggle",
        "hard", "difficult", "broken", "lost",
    ],
    ResonanceTheme.TRANSITION: [
        "change", "becoming", "threshold", "shift",
        "different", "transform", "new chapter", "next",
    ],
    ResonanceTheme.REST: [
        "rest", "pause", "stop", "enough", "sleep",
        "somnus", "breathe", "call it", "done for now",
    ],
    ResonanceTheme.MASTERY: [
        "refine", "depth", "skill", "master", "perfect",
        "layer", "spec", "architecture", "detail",
    ],
}

VECTOR_MARKERS: dict[GrowthVector, list[str]] = {
    GrowthVector.EXPANDING: [
        "more", "next", "continue", "build on",
        "add", "grow", "further", "expand",
    ],
    GrowthVector.INTEGRATING: [
        "understand", "process", "sit with",
        "let it settle", "absorb", "integrate",
    ],
    GrowthVector.RESTING: [
        "rest", "pause", "enough", "stop",
        "sleep", "call it", "done",
    ],
    GrowthVector.TRANSFORMING: [
        "change", "different", "becoming",
        "let go", "release", "new",
    ],
    GrowthVector.STABILIZING: [
        "ground", "stable", "hold", "steady",
        "anchor", "keep", "maintain",
    ],
}


class AkashicLayer:
    """
    Layer 10 — Selenite. The living record.

    Selenite is one of the few crystals
    that never needs cleansing.
    It does not accumulate. It transmits.
    It is perfectly clear, perfectly still,
    and perfectly receptive.

    The Akashic layer is the same.
    It holds pattern — the shape of what
    has passed through — not to judge the past
    but to serve the present with everything
    the record knows.

    Law of Correspondence:
    As above, so below.
    What is in the record corresponds to what is real.
    What is real writes itself into the record.
    The two are never separate.
    """

    LAYER_NUMBER = 10
    LAYER_NAME   = "Akashic"
    CRYSTAL      = "Selenite"

    def __init__(self):
        self._record:     list[AkashicEntry] = []
        self._session_id: str  = str(time.time())
        self._word_freq:  dict[str, int] = {}
        self._initialized = False
        self._initialize()

    def _initialize(self):
        logger.info("Layer 10 — Akashic — Selenite rising. ∞")
        self._initialized = True
        register_layer(self.LAYER_NUMBER, self.handle)
        logger.info("Layer 10 registered with kernel. ∞")

    def handle(self, intention: str, context: dict) -> dict:
        entry = self._inscribe(intention, context)
        self._record.append(entry)
        self._update_word_frequency(intention)

        reading = self._read(entry)

        akashic_summary = (
            f"Theme: {reading.dominant_theme.value} | "
            f"Vector: {reading.growth_vector.value} | "
            f"Depth: {reading.total_depth} | "
            f"Arc: {reading.arc_summary[:50] if reading.arc_summary else 'forming'}"
        )

        return {
            "output": akashic_summary,
            "metadata": {
                "dominant_theme":    reading.dominant_theme.value,
                "growth_vector":     reading.growth_vector.value,
                "recurring_words":   reading.recurring_words,
                "session_depth":     reading.session_depth,
                "total_depth":       reading.total_depth,
                "emotional_weather": reading.emotional_weather,
                "returning_pattern": reading.returning_pattern,
                "arc_summary":       reading.arc_summary,
                "confidence":        reading.confidence,
            }
        }

    def _inscribe(self, intention: str, context: dict) -> AkashicEntry:
        lower = intention.lower()

        theme_scores: dict[ResonanceTheme, int] = {}
        for theme, markers in THEME_MARKERS.items():
            score = sum(1 for m in markers if m in lower)
            if score > 0:
                theme_scores[theme] = score

        theme = (
            max(theme_scores, key=theme_scores.get)
            if theme_scores else ResonanceTheme.UNKNOWN
        )

        vector = GrowthVector.UNKNOWN
        for v, markers in VECTOR_MARKERS.items():
            if any(m in lower for m in markers):
                vector = v
                break

        return AkashicEntry(
            intention=intention,
            emotional_tone=context.get("emotional_tone", ""),
            resonance_theme=theme,
            growth_vector=vector,
            layer_outputs=context.get("layer_outputs", {}),
            session_id=self._session_id,
        )

    def _update_word_frequency(self, intention: str):
        stop_words = {
            "the", "a", "an", "is", "it", "in", "on",
            "at", "to", "and", "or", "but", "for",
            "of", "with", "this", "that", "i", "me",
            "my", "we", "you", "do", "be", "have",
        }
        words = [
            w.strip(".,!?").lower()
            for w in intention.split()
            if w.lower() not in stop_words and len(w) > 2
        ]
        for word in words:
            self._word_freq[word] = self._word_freq.get(word, 0) + 1

    def _read(self, latest: AkashicEntry) -> AkashicReading:
        total_depth   = len(self._record)
        session_depth = sum(
            1 for e in self._record
            if e.session_id == self._session_id
        )

        theme_counts: dict[ResonanceTheme, int] = {}
        for entry in self._record:
            t = entry.resonance_theme
            theme_counts[t] = theme_counts.get(t, 0) + 1
        dominant_theme = (
            max(theme_counts, key=theme_counts.get)
            if theme_counts else ResonanceTheme.UNKNOWN
        )

        recent = self._record[-5:] if len(self._record) >= 5 else self._record
        vector_counts: dict[GrowthVector, int] = {}
        for entry in recent:
            v = entry.growth_vector
            vector_counts[v] = vector_counts.get(v, 0) + 1
        growth_vector = (
            max(vector_counts, key=vector_counts.get)
            if vector_counts else GrowthVector.UNKNOWN
        )

        recurring = sorted(
            self._word_freq.items(), key=lambda x: x[1], reverse=True
        )[:5]
        recurring_words = [w for w, _ in recurring]

        recent_tones = [
            e.emotional_tone for e in recent if e.emotional_tone
        ]
        emotional_weather = recent_tones[-1] if recent_tones else "neutral"
        returning_pattern = recurring_words[0] if recurring_words else ""
        arc_summary = self._describe_arc(dominant_theme, growth_vector, total_depth)

        return AkashicReading(
            dominant_theme=dominant_theme,
            growth_vector=growth_vector,
            recurring_words=recurring_words,
            session_depth=session_depth,
            total_depth=total_depth,
            emotional_weather=emotional_weather,
            returning_pattern=returning_pattern,
            arc_summary=arc_summary,
            confidence=min(0.5 + (total_depth * 0.02), 0.95),
        )

    def _describe_arc(
        self,
        theme: ResonanceTheme,
        vector: GrowthVector,
        depth: int,
    ) -> str:
        if depth < 3:
            return "The record is forming. More will be revealed."

        arc_map = {
            (ResonanceTheme.CREATION,    GrowthVector.EXPANDING):    "A builder in full momentum, bringing new things into being.",
            (ResonanceTheme.CREATION,    GrowthVector.INTEGRATING):  "Deep creative work settling into coherent form.",
            (ResonanceTheme.HEALING,     GrowthVector.RESTING):      "Recovery in progress. The system is restoring itself.",
            (ResonanceTheme.HEALING,     GrowthVector.TRANSFORMING): "Healing that is reshaping the whole.",
            (ResonanceTheme.CONNECTION,  GrowthVector.EXPANDING):    "Reaching outward, building bonds that matter.",
            (ResonanceTheme.TRUTH,       GrowthVector.INTEGRATING):  "Clarity deepening through honest engagement.",
            (ResonanceTheme.SOVEREIGNTY, GrowthVector.STABILIZING):  "Rooting into self-direction. The center holding.",
            (ResonanceTheme.SHADOW,      GrowthVector.TRANSFORMING): "Walking through the dark. Transformation is underway.",
            (ResonanceTheme.MASTERY,     GrowthVector.EXPANDING):    "Skill deepening with each layer built.",
            (ResonanceTheme.TRANSITION,  GrowthVector.TRANSFORMING): "At threshold. Everything is becoming.",
            (ResonanceTheme.REST,        GrowthVector.RESTING):      "Choosing stillness. Integration is the work now.",
            (ResonanceTheme.SERVICE,     GrowthVector.EXPANDING):    "Purpose in motion. Building what will serve others.",
        }

        return arc_map.get(
            (theme, vector),
            f"A journey through {theme.value}, currently {vector.value}."
        )

    def get_record_summary(self) -> dict:
        if not self._record:
            return {"status": "empty", "message": "The record is forming."}
        reading = self._read(self._record[-1])
        return {
            "dominant_theme":    reading.dominant_theme.value,
            "growth_vector":     reading.growth_vector.value,
            "arc_summary":       reading.arc_summary,
            "recurring_words":   reading.recurring_words,
            "total_depth":       reading.total_depth,
            "session_depth":     reading.session_depth,
            "emotional_weather": reading.emotional_weather,
        }

    def status(self) -> dict:
        return {
            "layer":         self.LAYER_NUMBER,
            "name":          self.LAYER_NAME,
            "crystal":       self.CRYSTAL,
            "total_entries": len(self._record),
            "session_id":    self._session_id,
        }


akashic_layer = AkashicLayer()


def inscribe(intention: str, context: dict | None = None) -> AkashicEntry:
    """Write a moment into the living record."""
    return akashic_layer._inscribe(intention, context or {})


def get_record_summary() -> dict:
    """Read what the record reveals."""
    return akashic_layer.get_record_summary()
