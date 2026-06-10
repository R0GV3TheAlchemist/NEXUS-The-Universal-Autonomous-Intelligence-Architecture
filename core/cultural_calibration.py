"""
Cultural Calibration — adapts GAIA responses to cultural context.

Exposes the module-level singleton factory `get_cultural_calibration_engine()`
in addition to the full engine implementation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class CulturalDimension(str, Enum):
    INDIVIDUALISM = "individualism"
    COLLECTIVISM = "collectivism"
    HIGH_CONTEXT = "high_context"
    LOW_CONTEXT = "low_context"
    POWER_DISTANCE = "power_distance"
    UNCERTAINTY_AVOIDANCE = "uncertainty_avoidance"
    LONG_TERM_ORIENTATION = "long_term_orientation"


@dataclass
class CulturalProfile:
    """A snapshot of cultural calibration values for a user or context."""

    locale: str = "en"
    dimensions: Dict[CulturalDimension, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "locale": self.locale,
            "dimensions": {k.value: v for k, v in self.dimensions.items()},
            "tags": self.tags,
            "metadata": self.metadata,
        }


class CulturalCalibrationEngine:
    """Engine that calibrates GAIA output to cultural context."""

    def __init__(self) -> None:
        self._profiles: Dict[str, CulturalProfile] = {}
        log.info("CulturalCalibrationEngine initialised")

    def get_profile(self, locale: str = "en") -> CulturalProfile:
        if locale not in self._profiles:
            self._profiles[locale] = CulturalProfile(locale=locale)
        return self._profiles[locale]

    def calibrate(
        self,
        text: str,
        locale: str = "en",
    ) -> str:
        """Return text calibrated for the given locale (stub: returns as-is)."""
        _ = self.get_profile(locale)
        return text

    def set_dimension(
        self,
        locale: str,
        dimension: CulturalDimension,
        value: float,
    ) -> None:
        profile = self.get_profile(locale)
        profile.dimensions[dimension] = max(0.0, min(1.0, value))

    def reset(self) -> None:
        self._profiles.clear()

    def to_dict(self) -> dict:
        return {locale: p.to_dict() for locale, p in self._profiles.items()}


_engine: Optional[CulturalCalibrationEngine] = None


def get_cultural_calibration_engine() -> CulturalCalibrationEngine:
    """Return the module-level singleton CulturalCalibrationEngine."""
    global _engine
    if _engine is None:
        _engine = CulturalCalibrationEngine()
    return _engine
