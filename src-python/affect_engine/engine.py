"""
affect_engine.engine — Affective State Engine

Models agent affective state using the PAD dimensional space:
  - Pleasure  (valence)  : −1.0 (very negative) → +1.0 (very positive)
  - Arousal   (intensity): 0.0 (calm) → 1.0 (highly activated)
  - Dominance (control)  : 0.0 (submissive) → 1.0 (dominant)

Appraisal events (OCC model) update the PAD state. An EmotionalRegulator
applies dampening to prevent runaway arousal.

Reference: Mehrabian & Russell 1974 (PAD); Ortony, Clore & Collins 1988 (OCC)
           NEXUS_UNIVERSAL_OS.md Domain 2.7
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("affect_engine.engine")


@dataclass
class AffectState:
    """Current PAD affective state of the agent."""
    pleasure:   float = 0.0   # -1.0 → +1.0
    arousal:    float = 0.0   #  0.0 →  1.0
    dominance:  float = 0.5   #  0.0 →  1.0

    def clamp(self) -> None:
        """Clamp all values to their valid ranges."""
        self.pleasure  = max(-1.0, min(1.0, self.pleasure))
        self.arousal   = max(0.0,  min(1.0, self.arousal))
        self.dominance = max(0.0,  min(1.0, self.dominance))


class AffectEngine:
    """Maintains and updates the agent's PAD affective state.

    Appraisal events are fed in via appraise(). The state is updated
    using weighted delta rules. EmotionalRegulator dampening is applied
    each cycle to prevent runaway values.
    Reference: NEXUS_UNIVERSAL_OS.md Domain 2.7; PAD model.
    """

    def __init__(self, initial_state: Optional[AffectState] = None) -> None:
        self._state = initial_state or AffectState()
        logger.info("AffectEngine initialised with state %s", self._state)

    @property
    def state(self) -> AffectState:
        """Return the current affective state (read-only snapshot)."""
        return AffectState(
            pleasure=self._state.pleasure,
            arousal=self._state.arousal,
            dominance=self._state.dominance,
        )

    def appraise(self, event_type: str, intensity: float = 0.5) -> AffectState:
        """Apply an OCC appraisal event and update the PAD state.

        Args:
            event_type: OCC event category string (e.g. 'joy', 'distress', 'hope').
            intensity:  Event intensity multiplier [0.0, 1.0].
        Returns:
            Updated AffectState.
        Raises:
            NotImplementedError: Always (stub).
        Reference: OCC model; NEXUS_UNIVERSAL_OS.md Domain 2.7.
        """
        raise NotImplementedError(
            "AffectEngine.appraise — not yet implemented. "
            "Expected: map event_type to PAD deltas via OCC appraisal rules, "
            "update self._state, apply EmotionalRegulator dampening, clamp, return state."
        )

    def regulate(self) -> None:
        """Apply homeostatic dampening toward neutral state each cycle.

        Raises:
            NotImplementedError: Always (stub).
        """
        raise NotImplementedError(
            "AffectEngine.regulate — not yet implemented. "
            "Expected: apply exponential decay toward (0.0, 0.0, 0.5) baseline."
        )
