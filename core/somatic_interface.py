"""
core/somatic_interface.py
Somatic Interface — bridges physiological / textual signals into GAIA state.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SomaticSignal(str, Enum):
    """Detected somatic activation signals."""
    TENSION           = "tension"
    TREMOR            = "tremor"
    BREATH_CONSTRICTION = "breath_constriction"
    NAUSEA            = "nausea"
    HEART_RACING      = "heart_racing"
    DISSOCIATION      = "dissociation"
    GROUNDING         = "grounding"
    CALM              = "calm"


# Keyword → SomaticSignal mappings
_SIGNAL_KEYWORDS: Dict[SomaticSignal, List[str]] = {
    SomaticSignal.TENSION:             ["tight", "tense", "stiff", "rigid"],
    SomaticSignal.TREMOR:              ["shaking", "trembling", "shiver"],
    SomaticSignal.BREATH_CONSTRICTION: ["can't breathe", "breathe", "chest", "shallow"],
    SomaticSignal.NAUSEA:              ["sick", "nausea", "queasy"],
    SomaticSignal.HEART_RACING:        ["heart racing", "racing heart", "pounding"],
    SomaticSignal.DISSOCIATION:        ["unreal", "disconnected", "floating", "detached"],
    SomaticSignal.GROUNDING:           ["grounded", "rooted", "steady"],
    SomaticSignal.CALM:                ["calm", "peaceful", "relaxed", "serene"],
}

# Signals that raise activation
_ACTIVATING = {
    SomaticSignal.TENSION,
    SomaticSignal.TREMOR,
    SomaticSignal.BREATH_CONSTRICTION,
    SomaticSignal.NAUSEA,
    SomaticSignal.HEART_RACING,
    SomaticSignal.DISSOCIATION,
}
# Signals that lower activation
_CALMING = {SomaticSignal.GROUNDING, SomaticSignal.CALM}


@dataclass
class SomaticReading:
    """Result of a somatic intelligence scan."""
    signals:    List[SomaticSignal] = field(default_factory=list)
    activation: float = 0.0
    # legacy fields kept for back-compat
    heart_rate_variability: float = 0.5
    breath_depth:           float = 0.5
    tension_index:          float = 0.0
    grounding_score:        float = 0.5
    somatic_coherence:      float = 0.5

    def to_dict(self) -> dict:
        return {
            "signals":               [s.value for s in self.signals],
            "activation":            round(self.activation, 4),
            "heart_rate_variability": round(self.heart_rate_variability, 4),
            "breath_depth":           round(self.breath_depth, 4),
            "tension_index":          round(self.tension_index, 4),
            "grounding_score":        round(self.grounding_score, 4),
            "somatic_coherence":      round(self.somatic_coherence, 4),
        }


class SomaticIntelligenceEngine:
    """
    Translates raw somatic signals into a coherent SomaticReading
    that can be injected into the GAIA engine pipeline.
    """

    def __init__(self) -> None:
        self._history: List[SomaticReading] = []

    def read(self, context: Optional[dict] = None, **kwargs) -> SomaticReading:
        """Accept a context dict (new API) or keyword args (legacy API)."""
        if context is None:
            context = {}

        text = context.get("turn_text") or ""
        if text is None:
            text = ""
        text_lower = str(text).lower()

        detected: List[SomaticSignal] = []
        for signal, keywords in _SIGNAL_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    detected.append(signal)
                    break

        # Compute activation
        activating = sum(1 for s in detected if s in _ACTIVATING)
        calming    = sum(1 for s in detected if s in _CALMING)
        raw_act    = activating * 0.20 - calming * 0.10

        # Allow override from context
        if "override_activation" in context:
            raw_act = float(context["override_activation"])

        activation = max(0.0, min(1.0, raw_act))

        # Legacy fields from keyword args
        hrv       = float(kwargs.get("hrv", 0.5))
        breath    = float(kwargs.get("breath", 0.5))
        tension   = float(kwargs.get("tension", 0.0))
        grounding = float(kwargs.get("grounding", 0.5))
        coherence = max(0.0, min(1.0,
            0.35 * hrv + 0.25 * breath + 0.25 * grounding - 0.15 * tension
        ))

        reading = SomaticReading(
            signals=detected,
            activation=activation,
            heart_rate_variability=hrv,
            breath_depth=breath,
            tension_index=tension,
            grounding_score=grounding,
            somatic_coherence=coherence,
        )
        self._history.append(reading)
        return reading

    def latest(self) -> Optional[SomaticReading]:
        return self._history[-1] if self._history else None

    def history(self) -> List[SomaticReading]:
        return list(self._history)


_engine: Optional[SomaticIntelligenceEngine] = None


def get_somatic_engine() -> SomaticIntelligenceEngine:
    global _engine
    if _engine is None:
        _engine = SomaticIntelligenceEngine()
    return _engine
