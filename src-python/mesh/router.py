"""
mesh.router — FastAPI Router for GAIAN Mesh Network Endpoints

v0.1.0 endpoints:
  GET  /mesh/health  — mesh router health probe
  GET  /mesh/peers   — list known mesh peers
  POST /mesh/send    — send a message to a mesh peer

Reference: NEXUS_UNIVERSAL_OS.md Domain 1.5
GAIAN law: GAIAN_LAWS.md Law IV — Mesh Sovereignty
"""
from __future__ import annotations

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger("mesh.router")
mesh_router = APIRouter(prefix="/mesh", tags=["mesh"],
                        responses={404: {"description": "Mesh endpoint not found"}})

_mesh_initialized: bool = False


def init_mesh_router() -> None:
    """Initialise the GAIAN mesh router.

    Called once from src-python/main.py during application startup.
    In v0.1.0, performs no actual hardware initialisation.
    """
    global _mesh_initialized
    _mesh_initialized = True
    logger.info("Mesh router initialised.")


@mesh_router.get("/health")
async def mesh_health() -> JSONResponse:
    return JSONResponse(content={"engine": "mesh", "initialized": _mesh_initialized})


@mesh_router.get("/peers")
async def mesh_peers() -> JSONResponse:
    return JSONResponse(content={"engine": "mesh", "peers": [],
                                  "note": "Peer discovery not yet implemented."})


@mesh_router.post("/send")
async def mesh_send(payload: dict) -> JSONResponse:
    return JSONResponse(content={"engine": "mesh",
                                  "note": "Mesh send not yet implemented.",
                                  "payload": payload})
