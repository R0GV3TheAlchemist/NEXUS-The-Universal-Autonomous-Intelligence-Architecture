"""
affect_engine.router — FastAPI Router for Affect Engine Endpoints

v0.1.0 endpoints:
  GET /affect/health   — engine health probe
  GET /affect/state    — current PAD affective state

Reference: NEXUS_UNIVERSAL_OS.md Domain 2.7
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from affect_engine.engine import AffectEngine

logger = logging.getLogger("affect_engine.router")
affect_router = APIRouter(prefix="/affect", tags=["affect"],
                          responses={404: {"description": "Affect endpoint not found"}})

_affect_engine: AffectEngine | None = None


def _get_engine() -> AffectEngine:
    if _affect_engine is None:
        raise RuntimeError("AffectEngine not initialised.")
    return _affect_engine


def init_affect_engine(engine: AffectEngine) -> None:
    global _affect_engine
    _affect_engine = engine
    logger.info("AffectEngine router initialised.")


@affect_router.get("/health")
async def affect_health(engine: AffectEngine = Depends(_get_engine)) -> JSONResponse:
    return JSONResponse(content={"engine": "affect", "status": "online"})


@affect_router.get("/state")
async def affect_state(engine: AffectEngine = Depends(_get_engine)) -> JSONResponse:
    s = engine.state
    return JSONResponse(content={
        "engine": "affect",
        "pleasure": s.pleasure, "arousal": s.arousal, "dominance": s.dominance
    })
