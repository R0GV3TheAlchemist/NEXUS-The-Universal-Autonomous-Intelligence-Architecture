"""
crystal/router.py
FastAPI router for the Crystal Core.

Mounts at: /crystal

Endpoints
---------
GET  /crystal/health          — liveness probe
GET  /crystal/state           — current CrystalState as JSON
GET  /crystal/history?days=N  — last N days of tick history
POST /crystal/tick            — force an immediate re-tick
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing   import Optional

from fastapi           import APIRouter
from fastapi.responses import JSONResponse

from .engine import CrystalCore
from .types  import CrystalState, OrbParams

router = APIRouter(prefix="/crystal", tags=["crystal"])

# Module-level singleton; call init_crystal() from app lifespan.
_core: Optional[CrystalCore] = None


# ---------------------------------------------------------------------------
# Lifecycle helper — called from main.py lifespan
# ---------------------------------------------------------------------------

def init_crystal(principal_id: str = "default") -> None:
    """Initialise the global CrystalCore singleton."""
    global _core
    _core = CrystalCore(principal_id=principal_id)


async def get_crystal_state() -> Optional[CrystalState]:
    """Return the latest cached CrystalState without triggering a tick."""
    if _core is None:
        return None
    return _core.latest


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({
        "status":    "ok",
        "service":   "crystal_core",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "has_state": _core is not None and _core.latest is not None,
    })


@router.get("/state")
async def get_state() -> JSONResponse:
    if _core is None:
        return JSONResponse(status_code=503, content={"error": "crystal core not initialised"})
    state = _core.latest
    if state is None:
        # No tick yet — run one now
        state = await _core.tick()
    return JSONResponse(_serialise(state))


@router.get("/history")
async def get_history(days: int = 7) -> JSONResponse:
    if _core is None:
        return JSONResponse(status_code=503, content={"error": "crystal core not initialised"})
    ticks = _core.history(days=days)
    return JSONResponse({
        "days":   days,
        "count":  len(ticks),
        "ticks":  [_serialise(t) for t in ticks],
    })


@router.post("/tick")
async def force_tick() -> JSONResponse:
    if _core is None:
        return JSONResponse(status_code=503, content={"error": "crystal core not initialised"})
    state = await _core.tick()
    return JSONResponse(_serialise(state))


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def _serialise_orb(orb: OrbParams) -> dict:
    return {
        "glow_color":       orb.glow_color,
        "glow_intensity":   round(orb.glow_intensity,   4),
        "pulse_frequency":  round(orb.pulse_frequency,  4),
        "pulse_amplitude":  round(orb.pulse_amplitude,  4),
        "cloud_opacity":    round(orb.cloud_opacity,    4),
        "aurora_intensity": round(orb.aurora_intensity, 4),
        "rotation_speed":   round(orb.rotation_speed,   4),
        "coherence_ring":   round(orb.coherence_ring,   4),
    }


def _serialise(state: CrystalState) -> dict:
    return {
        "timestamp":            state.timestamp.isoformat(),
        "affect_coherence":     round(state.affect_coherence,   4),
        "stage_coherence":      round(state.stage_coherence,    4),
        "shadow_integration":   round(state.shadow_integration, 4),
        "schumann_alignment":   round(state.schumann_alignment, 4),
        "coherence":            round(state.coherence,          4),
        "coherence_band":       state.coherence_band.value,
        "dominant_emotion":     state.dominant_emotion,
        "active_stage":         state.active_stage,
        "active_archetype":     state.active_archetype,
        "schumann_disturbance": state.schumann_disturbance,
        "inner_narrative":      state.inner_narrative,
        "persona_tone":         state.persona_tone.value,
        "orb_params":           _serialise_orb(state.orb_params),
        "home_label":           state.coherence_band.value.replace(
                                    "_", " "
                                ).capitalize(),
    }
