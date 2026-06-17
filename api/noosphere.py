"""
api/noosphere.py
Canon: C48 (GAIA_Autopoiesis_Doctrine), C50 (Prism_Cube_Doctrine)

FastAPI router: /noosphere/*

Exposes the core noosphere layer — the collective signal field that GAIA
taps into when reasoning about planetary coherence, shared consciousness,
and emergent collective intelligence.

Routes:
  GET  /noosphere/state              — current field state and coherence index
  POST /noosphere/pulse              — inject a signal pulse into the field
  GET  /noosphere/field              — full field topology snapshot
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.noosphere import Noosphere

# ─── Router ───────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/noosphere", tags=["noosphere"])

# Runtime singleton
_noosphere = Noosphere()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Pydantic models ──────────────────────────────────────────────────────────

class NoosphereStateResponse(BaseModel):
    coherence_index: float = Field(..., ge=0.0, le=1.0)
    field_density: float = Field(..., ge=0.0)
    active_nodes: int
    schumann_alignment: float
    apex_protocol_active: bool
    timestamp: str


class PulseRequest(BaseModel):
    source_id: str
    signal_type: str = "resonance"  # resonance | disruption | coherence | intention
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    payload: Optional[dict] = None


class PulseResponse(BaseModel):
    pulse_id: str
    accepted: bool
    field_delta: float
    new_coherence: float
    timestamp: str


class FieldTopologyResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]
    global_coherence: float
    dominant_frequency: Optional[float]
    timestamp: str


# ─── GET /noosphere/state ─────────────────────────────────────────────────────

@router.get("/state", response_model=NoosphereStateResponse)
async def get_noosphere_state() -> NoosphereStateResponse:
    """Return the current noosphere field state and coherence index."""
    try:
        state = _noosphere.get_state()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Noosphere state error: {exc}") from exc

    return NoosphereStateResponse(
        coherence_index=state.get("coherence_index", 0.0),
        field_density=state.get("field_density", 0.0),
        active_nodes=state.get("active_nodes", 0),
        schumann_alignment=state.get("schumann_alignment", 0.0),
        apex_protocol_active=state.get("apex_protocol_active", False),
        timestamp=_now(),
    )


# ─── POST /noosphere/pulse ────────────────────────────────────────────────────

@router.post("/pulse", response_model=PulseResponse)
async def inject_pulse(req: PulseRequest) -> PulseResponse:
    """Inject a signal pulse into the noosphere field."""
    import uuid
    pulse_id = f"pulse_{uuid.uuid4().hex[:8]}"

    try:
        result = _noosphere.inject_pulse(
            source_id=req.source_id,
            signal_type=req.signal_type,
            intensity=req.intensity,
            payload=req.payload or {},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pulse injection failed: {exc}") from exc

    return PulseResponse(
        pulse_id=pulse_id,
        accepted=result.get("accepted", True),
        field_delta=result.get("field_delta", 0.0),
        new_coherence=result.get("new_coherence", 0.0),
        timestamp=_now(),
    )


# ─── GET /noosphere/field ─────────────────────────────────────────────────────

@router.get("/field", response_model=FieldTopologyResponse)
async def get_field_topology() -> FieldTopologyResponse:
    """Return full field topology — nodes, edges, dominant frequency."""
    try:
        topology = _noosphere.get_field_topology()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Field topology error: {exc}") from exc

    return FieldTopologyResponse(
        nodes=topology.get("nodes", []),
        edges=topology.get("edges", []),
        global_coherence=topology.get("global_coherence", 0.0),
        dominant_frequency=topology.get("dominant_frequency"),
        timestamp=_now(),
    )
