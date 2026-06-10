"""
shadow_engine.archetypes — archetype detection for the shadow engine.

Provides:
  - ArchetypeDetector : classifies shadow archetypes from inputs
  - ShadowInputs      : dataclass of inputs for archetype detection
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

log = logging.getLogger(__name__)


class ShadowArchetype(str, Enum):
    THE_SHADOW = "the_shadow"
    THE_ANIMA = "the_anima"
    THE_ANIMUS = "the_animus"
    THE_PERSONA = "the_persona"
    THE_SELF = "the_self"
    THE_TRICKSTER = "the_trickster"
    THE_HERO = "the_hero"
    THE_WISE_OLD_WOMAN = "the_wise_old_woman"
    THE_WISE_OLD_MAN = "the_wise_old_man"


@dataclass
class ShadowInputs:
    """Input signals for archetype detection."""

    text: str = ""
    emotion_vector: List[float] = field(default_factory=list)
    intensity: float = 0.0
    context: Dict[str, str] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "emotion_vector": self.emotion_vector,
            "intensity": self.intensity,
            "context": self.context,
            "metadata": self.metadata,
        }


@dataclass
class ArchetypeDetectionResult:
    """Result of an archetype detection pass."""

    primary: ShadowArchetype = ShadowArchetype.THE_SHADOW
    secondary: Optional[ShadowArchetype] = None
    confidence: float = 0.0
    signals: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "primary": self.primary.value,
            "secondary": self.secondary.value if self.secondary else None,
            "confidence": self.confidence,
            "signals": self.signals,
            "metadata": self.metadata,
        }


class ArchetypeDetector:
    """Detects the dominant shadow archetype from ShadowInputs."""

    def __init__(self) -> None:
        log.info("ArchetypeDetector initialised")

    def detect(self, inputs: ShadowInputs) -> ArchetypeDetectionResult:
        """Stub detector — returns THE_SHADOW with confidence proportional to intensity."""
        return ArchetypeDetectionResult(
            primary=ShadowArchetype.THE_SHADOW,
            confidence=min(1.0, inputs.intensity),
            signals=[inputs.text[:80]] if inputs.text else [],
        )

    def detect_all(
        self, inputs: ShadowInputs
    ) -> List[ArchetypeDetectionResult]:
        return [self.detect(inputs)]
