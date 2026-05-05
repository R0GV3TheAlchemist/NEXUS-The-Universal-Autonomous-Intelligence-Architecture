"""
FastAPI router for the Affect Engine  (Issue #65)

Mount in main.py::

    from affect_engine.router import affect_router, init_affect_engine
    app.include_router(affect_router, prefix="/affect")

Endpoints
---------
GET  /affect/health              — liveness probe
POST /affect/analyze             — run affect inference on a text block
GET  /affect/history/{principal} — last N days of AffectSnapshots
GET  /affect/trend/{principal}   — ArcTrend for last 30 days
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .nlp_backend import build_backend, AffectBackend
from .arc_trend import compute_arc_trend

logger = logging.getLogger(__name__)

affect_router = APIRouter(tags=["affect_engine"])

_engine  = None   # AffectEngine singleton
_backend: AffectBackend | None = None


def init_affect_engine(engine, backend_name: str = "heuristic") -> None:
    """Call from app lifespan with fully initialised instances."""
    global _engine, _backend
    _engine  = engine
    _backend = build_backend(backend_name)
    logger.info("AffectEngine router initialised (backend=%s)", _backend.name)


class AnalyzeRequest(BaseModel):
    principal_id : str
    text         : str
    source       : str = "gaia_chat"   # journal | gaia_chat | system
    persist      : bool = True
    backend      : Optional[str] = None  # override per-request


@affect_router.get("/health")
async def health() -> JSONResponse:
    ok = _engine is not None
    return JSONResponse(status_code=200 if ok else 503, content={"ok": ok})


@affect_router.post("/analyze")
async def analyze(req: AnalyzeRequest) -> JSONResponse:
    """Run affect inference and optionally persist the snapshot."""
    if _engine is None:
        raise HTTPException(503, "Affect engine not initialised")
    backend = build_backend(req.backend) if req.backend else _backend
    # Override the engine’s internal heuristic call with the chosen backend
    result = backend.analyze(req.text)
    snapshot = _engine.analyze_text(
        principal_id=req.principal_id,
        text=req.text,
        source=req.source,
        persist=req.persist,
    )
    payload = snapshot.to_dict()
    payload["backend"] = backend.name
    payload["nlp_result"] = result.to_dict()
    return JSONResponse(content=payload)


@affect_router.get("/history/{principal_id}")
async def get_history(principal_id: str, days: int = 30) -> JSONResponse:
    """Return raw AffectSnapshot history from SovereignMemory."""
    if _engine is None:
        raise HTTPException(503, "Affect engine not initialised")
    history = _engine.get_affect_history(principal_id, days)
    return JSONResponse(content={
        k: [s.value if hasattr(s, "value") else s for s in v]
        for k, v in history.items()
    })


@affect_router.get("/trend/{principal_id}")
async def get_trend(principal_id: str, days: int = 30) -> JSONResponse:
    """Return ArcTrend (valence trend, momentum, volatility, etc.)."""
    if _engine is None:
        raise HTTPException(503, "Affect engine not initialised")
    history = _engine.get_affect_history(principal_id, days)

    def _vals(key: str) -> list[float]:
        return [s.value if hasattr(s, "value") else float(s) for s in history.get(key, [])]

    # Emotion labels aren’t stored in biometric history — use neutral as placeholder
    # until SovereignMemory exposes a labelled snapshot query.
    valence   = _vals("valence")
    arousal   = _vals("arousal")
    n_labels  = len(valence)
    labels    = ["neutral"] * n_labels  # TODO: fetch real labels from snapshot table

    trend = compute_arc_trend(valence, arousal, labels)
    return JSONResponse(content=trend.to_dict())
