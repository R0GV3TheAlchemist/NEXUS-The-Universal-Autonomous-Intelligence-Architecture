"""
schumann.router — FastAPI Router for Schumann Engine Endpoints

v0.1.0 endpoints:
  GET /schumann/health  — engine health probe
  GET /schumann/latest  — most recent Schumann reading

Reference: NEXUS_UNIVERSAL_OS.md Domain 1.6
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from schumann.engine import SchumannEngine

logger = logging.getLogger("schumann.router")
schumann_router = APIRouter(prefix="/schumann", tags=["schumann"],
                            responses={404: {"description": "Schumann endpoint not found"}})

_schumann_engine: SchumannEngine | None = None


def _get_engine() -> SchumannEngine:
    if _schumann_engine is None:
        raise RuntimeError("SchumannEngine not initialised.")
    return _schumann_engine


def init_schumann_engine(engine: SchumannEngine) -> None:
    global _schumann_engine
    _schumann_engine = engine
    logger.info("SchumannEngine router initialised.")


@schumann_router.get("/health")
async def schumann_health(engine: SchumannEngine = Depends(_get_engine)) -> JSONResponse:
    return JSONResponse(content={"engine": "schumann", "status": "online"})


@schumann_router.get("/latest")
async def schumann_latest(engine: SchumannEngine = Depends(_get_engine)) -> JSONResponse:
    reading = engine.latest
    if reading is None:
        return JSONResponse(content={"engine": "schumann", "reading": None,
                                      "note": "No reading available yet."})
    return JSONResponse(content={
        "engine": "schumann",
        "frequency_hz": reading.frequency_hz,
        "amplitude_pT": reading.amplitude_pT,
        "coherence": reading.coherence,
        "anomaly": reading.anomaly,
        "timestamp": reading.timestamp.isoformat(),
    })
