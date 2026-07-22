"""
crystal.router — FastAPI Router for Crystal Engine Endpoints

v0.1.0 endpoints:
  GET /crystal/health   — engine health probe
  GET /crystal/lattice  — current lattice node count & parameters

Reference: NEXUS_UNIVERSAL_OS.md Domain 3.1
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from crystal.engine import CrystalCore

logger = logging.getLogger("crystal.router")
crystal_router = APIRouter(prefix="/crystal", tags=["crystal"],
                           responses={404: {"description": "Crystal endpoint not found"}})

_crystal_core: CrystalCore | None = None


def _get_engine() -> CrystalCore:
    if _crystal_core is None:
        raise RuntimeError("CrystalCore not initialised.")
    return _crystal_core


def init_crystal_core(engine: CrystalCore) -> None:
    global _crystal_core
    _crystal_core = engine
    logger.info("CrystalCore router initialised.")


@crystal_router.get("/health")
async def crystal_health(engine: CrystalCore = Depends(_get_engine)) -> JSONResponse:
    return JSONResponse(content={"engine": "crystal", "status": "online"})


@crystal_router.get("/lattice")
async def crystal_lattice(engine: CrystalCore = Depends(_get_engine)) -> JSONResponse:
    lat = engine.lattice
    return JSONResponse(content={
        "engine": "crystal",
        "node_count": len(lat.nodes),
        "lattice_a": lat.lattice_a,
        "lattice_b": lat.lattice_b,
        "lattice_c": lat.lattice_c,
        "space_group": lat.space_group,
    })
