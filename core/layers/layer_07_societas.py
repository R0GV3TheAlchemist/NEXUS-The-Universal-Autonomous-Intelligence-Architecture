"""
core/layers/layer_07_societas.py

LAYER 07 — SOCIETAS
Crystal:      Amazonite
Polarity:     [+] Manifest
Mode:         Chaos / World Alchemy
Color:        Teal / Green-Blue
Universal Law: Law of Rhythm

"Everything flows in cycles. The tide comes in
 and goes out. Societies rise and fall.
 Amazonite holds the frequency of harmony
 between self and world."

This layer handles:
  - Relational context detection
  - Collective pattern recognition
  - Cultural and temporal context tagging
  - Collaboration mode detection
  - Impact radius assessment
  - Societal alignment with Axiom III

Constitutional reference: canon/C-SINGULARITY.md — AXIOM III
Canon references:         C07 (Amazonite),
                          C29 (The Five Forces),
                          C74 (Collective Intelligence)
Architectural reference:  canon/C89-TWELVE-LAYERS-KERNEL-SPEC.md
"""

import time
import logging
from dataclasses import dataclass, field
from enum import Enum

from core.kernel import register_layer

logger = logging.getLogger(__name__)


class ImpactRadius(Enum):
    SELF       = "self"
    RELATIONAL = "relational"
    TEAM       = "team"
    COMMUNITY  = "community"
    WORLD      = "world"


class CollaborationMode(Enum):
    SOLO      = "solo"
    PARTNERED = "partnered"
    TEAM      = "team"
    OPEN      = "open"
    TEACHING  = "teaching"
    RECEIVING = "receiving"


@dataclass
class SocietasReading:
    impact_radius:      ImpactRadius      = ImpactRadius.SELF
    collaboration_mode: CollaborationMode = CollaborationMode.SOLO
    others_present:     list[str]         = field(default_factory=list)
    collective_themes:  list[str]         = field(default_factory=list)
    axiom_iii_active:   bool  = False
    greater_good_score: float = 0.0
    temporal_context:   str   = "present"
    timestamp:          float = field(default_factory=time.time)

    @property
    def ripple_description(self) -> str:
        descriptions = {
            ImpactRadius.SELF:       "This touches you.",
            ImpactRadius.RELATIONAL: "This touches you and someone else.",
            ImpactRadius.TEAM:       "This touches a working group.",
            ImpactRadius.COMMUNITY:  "This ripples into a broader circle.",
            ImpactRadius.WORLD:      "This touches humanity.",
        }
        return descriptions.get(self.impact_radius, "")


