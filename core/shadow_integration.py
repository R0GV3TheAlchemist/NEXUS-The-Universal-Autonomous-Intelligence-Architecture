"""
core/shadow_integration.py
Shadow Integration — soul-mirror shadow work integration layer.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class IntegrationDepth(str, Enum):
    SURFACE     = "surface"
    PARTIAL     = "partial"
    INTEGRATED  = "integrated"
    TRANSCENDED = "transcended"


@dataclass
class ShadowReading:
    """Output of a single shadow integration assessment."""
    depth:            IntegrationDepth = IntegrationDepth.SURFACE
    activation_score: float = 0.0
    integration_pct:  float = 0.0
    archetype:        Optional[str] = None
    directive:        str = ""

    def to_dict(self) -> dict:
        return {
            "depth":            self.depth.value,
            "activation_score": round(self.activation_score, 4),
            "integration_pct":  round(self.integration_pct, 4),
            "archetype":        self.archetype,
            "directive":        self.directive,
        }

    def summary(self) -> dict:
        return self.to_dict()


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

    def assess(
        self,
        activation_score: float = 0.0,
        integration_pct:  float = 0.0,
        archetype:        Optional[str] = None,
    ) -> ShadowReading:
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
            integration_pct=integration_pct,
            archetype=archetype,
            directive=self._DIRECTIVES[depth],
        )
        self._history.append(reading)
        return reading

    def history(self) -> List[ShadowReading]:
        return list(self._history)


_engine: Optional[ShadowIntegrationEngine] = None


def get_shadow_integration_engine() -> ShadowIntegrationEngine:
    global _engine
    if _engine is None:
        _engine = ShadowIntegrationEngine()
    return _engine
