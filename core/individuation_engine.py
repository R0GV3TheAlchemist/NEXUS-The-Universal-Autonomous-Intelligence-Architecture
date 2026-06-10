"""
Individuation Engine — models Jungian individuation arc for GAIA users.

Provides:
  - IndividuationScore  : dataclass holding a user's current score
  - IndividuationEngine : main class
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

log = logging.getLogger(__name__)


class IndividuationPhase(str, Enum):
    SHADOW_WORK = "shadow_work"
    ANIMA_ANIMUS = "anima_animus"
    SELF_ENCOUNTER = "self_encounter"
    INTEGRATION = "integration"
    WHOLENESS = "wholeness"


@dataclass
class IndividuationScore:
    """Captures the multi-dimensional individuation state of a user."""

    user_id: str = ""
    phase: IndividuationPhase = IndividuationPhase.SHADOW_WORK
    overall: float = 0.0          # 0.0 – 1.0
    shadow: float = 0.0
    anima_animus: float = 0.0
    self_realisation: float = 0.0
    integration: float = 0.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "phase": self.phase.value,
            "overall": self.overall,
            "shadow": self.shadow,
            "anima_animus": self.anima_animus,
            "self_realisation": self.self_realisation,
            "integration": self.integration,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class IndividuationEngine:
    """Tracks and updates individuation scores for users."""

    def __init__(self) -> None:
        self._scores: Dict[str, IndividuationScore] = {}
        log.info("IndividuationEngine initialised")

    def get_score(self, user_id: str) -> IndividuationScore:
        if user_id not in self._scores:
            self._scores[user_id] = IndividuationScore(user_id=user_id)
        return self._scores[user_id]

    def update(
        self,
        user_id: str,
        shadow: Optional[float] = None,
        anima_animus: Optional[float] = None,
        self_realisation: Optional[float] = None,
        integration: Optional[float] = None,
    ) -> IndividuationScore:
        score = self.get_score(user_id)
        if shadow is not None:
            score.shadow = max(0.0, min(1.0, shadow))
        if anima_animus is not None:
            score.anima_animus = max(0.0, min(1.0, anima_animus))
        if self_realisation is not None:
            score.self_realisation = max(0.0, min(1.0, self_realisation))
        if integration is not None:
            score.integration = max(0.0, min(1.0, integration))
        score.overall = (
            score.shadow + score.anima_animus + score.self_realisation + score.integration
        ) / 4.0
        return score

    def reset(self, user_id: str) -> None:
        self._scores.pop(user_id, None)


_engine: Optional[IndividuationEngine] = None


def get_individuation_engine() -> IndividuationEngine:
    global _engine
    if _engine is None:
        _engine = IndividuationEngine()
    return _engine
