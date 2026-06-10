"""
shadow_engine.engine — main shadow-engine orchestrator.

Provides:
  - ShadowEngine : orchestrates archetype detection and integration
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from shadow_engine.archetypes import (
    ArchetypeDetector,
    ArchetypeDetectionResult,
    ShadowInputs,
)

log = logging.getLogger(__name__)


@dataclass
class ShadowEngineResult:
    """Combined output of a shadow-engine processing pass."""

    detection: ArchetypeDetectionResult = field(
        default_factory=ArchetypeDetectionResult
    )
    intensity_modifier: float = 1.0
    integrated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "detection": self.detection.to_dict(),
            "intensity_modifier": self.intensity_modifier,
            "integrated": self.integrated,
            "metadata": self.metadata,
        }


class ShadowEngine:
    """Orchestrates archetype detection and shadow integration."""

    def __init__(self) -> None:
        self._detector = ArchetypeDetector()
        self._history: List[ShadowEngineResult] = []
        log.info("ShadowEngine initialised")

    def process(self, inputs: ShadowInputs) -> ShadowEngineResult:
        detection = self._detector.detect(inputs)
        result = ShadowEngineResult(
            detection=detection,
            intensity_modifier=max(0.1, 1.0 - detection.confidence * 0.5),
        )
        self._history.append(result)
        return result

    def get_history(self) -> List[ShadowEngineResult]:
        return list(self._history)

    def reset(self) -> None:
        self._history.clear()


_shadow_engine: Optional[ShadowEngine] = None


def get_shadow_engine() -> ShadowEngine:
    global _shadow_engine
    if _shadow_engine is None:
        _shadow_engine = ShadowEngine()
    return _shadow_engine
