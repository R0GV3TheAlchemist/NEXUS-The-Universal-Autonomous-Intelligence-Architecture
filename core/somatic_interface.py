"""
core/somatic_interface.py
Somatic Interface — bridges physiological signals into GAIA state.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SomaticReading:
    heart_rate_variability: float = 0.5
    breath_depth:           float = 0.5
    tension_index:          float = 0.0
    grounding_score:        float = 0.5
    somatic_coherence:      float = 0.5

    def to_dict(self) -> dict:
        return {
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

    def read(
        self,
        hrv:       float = 0.5,
        breath:    float = 0.5,
        tension:   float = 0.0,
        grounding: float = 0.5,
    ) -> SomaticReading:
        coherence = max(0.0, min(1.0,
            0.35 * hrv
            + 0.25 * breath
            + 0.25 * grounding
            - 0.15 * tension
        ))
        reading = SomaticReading(
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
