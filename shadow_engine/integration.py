"""
shadow_engine.integration — integrates shadow detections into the psyche model.

Provides:
  - ShadowIntegrationPipeline : high-level integration pipeline
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from shadow_engine.archetypes import ArchetypeDetectionResult, ShadowArchetype

log = logging.getLogger(__name__)


@dataclass
class IntegrationRecord:
    """Records the outcome of a single integration step."""

    archetype: ShadowArchetype = ShadowArchetype.THE_SHADOW
    depth: float = 0.0
    resolved: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "archetype": self.archetype.value,
            "depth": self.depth,
            "resolved": self.resolved,
            "metadata": self.metadata,
        }


class ShadowIntegrationPipeline:
    """Integrates archetype detections into the shadow-integration model."""

    def __init__(self) -> None:
        self._records: List[IntegrationRecord] = []
        log.info("ShadowIntegrationPipeline initialised")

    def integrate(self, detection: ArchetypeDetectionResult) -> IntegrationRecord:
        depth = detection.confidence * 0.8
        record = IntegrationRecord(
            archetype=detection.primary,
            depth=depth,
            resolved=depth > 0.5,
        )
        self._records.append(record)
        return record

    def get_records(self) -> List[IntegrationRecord]:
        return list(self._records)

    def reset(self) -> None:
        self._records.clear()

    def to_dict(self) -> dict:
        return {
            "record_count": len(self._records),
            "resolved_count": sum(1 for r in self._records if r.resolved),
        }


_pipeline: Optional[ShadowIntegrationPipeline] = None


def get_shadow_integration_pipeline() -> ShadowIntegrationPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ShadowIntegrationPipeline()
    return _pipeline
