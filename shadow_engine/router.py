"""
shadow_engine/router.py — FastAPI router for the Shadow Engine.

Exposes:
  GET  /api/shadow/{principal_id}          — fetch cached ShadowRecord (or 404)
  POST /api/shadow/{principal_id}/evaluate — run full archetype evaluation
  POST /api/shadow/{principal_id}/reflect  — record a reflection session
  GET  /api/shadow/history                 — all cached records (debug/admin)

Mount in main.py via:
  from shadow_engine.router import router as shadow_router
  app.include_router(shadow_router)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from shadow_engine.engine import get_shadow_engine
from shadow_engine.archetypes import ShadowInputs

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/shadow", tags=["Shadow"])


# ── Request / Response models ─────────────────────────────────────────────

class ShadowInputsRequest(BaseModel):
    """Optional biometric/emotional signal overrides for evaluation."""
    dominant_emotion:        str   = Field("neutral", description="e.g. anger, sadness, fear")
    valence_trend:           float = Field(0.0,  ge=-1.0, le=1.0)
    mood_momentum:           float = Field(0.0,  ge=-1.0, le=1.0)
    volatility:              float = Field(0.0,  ge=0.0,  le=1.0)
    is_volatile:             bool  = False
    arc_stability:           float = Field(0.5,  ge=0.0,  le=1.0)
    low_energy_flag:         bool  = False
    arousal:                 float = Field(0.5,  ge=0.0,  le=1.0)
    decision_entropy:        float = Field(50.0, ge=0.0,  le=100.0)
    hrv_coherence:           float = Field(50.0, ge=0.0,  le=100.0)
    journaling_depth:        float = Field(50.0, ge=0.0,  le=100.0)
    focus_session_length:    float = Field(50.0, ge=0.0,  le=100.0)
    goal_completion_rate:    float = Field(50.0, ge=0.0,  le=100.0)
    emotional_arc_stability: float = Field(50.0, ge=0.0,  le=100.0)
    days_in_stage:           int   = Field(0,    ge=0)
    regression_active:       bool  = False


class ShadowRecordResponse(BaseModel):
    principal_id:         str
    archetype:            Optional[str]
    archetype_scores:     Dict[str, float]
    active_archetype:     Optional[str]
    shadow_intensity:     float
    integration_progress: float
    days_active:          int
    is_activated:         bool
    recorded_at:          str


class ReflectionResponse(BaseModel):
    principal_id:         str
    integration_gain:     float
    integration_progress: float
    message:              str


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.get(
    "/history",
    response_model=List[ShadowRecordResponse],
    summary="All cached shadow records (admin/debug)",
)
async def get_history() -> List[Dict[str, Any]]:
    """Return all currently cached ShadowRecords across all principals."""
    engine = get_shadow_engine()
    return [r.to_dict() for r in engine.get_history()]


@router.get(
    "/{principal_id}",
    response_model=ShadowRecordResponse,
    summary="Fetch the cached ShadowRecord for a principal",
)
async def get_shadow_record(principal_id: str) -> Dict[str, Any]:
    """
    Returns the most recent cached ShadowRecord for the given principal.
    Returns 404 if no evaluation has been run yet.
    """
    engine = get_shadow_engine()
    record = await engine.get_current(principal_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No shadow record found for principal '{principal_id}'. "
                   f"Run POST /api/shadow/{principal_id}/evaluate first.",
        )
    return record.to_dict()


@router.post(
    "/{principal_id}/evaluate",
    response_model=ShadowRecordResponse,
    summary="Run a full shadow archetype evaluation",
)
async def evaluate_shadow(
    principal_id: str,
    inputs: Optional[ShadowInputsRequest] = None,
) -> Dict[str, Any]:
    """
    Scores all 7 archetypes against the provided biometric/emotional signals
    (or defaults if no body is sent), stores the result, and returns it.

    Archetypes: Orphan, Warrior, Wanderer, Caregiver, Seeker, Destroyer, Creator.
    Activation threshold: 0.35 (Canon §Shadow-3.1).
    """
    engine = get_shadow_engine()
    override: Optional[ShadowInputs] = None

    if inputs is not None:
        override = ShadowInputs(
            dominant_emotion=inputs.dominant_emotion,
            valence_trend=inputs.valence_trend,
            mood_momentum=inputs.mood_momentum,
            volatility=inputs.volatility,
            is_volatile=inputs.is_volatile,
            arc_stability=inputs.arc_stability,
            low_energy_flag=inputs.low_energy_flag,
            arousal=inputs.arousal,
            decision_entropy=inputs.decision_entropy,
            hrv_coherence=inputs.hrv_coherence,
            journaling_depth=inputs.journaling_depth,
            focus_session_length=inputs.focus_session_length,
            goal_completion_rate=inputs.goal_completion_rate,
            emotional_arc_stability=inputs.emotional_arc_stability,
            days_in_stage=inputs.days_in_stage,
            regression_active=inputs.regression_active,
        )

    record = await engine.evaluate(principal_id, override_inputs=override)
    log.info(
        "[Shadow] Evaluated principal=%s archetype=%s intensity=%.3f",
        principal_id,
        record.active_archetype,
        record.shadow_intensity,
    )
    return record.to_dict()


@router.post(
    "/{principal_id}/reflect",
    response_model=ReflectionResponse,
    summary="Record a reflection session for integration progress",
)
async def record_reflection(
    principal_id: str,
) -> Dict[str, Any]:
    """
    Registers a reflection session for the given principal, increasing their
    shadow integration_progress by REFLECTION_GAIN (0.05).
    Returns 404 if no evaluation has been run yet (nothing to integrate).
    """
    engine = get_shadow_engine()
    record = await engine.get_current(principal_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No shadow record found for '{principal_id}'. "
                   f"Run POST /api/shadow/{principal_id}/evaluate first.",
        )
    gain = engine.record_reflection_session(principal_id)
    log.info(
        "[Shadow] Reflection recorded principal=%s gain=%.3f progress=%.3f",
        principal_id,
        gain,
        record.integration_progress,
    )
    return {
        "principal_id":         principal_id,
        "integration_gain":     gain,
        "integration_progress": round(record.integration_progress, 4),
        "message": (
            f"Reflection session recorded. Integration progress: "
            f"{round(record.integration_progress * 100, 1)}%"
        ),
    }
