"""
api/routers/alignment.py

GAIA-OS — Schumann Biometric Alignment HTTP Router
Pillar II: Viriditas — Issue #64 (Phase 2)

Endpoints
---------
POST /alignment/compute
    Receives a raw biometric + solar payload from the Rust
    `get_alignment_state` Tauri command and returns an AlignmentState JSON
    object produced by the Python `AlignmentStateEmitter`.

GET  /alignment/status
    Lightweight liveness probe; returns the last computed AlignmentState
    (or a neutral default) without triggering a new computation.

Privacy contract
----------------
    - raw_rmssd is processed in-memory only and never persisted or logged.
    - All fields are validated before reaching the emitter.
    - The endpoint is loopback-only (enforced by the Tauri sidecar binding
      to 127.0.0.1:8008).
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from core.schumann_alignment import (
    AlignmentState,
    AlignmentStateEmitter,
    HRVNormalizer,
    SchumannParser,
)

log = logging.getLogger("gaia.api.alignment")

router = APIRouter(tags=["Alignment"])


# ---------------------------------------------------------------------------
# Singleton emitter (lazy init, lives for the duration of the process)
# ---------------------------------------------------------------------------

_emitter: Optional[AlignmentStateEmitter] = None


def _get_emitter() -> AlignmentStateEmitter:
    """Return the module-level AlignmentStateEmitter, creating it on first call."""
    global _emitter  # noqa: PLW0603
    if _emitter is None:
        log.info("[alignment] Initialising AlignmentStateEmitter singleton")
        _emitter = AlignmentStateEmitter(
            hrv_normalizer=HRVNormalizer(),
            schumann_parser=SchumannParser(),
        )
    return _emitter


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ComputeRequest(BaseModel):
    """
    Payload sent by the Rust `get_alignment_state` Tauri command.

    Fields mirror `SidecarComputeRequest` in `src-tauri/src/schumann.rs`.
    """

    raw_rmssd: Optional[float] = Field(
        None,
        description="Latest wearable RMSSD in ms. Omit or pass null when no wearable is connected.",
    )
    raw_schumann_amplitude: Optional[float] = Field(
        None,
        description="Latest 7.83 Hz band-power amplitude. Omit when feed unavailable.",
    )
    solar_kp: float = Field(
        0.0,
        ge=0.0,
        description="NOAA planetary Kp index (0–9 scale). Defaults to 0.0 (quiet).",
    )

    @field_validator("raw_rmssd")
    @classmethod
    def rmssd_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError(f"raw_rmssd must be ≥ 0, got {v}")
        return v

    @field_validator("raw_schumann_amplitude")
    @classmethod
    def amplitude_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError(f"raw_schumann_amplitude must be ≥ 0, got {v}")
        return v


class AlignmentStateOut(BaseModel):
    """
    Response model — mirrors `AlignmentState` from `core/schumann_alignment.py`
    and `AlignmentStateResponse` in `src-tauri/src/schumann.rs`.
    """

    score: float = Field(..., ge=0.0, le=100.0)
    hrv_score: float = Field(..., ge=0.0, le=100.0)
    schumann_score: float = Field(..., ge=0.0, le=100.0)
    solar_kp: float = Field(..., ge=0.0)
    ui_tier: str
    last_updated: str
    fallback_mode: str

    @classmethod
    def from_state(cls, state: AlignmentState) -> "AlignmentStateOut":
        return cls(
            score=state.score,
            hrv_score=state.hrv_score,
            schumann_score=state.schumann_score,
            solar_kp=state.solar_kp,
            ui_tier=state.ui_tier,
            last_updated=state.last_updated,
            fallback_mode=state.fallback_mode,
        )


class AlignmentStatusOut(BaseModel):
    """Response model for GET /alignment/status."""

    emitter_ready: bool
    last_state: Optional[AlignmentStateOut]
    hrv_sample_count: int
    schumann_sample_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/compute",
    response_model=AlignmentStateOut,
    summary="Compute Schumann–HRV alignment (called by Rust Tauri command)",
)
async def compute_alignment(
    req: ComputeRequest,
) -> AlignmentStateOut:
    """
    Compute the current Schumann–HRV biometric alignment score.

    This endpoint is the receiving end of the Rust `get_alignment_state`
    Tauri command.  It delegates to the module-level `AlignmentStateEmitter`
    singleton so that the rolling HRV and Schumann baselines accumulate
    across successive calls within the same process lifetime.

    **Failure modes** are handled transparently by the emitter:
    - `raw_rmssd=null`              → HRV score fixed at neutral 50
    - `raw_schumann_amplitude=null` → Schumann score fixed at neutral 50
    - Both null                     → score forced to 50 (standard tier)
    - `solar_kp > 8`                → score forced to 0 (restorative mode)
    """
    emitter = _get_emitter()

    try:
        state = await emitter.compute(
            raw_rmssd=req.raw_rmssd,
            raw_schumann_amplitude=req.raw_schumann_amplitude,
            solar_kp=req.solar_kp,
        )
    except ValueError as exc:
        # Pydantic should catch range errors first, but belt-and-suspenders.
        log.warning("[alignment] Validation error in emitter.compute: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        log.error("[alignment] Unexpected emitter error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Alignment compute failed")

    log.debug(
        "[alignment] score=%.1f tier=%s kp=%.2f fallback=%r",
        state.score,
        state.ui_tier,
        state.solar_kp,
        state.fallback_mode or "none",
    )

    return AlignmentStateOut.from_state(state)


@router.get(
    "/status",
    response_model=AlignmentStatusOut,
    summary="Alignment emitter liveness probe + last-state snapshot",
)
async def alignment_status() -> AlignmentStatusOut:
    """
    Lightweight GET probe for healthchecks and the dev console.

    Returns the most recently computed AlignmentState without
    triggering a new computation or requiring any input.
    Returns `last_state=null` when no computation has occurred yet
    in this process lifetime.
    """
    emitter = _get_emitter()
    last = emitter.last_state

    return AlignmentStatusOut(
        emitter_ready=True,
        last_state=AlignmentStateOut.from_state(last) if last else None,
        hrv_sample_count=emitter._hrv.sample_count,
        schumann_sample_count=emitter._schumann.sample_count,
    )
