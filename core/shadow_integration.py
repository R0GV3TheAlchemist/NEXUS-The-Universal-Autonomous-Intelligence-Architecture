"""
Shadow Integration — integrates shadow-work signals into the GAIA psyche model.

Exposes `get_shadow_integration_engine()` singleton accessor.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

log = logging.getLogger(__name__)


class ShadowIntegrationStage(str, Enum):
    DENIAL = "denial"
    RECOGNITION = "recognition"
    CONFRONTATION = "confrontation"
    ACCEPTANCE = "acceptance"
    INTEGRATION = "integration"
    TRANSCENDENCE = "transcendence"


@dataclass
class ShadowIntegrationRecord:
    """Records a single shadow-integration event."""

    archetype: str = ""
    stage: ShadowIntegrationStage = ShadowIntegrationStage.DENIAL
    intensity: float = 0.0
    resolved: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "archetype": self.archetype,
            "stage": self.stage.value,
            "intensity": self.intensity,
            "resolved": self.resolved,
            "metadata": self.metadata,
        }


class ShadowIntegrationEngine:
    """Manages the shadow-integration process for GAIA."""

    def __init__(self) -> None:
        self._records: List[ShadowIntegrationRecord] = []
        log.info("ShadowIntegrationEngine initialised")

    def integrate(
        self,
        archetype: str,
        intensity: float = 0.0,
        stage: ShadowIntegrationStage = ShadowIntegrationStage.RECOGNITION,
    ) -> ShadowIntegrationRecord:
        record = ShadowIntegrationRecord(
            archetype=archetype,
            stage=stage,
            intensity=max(0.0, min(1.0, intensity)),
        )
        self._records.append(record)
        return record

    def resolve(self, archetype: str) -> None:
        for r in self._records:
            if r.archetype == archetype:
                r.resolved = True
                r.stage = ShadowIntegrationStage.INTEGRATION

    def get_records(self, resolved: Optional[bool] = None) -> List[ShadowIntegrationRecord]:
        if resolved is None:
            return list(self._records)
        return [r for r in self._records if r.resolved == resolved]

    def reset(self) -> None:
        self._records.clear()

    def to_dict(self) -> dict:
        return {
            "record_count": len(self._records),
            "resolved_count": sum(1 for r in self._records if r.resolved),
        }


_engine: Optional[ShadowIntegrationEngine] = None


def get_shadow_integration_engine() -> ShadowIntegrationEngine:
    """Return the module-level singleton ShadowIntegrationEngine."""
    global _engine
    if _engine is None:
        _engine = ShadowIntegrationEngine()
    return _engine