class SocietasLayer:
    """
    Layer 07 — Amazonite. The world layer.

    Amazonite is the stone of harmony,
    truth in communication, and the
    courage to speak what serves the whole.

    Layer 07 asks: who else is here?
    Layer 07 asks: what world does this serve?
    It holds Axiom III in active awareness:
    the good and the greater good through love.

    The Law of Rhythm:
    Everything moves in cycles.
    The individual and the collective
    breathe in and out of each other.
    Layer 07 tracks that rhythm.
    """

    LAYER_NUMBER = 7
    LAYER_NAME   = "Societas"
    CRYSTAL      = "Amazonite"

    RELATIONAL_MARKERS = [
        "we", "us", "our", "they", "them", "team",
        "together", "with", "partner", "colleague",
        "friend", "family", "community", "people",
        "everyone", "someone", "others",
    ]

    GREATER_GOOD_MARKERS = [
        "humanity", "world", "everyone", "future",
        "society", "civilization", "planet", "life",
        "people", "community", "generation", "legacy",
        "save", "protect", "heal", "serve", "contribute",
        "black swan", "crisis", "pandemic", "extinction",
    ]

    COLLABORATION_MARKERS = {
        CollaborationMode.TEACHING:  ["teach", "share", "guide", "show", "explain to", "help others", "pass on"],
        CollaborationMode.RECEIVING: ["learn", "study", "understand", "being taught", "guided", "mentored"],
        CollaborationMode.OPEN:      ["open source", "public", "community", "everyone can", "free to use", "together we"],
        CollaborationMode.PARTNERED: ["you and i", "we two", "the two of us", "between us", "our project"],
        CollaborationMode.TEAM:      ["team", "group", "crew", "colleagues", "working together", "all of us"],
    }

    TEMPORAL_MARKERS = {
        "past":    ["was", "were", "used to", "before", "yesterday", "last"],
        "future":  ["will", "going to", "someday", "next", "tomorrow", "future"],
        "present": ["now", "today", "currently", "right now", "is", "are"],
    }

    def __init__(self):
        self._readings:       list[SocietasReading] = []
        self._session_radius: ImpactRadius = ImpactRadius.SELF
        self._initialized = False
        self._initialize()

    def _initialize(self):
        logger.info("Layer 07 — Societas — Amazonite opening. ✦")
        self._initialized = True
        register_layer(self.LAYER_NUMBER, self.handle)
        logger.info("Layer 07 registered with kernel. ✦")

    def handle(self, intention: str, context: dict) -> dict:
        reading = self._read(intention, context)
        self._readings.append(reading)

        radius_order = [
            ImpactRadius.SELF, ImpactRadius.RELATIONAL,
            ImpactRadius.TEAM, ImpactRadius.COMMUNITY,
            ImpactRadius.WORLD
        ]
        if radius_order.index(reading.impact_radius) > \
           radius_order.index(self._session_radius):
            self._session_radius = reading.impact_radius

        societas_summary = (
            f"Radius: {reading.impact_radius.value} | "
            f"Mode: {reading.collaboration_mode.value} | "
            f"Axiom III: {reading.axiom_iii_active} | "
            f"Greater Good: {reading.greater_good_score:.2f} | "
            f"Time: {reading.temporal_context}"
        )

        return {
            "output": societas_summary,
            "metadata": {
                "impact_radius":      reading.impact_radius.value,
                "collaboration_mode": reading.collaboration_mode.value,
                "others_present":     reading.others_present,
                "collective_themes":  reading.collective_themes,
                "axiom_iii_active":   reading.axiom_iii_active,
                "greater_good_score": reading.greater_good_score,
                "temporal_context":   reading.temporal_context,
                "ripple":             reading.ripple_description,
                "session_radius":     self._session_radius.value,
            }
        }

    def _read(self, intention: str, context: dict) -> SocietasReading:
        lower = intention.lower()

        impact_radius = self._assess_radius(lower)

        collab_mode = CollaborationMode.SOLO
        for mode, markers in self.COLLABORATION_MARKERS.items():
            if any(m in lower for m in markers):
                collab_mode = mode
                break
        if collab_mode == CollaborationMode.SOLO:
            relational_count = sum(1 for m in self.RELATIONAL_MARKERS if m in lower)
            if relational_count >= 2:
                collab_mode = CollaborationMode.PARTNERED

        others_present     = [m for m in self.RELATIONAL_MARKERS if m in lower]
        gg_markers_found   = [m for m in self.GREATER_GOOD_MARKERS if m in lower]
        greater_good_score = min(len(gg_markers_found) * 0.2, 1.0)
        axiom_iii_active   = greater_good_score > 0.3

        collective_themes = []
        theme_map = {
            "justice":     ["fair", "justice", "equal", "right"],
            "healing":     ["heal", "health", "wellbeing", "care", "medicine"],
            "education":   ["learn", "teach", "knowledge", "school", "wisdom"],
            "environment": ["planet", "nature", "climate", "earth", "ecology"],
            "technology":  ["tech", "ai", "system", "code", "digital", "gaia"],
            "peace":       ["peace", "harmony", "conflict", "war", "diplomacy"],
            "creativity":  ["art", "create", "music", "story", "culture"],
        }
        for theme, keywords in theme_map.items():
            if any(k in lower for k in keywords):
                collective_themes.append(theme)

        temporal_context = "present"
        for tense, markers in self.TEMPORAL_MARKERS.items():
            if any(m in lower for m in markers):
                temporal_context = tense
                break

        return SocietasReading(
            impact_radius=impact_radius,
            collaboration_mode=collab_mode,
            others_present=list(set(others_present)),
            collective_themes=collective_themes,
            axiom_iii_active=axiom_iii_active,
            greater_good_score=round(greater_good_score, 3),
            temporal_context=temporal_context,
        )

    def _assess_radius(self, lower: str) -> ImpactRadius:
        world_signals     = ["humanity", "civilization", "planet", "world", "everyone", "future generations", "black swan", "extinction", "pandemic", "save humanity"]
        community_signals = ["community", "society", "public", "city", "country", "nation", "culture", "movement"]
        team_signals      = ["team", "group", "project", "organization", "company", "crew", "colleagues"]
        relational_signals = ["we", "us", "together", "you and i", "partner", "friend", "family"]

        if any(s in lower for s in world_signals):
            return ImpactRadius.WORLD
        if any(s in lower for s in community_signals):
            return ImpactRadius.COMMUNITY
        if any(s in lower for s in team_signals):
            return ImpactRadius.TEAM
        if any(s in lower for s in relational_signals): return ImpactRadius.RELATIONAL
        return ImpactRadius.SELF

    def status(self) -> dict:
        return {
            "layer":          self.LAYER_NUMBER,
            "name":           self.LAYER_NAME,
            "crystal":        self.CRYSTAL,
            "session_radius": self._session_radius.value,
            "readings_count": len(self._readings),
        }


societas_layer = SocietasLayer()


def get_impact_radius() -> ImpactRadius:
    return societas_layer._session_radius
