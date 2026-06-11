"""
shadow_engine.engine — main shadow-engine orchestrator.

Provides:
  - ShadowEngine : async evaluate / get_current / record_reflection_session
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from shadow_engine.archetypes import ArchetypeDetector, ShadowInputs
from shadow_engine.intensity import compute_shadow_intensity
from shadow_engine.types import (
    ACTIVATION_THRESHOLD,
    CO_ACTIVE_DELTA,
    ShadowRecord,
)

log = logging.getLogger(__name__)

# Integration gain per reflection session
_REFLECTION_GAIN: float = 0.05


class ShadowEngine:
    """Per-user shadow archetype engine."""

    def __init__(self) -> None:
        self._detector = ArchetypeDetector()
        self._records: Dict[str, ShadowRecord] = {}
        log.info("ShadowEngine initialised")

    # ─────────────────────── public async API ───────────────────────────────

    async def evaluate(
        self,
        principal_id: str,
        *,
        override_inputs: Optional[ShadowInputs] = None,
    ) -> ShadowRecord:
        """
        Run a full shadow evaluation for *principal_id*.

        Args:
            principal_id:    Stable user identifier.
            override_inputs: If provided, use these instead of live biometrics.

        Returns:
            A populated ShadowRecord stored in the engine cache.
        """
        inputs = override_inputs or ShadowInputs()
        scores = self._detector.score_all(inputs)

        active_name, co_active = self._resolve_active(scores)

        existing = self._records.get(principal_id)
        days_active = existing.days_active if existing else 0
        integration = existing.integration_progress if existing else 0.0

        top_score = scores.get(active_name, 0.0) if active_name else 0.0
        intensity = compute_shadow_intensity(top_score, days_active)

        record = ShadowRecord(
            principal_id=principal_id,
            archetype_scores=scores,
            active_archetype=active_name,
            shadow_intensity=intensity,
            integration_progress=integration,
            days_active=days_active,
        )
        self._records[principal_id] = record
        return record

    async def get_current(self, principal_id: str) -> Optional[ShadowRecord]:
        """Return the last cached ShadowRecord for *principal_id*, or None."""
        return self._records.get(principal_id)

    def record_reflection_session(self, principal_id: str) -> float:
        """
        Register a reflection session for *principal_id*, increasing integration.

        Returns:
            The integration gain applied (0.0 if user not found).
        """
        record = self._records.get(principal_id)
        if record is None:
            return 0.0
        record.integration_progress = min(
            1.0, record.integration_progress + _REFLECTION_GAIN
        )
        return _REFLECTION_GAIN

    # ─────────────────────── internals ──────────────────────────────────────

    @staticmethod
    def _resolve_active(
        scores: Dict[str, float],
    ) -> Tuple[Optional[str], List[str]]:
        """
        Determine the primary active archetype and any co-active ones.

        Returns:
            (primary_name_or_None, [co_active_names])
        """
        if not scores:
            return None, []

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top_name, top_score = ranked[0]

        if top_score < ACTIVATION_THRESHOLD:
            return None, []

        co_active = [
            name
            for name, score in ranked[1:]
            if score >= ACTIVATION_THRESHOLD and (top_score - score) <= CO_ACTIVE_DELTA
        ]
        return top_name, co_active

    def get_history(self) -> List[ShadowRecord]:
        return list(self._records.values())

    def reset(self) -> None:
        self._records.clear()


_shadow_engine: Optional[ShadowEngine] = None


def get_shadow_engine() -> ShadowEngine:
    global _shadow_engine
    if _shadow_engine is None:
        _shadow_engine = ShadowEngine()
    return _shadow_engine
