"""
core/shadow_integration.py
Shadow Integration — soul-mirror shadow work integration layer.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class IntegrationDepth(str, Enum):
    SURFACE     = "surface"
    PARTIAL     = "partial"
    INTEGRATED  = "integrated"
    TRANSCENDED = "transcended"


class ShadowPattern(str, Enum):
    """Archetypal shadow patterns detectable in language."""
    PROJECTION         = "projection"
    DENIAL             = "denial"
    SCAPEGOATING       = "scapegoating"
    DEFLECTION         = "deflection"
    IDEALISATION       = "idealisation"
    SUPPRESSION        = "suppression"
    SPLITTING          = "splitting"
    REACTION_FORMATION = "reaction_formation"


# Simple keyword rules for each pattern
_PATTERN_SIGNALS: Dict[ShadowPattern, List[str]] = {
    ShadowPattern.PROJECTION:         ["everyone", "they always", "people are", "nobody"],
    ShadowPattern.DENIAL:             ["never angry", "never sad", "i don't feel", "i never"],
    ShadowPattern.SCAPEGOATING:       ["it's their fault", "blame", "caused by them"],
    ShadowPattern.DEFLECTION:         ["but what about", "let's change", "off topic"],
    ShadowPattern.IDEALISATION:       ["perfect", "flawless", "can do no wrong"],
    ShadowPattern.SUPPRESSION:        ["ignore it", "push through", "doesn't matter"],
    ShadowPattern.SPLITTING:          ["always", "never", "completely", "totally"],
    ShadowPattern.REACTION_FORMATION: ["hate", "despise", "can't stand"],
}


@dataclass
class ShadowReading:
    """Output of a single shadow integration assessment."""
    depth:             IntegrationDepth = IntegrationDepth.SURFACE
    activation_score:  float = 0.0
    integration_score: float = 0.0
    integration_pct:   float = 0.0
    archetype:         Optional[str] = None
    directive:         str = ""
    patterns:          List[ShadowPattern] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "depth":             self.depth.value,
            "activation_score":  round(self.activation_score, 4),
            "integration_score": round(self.integration_score, 4),
            "integration_pct":   round(self.integration_pct, 4),
            "archetype":         self.archetype,
            "directive":         self.directive,
            "patterns":          [p.value for p in self.patterns],
        }

    def summary(self) -> dict:
        return self.to_dict()


@dataclass
class ShadowIntegrationRecord:
    """
    A structured record of a single shadow integration event.
    Used by SoulLayer to track per-archetype shadow work.
    """
    archetype:         str
    intensity:         float
    depth:             IntegrationDepth = IntegrationDepth.SURFACE
    patterns:          List[ShadowPattern] = field(default_factory=list)
    directive:         str = ""
    integration_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "archetype":         self.archetype,
            "intensity":         round(self.intensity, 4),
            "depth":             self.depth.value,
            "patterns":          [p.value for p in self.patterns],
            "directive":         self.directive,
            "integration_score": round(self.integration_score, 4),
        }


class ShadowIntegrationEngine:
    """Assesses and tracks shadow integration progress."""

    _DIRECTIVES = {
        IntegrationDepth.SURFACE:     "Acknowledge the shadow presence gently.",
        IntegrationDepth.PARTIAL:     "Invite deeper reflection without forcing resolution.",
        IntegrationDepth.INTEGRATED:  "The shadow has been welcomed — honour this work.",
        IntegrationDepth.TRANSCENDED: "The shadow is now a conscious ally.",
    }

    def __init__(self) -> None:
        self._history: List[ShadowReading] = []
        self._records: List[ShadowIntegrationRecord] = []

    def detect(self, context: dict) -> ShadowReading:
        """Detect shadow patterns from a context dict with optional 'turn_text'."""
        text = context.get("turn_text") or ""
        if text is None:
            text = ""
        text_lower = str(text).lower()

        detected: List[ShadowPattern] = []
        for pattern, signals in _PATTERN_SIGNALS.items():
            for sig in signals:
                if sig in text_lower:
                    detected.append(pattern)
                    break

        activation_score  = min(1.0, len(detected) * 0.2)
        integration_pct   = max(0.0, 100.0 - activation_score * 100.0)
        integration_score = integration_pct / 100.0

        if integration_pct < 25.0:
            depth = IntegrationDepth.SURFACE
        elif integration_pct < 50.0:
            depth = IntegrationDepth.PARTIAL
        elif integration_pct < 80.0:
            depth = IntegrationDepth.INTEGRATED
        else:
            depth = IntegrationDepth.TRANSCENDED

        reading = ShadowReading(
            depth=depth,
            activation_score=activation_score,
            integration_score=integration_score,
            integration_pct=integration_pct,
            directive=self._DIRECTIVES[depth],
            patterns=detected,
        )
        self._history.append(reading)
        return reading

    def integrate(
        self,
        archetype: str,
        intensity: float = 0.0,
        context:   Optional[dict] = None,
    ) -> ShadowIntegrationRecord:
        """
        Integrate a named shadow archetype at a given intensity.
        Returns a ShadowIntegrationRecord for use by SoulLayer.
        """
        ctx = context or {"turn_text": archetype}
        reading = self.detect(ctx)
        record = ShadowIntegrationRecord(
            archetype=archetype,
            intensity=intensity,
            depth=reading.depth,
            patterns=reading.patterns,
            directive=reading.directive,
            integration_score=reading.integration_score,
        )
        self._records.append(record)
        return record

    # Legacy method
    def assess(
        self,
        activation_score: float = 0.0,
        integration_pct:  float = 0.0,
        archetype:        Optional[str] = None,
    ) -> ShadowReading:
        return self.detect({"turn_text": archetype or ""})

    def history(self) -> List[ShadowReading]:
        return list(self._history)

    def records(self) -> List[ShadowIntegrationRecord]:
        return list(self._records)


_engine: Optional[ShadowIntegrationEngine] = None


def get_shadow_integration_engine() -> ShadowIntegrationEngine:
    global _engine
    if _engine is None:
        _engine = ShadowIntegrationEngine()
    return _engine
