"""
FastAPI router — exposes SchumannEngine state via HTTP + WebSocket.

Mount this router in main.py::

    from schumann.router import schumann_router
    app.include_router(schumann_router, prefix="/schumann")

Endpoints
---------
GET  /schumann/state          — current SchumannState as JSON
GET  /schumann/health         — liveness probe
WS   /schumann/stream         — WebSocket; emits JSON state every N seconds
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .engine import EngineConfig, SchumannEngine
from .models import SchumannState

logger = logging.getLogger(__name__)

schumann_router = APIRouter(tags=["schumann"])

# Module-level singleton; call init_engine() from app lifespan.
_engine: Optional[SchumannEngine] = None


# ---------------------------------------------------------------------------
# Lifecycle helpers  (called from app startup / shutdown)
# ---------------------------------------------------------------------------

async def init_engine(config: Optional[EngineConfig] = None) -> None:
    """Initialise and start the global SchumannEngine."""
    global _engine
    cfg     = config or EngineConfig()
    _engine = SchumannEngine(cfg)
    await _engine.start()
    logger.info("SchumannEngine initialised via router.")


async def shutdown_engine() -> None:
    global _engine
    if _engine:
        await _engine.stop()
        _engine = None


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@schumann_router.get("/state")
async def get_state() -> JSONResponse:
    """
    Return the latest SchumannState snapshot.

    Returns 503 if the engine has no state yet (still warming up).
    """
    if _engine is None:
        return JSONResponse(status_code=503, content={"error": "engine not started"})
    state = await _engine.tick()
    return JSONResponse(content=_state_to_dict(state))


@schumann_router.get("/health")
async def health() -> JSONResponse:
    ok = _engine is not None
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"ok": ok, "source": _engine.config.source if ok else None},
    )


# ---------------------------------------------------------------------------
# WebSocket stream
# ---------------------------------------------------------------------------

@schumann_router.websocket("/stream")
async def ws_stream(websocket: WebSocket) -> None:
    """
    WebSocket endpoint — pushes SchumannState JSON every 5 seconds.

    Clients can simply connect and read; no messages need to be sent.
    The connection is closed gracefully if the engine shuts down.
    """
    await websocket.accept()
    logger.info("WebSocket client connected to /schumann/stream")
    try:
        while True:
            if _engine is None:
                await websocket.send_json({"error": "engine not running"})
                await asyncio.sleep(5)
                continue
            state = await _engine.tick()
            await websocket.send_json(_state_to_dict(state))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from /schumann/stream")
    except Exception:
        logger.exception("WebSocket /schumann/stream error")


# ---------------------------------------------------------------------------
# Serialisation helper
# ---------------------------------------------------------------------------

def _state_to_dict(state: SchumannState) -> dict:
    return {
        "timestamp"            : state.timestamp.isoformat(),
        "fundamental_hz"       : round(state.fundamental_hz, 4),
        "harmonic_power"       : {k: round(v, 4) for k, v in state.harmonic_power.items()},
        "geomagnetic_activity" : round(state.geomagnetic_activity, 4),
        "signal_quality"       : round(state.signal_quality, 4),
        "disturbance_level"    : state.disturbance_level.value,
        "alignment_score"      : round(state.alignment_score, 4),
        "confidence"           : round(state.confidence, 4),
        "is_trusted"           : state.is_trusted,
        "source_ids"           : state.source_ids,
        "baseline_hz"          : round(state.baseline_hz, 4),
        "deviation_sigma"      : round(state.deviation_sigma, 4),
        "experimental_flags"   : state.experimental_flags,
    }
