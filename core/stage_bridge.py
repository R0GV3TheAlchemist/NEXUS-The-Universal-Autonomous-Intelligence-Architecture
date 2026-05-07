"""
GAIA-OS Stage Bridge

Wires AffectInference (core/affect_inference.py) to StageEngine
(core/stage_engine.py).

Responsibilities:
  1. Translate FeelingState fields to StageEngine.update() parameters
  2. Provide is_shadow_surface_safe() — the combined stage + affect
     constitutional safety gate for the Shadow Engine

Wiring Map:
  FeelingState.conflict_density (0.0–1.0)
      → emotional_volatility_raw (0–100)

  FeelingState.coherence_phi (0.0–1.0)
      → hrv_rmssd_ms proxy (20–100 ms) when no wearable is present
      Formula: hrv_proxy = 20 + phi * 80
      (maps phi=0.0 → 20ms baseline, phi=1.0 → 100ms excellent HRV)

Shadow Surface Safety Gate:
  Stage gate:   get_shadow_mode(stage) must not be 'off'
  Affect gate:  affect_state must not be DISSONANCE or GRIEF
  Both must pass. Constitutional rule: never surface shadow patterns
  during active conflict or grief states.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from core.affect_inference import AffectInference, AffectState, FeelingState
from core.stage_engine import StageEngine, StageRecord, get_shadow_mode


# Affect states that block Shadow Engine surfacing regardless of stage
_SHADOW_BLOCKED_AFFECTS = {AffectState.DISSONANCE, AffectState.GRIEF}


class AffectStageAdapter:
    """
    Translates AffectInference output into StageEngine inputs and
    drives the Stage Engine update cycle.

    Usage:
        adapter = AffectStageAdapter()
        feeling = AffectInference().infer(...)
        record = adapter.update(
            user_id="user_gaia",
            feeling=feeling,
            journal_word_count=350.0,
            focus_minutes_avg=25.0,
            goal_completion_pct=45.0,
            decision_entropy_raw=55.0,
            regression_days_sustained=0,
        )
    """

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        kwargs = {"db_path": db_path} if db_path is not None else {}
        self._engine = StageEngine(**kwargs)

    def update(
        self,
        user_id: str,
        feeling: FeelingState,
        *,
        journal_word_count: float,
        focus_minutes_avg: float,
        goal_completion_pct: float,
        decision_entropy_raw: float,
        regression_days_sustained: int = 0,
        hrv_rmssd_ms_override: Optional[float] = None,
    ) -> StageRecord:
        """
        Drive a Stage Engine update from an AffectInference output.

        If hrv_rmssd_ms_override is provided (e.g. from a real wearable),
        it takes precedence over the coherence_phi proxy.
        """
        # Map conflict_density → emotional_volatility_raw
        emotional_volatility_raw = feeling.conflict_density * 100.0

        # Map coherence_phi → HRV proxy (unless real wearable data supplied)
        if hrv_rmssd_ms_override is not None:
            hrv_rmssd_ms = hrv_rmssd_ms_override
        else:
            hrv_rmssd_ms = 20.0 + feeling.coherence_phi * 80.0

        return self._engine.update(
            user_id,
            decision_entropy_raw=decision_entropy_raw,
            hrv_rmssd_ms=hrv_rmssd_ms,
            journal_word_count=journal_word_count,
            focus_minutes_avg=focus_minutes_avg,
            goal_completion_pct=goal_completion_pct,
            emotional_volatility_raw=emotional_volatility_raw,
            regression_days_sustained=regression_days_sustained,
        )

    @property
    def engine(self) -> StageEngine:
        """Direct access to the underlying StageEngine."""
        return self._engine


def is_shadow_surface_safe(stage: int, feeling: FeelingState) -> bool:
    """
    Returns True only when it is constitutionally safe to surface a
    Shadow Engine observation to the user.

    Two gates must both pass:
      1. Stage gate: Shadow Engine must not be in 'off' mode (Stage 1)
      2. Affect gate: Current affect must not be DISSONANCE or GRIEF

    Rationale: surfacing contradictions or shadow patterns during active
    conflict or grief violates the constitutional principle that GAIA
    never exploits vulnerable states.

    Args:
        stage:   Current user stage (1–5)
        feeling: Current FeelingState from AffectInference

    Returns:
        bool
    """
    stage_gate = get_shadow_mode(stage) != "off"
    affect_gate = feeling.affect_state not in _SHADOW_BLOCKED_AFFECTS
    return stage_gate and affect_gate
