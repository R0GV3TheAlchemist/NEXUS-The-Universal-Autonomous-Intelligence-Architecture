"""
shadow_engine.router — FastAPI Router for Shadow Engine Endpoints

v0.1.0 endpoints:
  GET /shadow/health  — engine health probe
  GET /shadow/state   — current shadow load state

Reference: NEXUS_UNIVERSAL_OS.md Domain 2.9
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from shadow_engine.engine import ShadowEngine

logger = logging.getLogger("shadow_engine.router")
shadow_router = APIRouter(prefix="/shadow", tags=["shadow"],
                          responses={404: {"description": "Shadow endpoint not found"}})

_shadow_engine: ShadowEngine | None = None


def _get_engine() -> ShadowEngine:
    if _shadow_engine is None:
        raise RuntimeError("ShadowEngine not initialised.")
    return _shadow_engine


def init_shadow_router(engine: ShadowEngine) -> None:
    global _shadow_engine
    _shadow_engine = engine
    logger.info("ShadowEngine router initialised.")


@shadow_router.get("/health")
async def shadow_health(engine: ShadowEngine = Depends(_get_engine)) -> JSONResponse:
    return JSONResponse(content={"engine": "shadow", "status": "online"})


@shadow_router.get("/state")
async def shadow_state(engine: ShadowEngine = Depends(_get_engine)) -> JSONResponse:
    s = engine.state
    return JSONResponse(content={
        "engine": "shadow",
        "total_load": s.total_load,
        "dominant_theme": s.dominant_theme,
        "integration_score": s.integration_score,
    })
