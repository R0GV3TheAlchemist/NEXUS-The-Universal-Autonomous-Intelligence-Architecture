"""
sovereign_memory.router — FastAPI Router for Sovereign Memory Endpoints

v0.1.0 endpoints:
  GET  /memory/health   — engine health probe
  GET  /memory/count    — total record count
  POST /memory/store    — store a new memory record (stub)

Reference: NEXUS_UNIVERSAL_OS.md Domain 2.6
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sovereign_memory.engine import SovereignMemory

logger = logging.getLogger("sovereign_memory.router")
memory_router = APIRouter(prefix="/memory", tags=["memory"],
                          responses={404: {"description": "Memory endpoint not found"}})

_memory_engine: SovereignMemory | None = None


def _get_engine() -> SovereignMemory:
    if _memory_engine is None:
        raise RuntimeError("SovereignMemory engine not initialised.")
    return _memory_engine


def init_memory(engine: SovereignMemory) -> None:
    global _memory_engine
    _memory_engine = engine
    logger.info("SovereignMemory router initialised.")


@memory_router.get("/health")
async def memory_health(engine: SovereignMemory = Depends(_get_engine)) -> JSONResponse:
    return JSONResponse(content={"engine": "sovereign-memory", "status": "online"})


@memory_router.get("/count")
async def memory_count(engine: SovereignMemory = Depends(_get_engine)) -> JSONResponse:
    return JSONResponse(content={"engine": "sovereign-memory", "record_count": engine.record_count})


@memory_router.post("/store")
async def memory_store(payload: dict, engine: SovereignMemory = Depends(_get_engine)) -> JSONResponse:
    return JSONResponse(content={"engine": "sovereign-memory",
                                  "note": "store not yet implemented.", "payload": payload})
