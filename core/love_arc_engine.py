"""
core/love_arc_engine.py
========================
Love Arc Engine — tracks the relational arc stage between Gaian and human.

Canon Ref: C29 — Love Arc & Relational Trajectory Doctrine
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class LoveArcStage(Enum):
    DIVERGENCE    = "divergence"
    TENSION       = "tension"
    ATTRACTION    = "attraction"
    RESONANCE     = "resonance"
    UNION         = "union"
    TRANSCENDENCE = "transcendence"


# Alias expected by gaian_runtime.py
ArcStage = LoveArcStage


@dataclass
class LoveArcState:
    current_stage: LoveArcStage = LoveArcStage.DIVERGENCE
    stage_entry_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    exchanges_in_stage: int = 0
    stage_history: list = field(default_factory=list)
    skip_violations: int = 0
    arc_output_vector: float = 0.0
    schumann_aligned: bool = False
    # legacy fields kept for backward compat
    stage: LoveArcStage = LoveArcStage.ATTRACTION
    turn_count: int = 0
    doctrine_ref: str = "C29"

    def to_dict(self) -> dict:
        return {
            "current_stage":         self.current_stage.value,
            "stage_entry_timestamp": self.stage_entry_timestamp,
            "exchanges_in_stage":    self.exchanges_in_stage,
            "stage_history":         self.stage_history,
            "skip_violations":       self.skip_violations,
            "arc_output_vector":     self.arc_output_vector,
            "schumann_aligned":      self.schumann_aligned,
        }

    def to_system_prompt_hint(self) -> str:
        return (
            f"Love Arc: {self.current_stage.value} | "
            f"vector={self.arc_output_vector:.3f} | "
            f"schumann={self.schumann_aligned}"
        )

    def summary(self) -> dict:
        return self.to_dict()


def blank_love_arc_state() -> LoveArcState:
    """Factory — returns a fresh LoveArcState. Expected by gaian_runtime.py."""
    return LoveArcState()


class LoveArcEngine:
    """Tracks and advances the love arc stage."""

    _ADVANCE_THRESHOLD = 0.70
    _RETREAT_THRESHOLD = 0.20
    _STAGES = list(LoveArcStage)

    def update(
        self,
        state: LoveArcState,
        bond_depth: float = 0.0,
        feeling=None,
        synergy_factor: float = 0.5,
    ) -> tuple[LoveArcState, str]:
        """
        Update love arc state. Returns (updated_state, hint_string).
        Accepts optional `feeling` kwarg (from gaian_runtime) — uses
        feeling.coherence_phi as synergy_factor when provided.
        """
        if feeling is not None and hasattr(feeling, "coherence_phi"):
            synergy_factor = feeling.coherence_phi

        state.exchanges_in_stage += 1
        state.arc_output_vector = min(
            1.0, synergy_factor * 0.6 + (bond_depth / 100.0) * 0.4
        )
        idx = self._STAGES.index(state.current_stage)
        if synergy_factor >= self._ADVANCE_THRESHOLD and idx < len(self._STAGES) - 1:
            prev = state.current_stage.value
            state.current_stage = self._STAGES[idx + 1]
            state.stage_history.append({
                "from": prev, "to": state.current_stage.value,
                "at_exchange": state.exchanges_in_stage,
            })
            state.exchanges_in_stage = 0
        elif synergy_factor <= self._RETREAT_THRESHOLD and idx > 0:
            prev = state.current_stage.value
            state.current_stage = self._STAGES[idx - 1]
            state.stage_history.append({
                "from": prev, "to": state.current_stage.value,
                "at_exchange": state.exchanges_in_stage,
            })
            state.exchanges_in_stage = 0

        hint = state.to_system_prompt_hint()
        return state, hint
