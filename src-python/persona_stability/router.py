"""
persona_stability.router — FastAPI Router for Persona Stability Endpoints

v0.1.0 endpoints:
  GET /persona/health   — engine health probe
  GET /persona/profile  — current persona stability profile

Reference: NEXUS_UNIVERSAL_OS.md Domain 2.5
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from persona_stability.engine import PersonaStabilityEngine

logger = logging.getLogger("persona_stability.router")
persona_router = APIRouter(prefix="/persona", tags=["persona"],
                           responses={404: {"description": "Persona endpoint not found"}})

_persona_engine: PersonaStabilityEngine | None = None


def _get_engine() -> PersonaStabilityEngine:
    if _persona_engine is None:
        raise RuntimeError("PersonaStabilityEngine not initialised.")
    return _persona_engine


def init_persona_engine(engine: PersonaStabilityEngine) -> None:
    global _persona_engine
    _persona_engine = engine
    logger.info("PersonaStabilityEngine router initialised.")


@persona_router.get("/health")
async def persona_health(engine: PersonaStabilityEngine = Depends(_get_engine)) -> JSONResponse:
    return JSONResponse(content={"engine": "persona-stability", "status": "online"})


@persona_router.get("/profile")
async def persona_profile(engine: PersonaStabilityEngine = Depends(_get_engine)) -> JSONResponse:
    p = engine.profile
    return JSONResponse(content={
        "engine": "persona-stability",
        "stability_score": p.stability_score,
        "coherence_index": p.coherence_index,
        "drift_velocity": p.drift_velocity,
        "dominant_persona": p.dominant_persona,
    })
