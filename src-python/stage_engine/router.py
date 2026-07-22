"""
stage_engine.router — FastAPI Router for Stage Engine Endpoints

v0.1.0 endpoints:
  GET /stage/health  — engine health probe
  GET /stage/state   — current stage state

Reference: NEXUS_UNIVERSAL_OS.md Domain 2.8
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from stage_engine.engine import StageEngine

logger = logging.getLogger("stage_engine.router")
stage_router = APIRouter(prefix="/stage", tags=["stage"],
                         responses={404: {"description": "Stage endpoint not found"}})

_stage_engine: StageEngine | None = None


def _get_engine() -> StageEngine:
    if _stage_engine is None:
        raise RuntimeError("StageEngine not initialised.")
    return _stage_engine


def init_stage_engine(engine: StageEngine) -> None:
    global _stage_engine
    _stage_engine = engine
    logger.info("StageEngine router initialised.")


@stage_router.get("/health")
async def stage_health(engine: StageEngine = Depends(_get_engine)) -> JSONResponse:
    return JSONResponse(content={"engine": "stage", "status": "online"})


@stage_router.get("/state")
async def stage_state(engine: StageEngine = Depends(_get_engine)) -> JSONResponse:
    s = engine.state
    return JSONResponse(content={
        "engine": "stage",
        "current_stage": s.current_stage.name,
        "progress": s.progress,
        "cycles": s.cycles,
    })
