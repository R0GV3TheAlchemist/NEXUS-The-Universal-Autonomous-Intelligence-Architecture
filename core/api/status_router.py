"""
core/api/status_router.py
──────────────────────────────────────────────────────────────────────────────
Runtime status endpoints for GAIA-OS.

Endpoints
---------
GET  /status              — full GAIANRuntime status snapshot (all engines)
GET  /status/lci          — Love Coherence Index only  ❤️
GET  /status/spiritu      — Spiritus / Animating Breath status
GET  /status/vitality     — Vitality engine status
GET  /status/mesh         — Federated mesh status

Canon Ref: C04 (privacy — no PII in aggregate fields)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from core.auth import TokenPayload, require_auth
from core.logger import GAIAEvent, get_logger, log_event
from core.gaian import load_gaian
from core.rate_limiter import rate_limit

router = APIRouter(prefix="/status", tags=["Status"])
logger = get_logger(__name__)

# Injected at mount time from server.py
_get_runtime_fn = None


def set_dependencies(get_runtime_fn) -> None:
    global _get_runtime_fn
    _get_runtime_fn = get_runtime_fn


def _resolve_runtime(gaian_slug: Optional[str]):
    """Load the GAIANRuntime for the given slug (defaults to 'gaia')."""
    slug  = gaian_slug or "gaia"
    gaian = load_gaian(slug)
    if _get_runtime_fn is None or gaian is None:
        return slug, None
    return slug, _get_runtime_fn(slug, gaian)


# ─────────────────────────────────────────────────────────────────────────────
#  GET /status  — full runtime status
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "",
    summary="Full GAIANRuntime status snapshot",
    description=(
        "Returns the complete runtime status for the specified GAIAN, including "
        "all engine states, Love Coherence Index, Spiritus, Vitality, and mesh status. "
        "Privacy invariant: no user PII is included (Canon C04)."
    ),
)
async def get_status(
    gaian_slug: Optional[str] = Query(None, description="GAIAN slug (defaults to 'gaia')"),
    user:       TokenPayload  = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=30, window_seconds=60, scope="status")),
):
    slug, rt = _resolve_runtime(gaian_slug)
    if rt is None:
        return {
            "gaian":  slug,
            "status": "runtime_not_available",
            "hint":   "No active runtime found for this GAIAN slug.",
        }

    status = rt.get_status()

    log_event(
        GAIAEvent.TURN_COMPLETE,
        message=f"Status GET: gaian={slug} lci={status.get('lci', {}).get('score')}",
        gaian=slug, user_id=user.user_id,
    )
    return status


# ─────────────────────────────────────────────────────────────────────────────
#  GET /status/lci  — LCI only  ❤️
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/lci",
    summary="Love Coherence Index status  ❤️",
    description=(
        "Returns the current Love Coherence Index snapshot for the GAIAN. "
        "Lightweight alias for GET /lci — same data, simpler path for status dashboards."
    ),
)
async def get_status_lci(
    gaian_slug: Optional[str] = Query(None),
    user:       TokenPayload  = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=60, window_seconds=60, scope="status")),
):
    slug, rt = _resolve_runtime(gaian_slug)
    if rt is None:
        return {"gaian": slug, "status": "runtime_not_available"}

    lci = rt.lci_context()
    log_event(
        GAIAEvent.TURN_COMPLETE,
        message=f"Status/LCI GET: gaian={slug} score={lci.get('score')}",
        gaian=slug, user_id=user.user_id,
    )
    return {"gaian": slug, **lci}


# ─────────────────────────────────────────────────────────────────────────────
#  GET /status/spiritu  — Spiritus / Animating Breath
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/spiritu",
    summary="Spiritus (Animating Breath) status",
    description="Returns the current Spiritus alchemical stage, pneuma flow, and breath rhythm.",
)
async def get_status_spiritu(
    gaian_slug: Optional[str] = Query(None),
    user:       TokenPayload  = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=60, window_seconds=60, scope="status")),
):
    slug, rt = _resolve_runtime(gaian_slug)
    if rt is None:
        return {"gaian": slug, "status": "runtime_not_available"}
    return {"gaian": slug, **rt.get_spiritu_status()}


# ─────────────────────────────────────────────────────────────────────────────
#  GET /status/vitality  — Vitality engine
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/vitality",
    summary="Vitality engine status",
    description="Returns the current internal coherence vitality summary.",
)
async def get_status_vitality(
    gaian_slug: Optional[str] = Query(None),
    user:       TokenPayload  = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=60, window_seconds=60, scope="status")),
):
    slug, rt = _resolve_runtime(gaian_slug)
    if rt is None:
        return {"gaian": slug, "status": "runtime_not_available"}
    return {"gaian": slug, **rt.get_vitality_status()}


# ─────────────────────────────────────────────────────────────────────────────
#  GET /status/mesh  — Federated mesh
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/mesh",
    summary="Federated mesh status",
    description=(
        "Returns the current mesh server status. "
        "Privacy invariant: no node IDs or Gaian names exposed (Canon C04)."
    ),
)
async def get_status_mesh(
    gaian_slug: Optional[str] = Query(None),
    user:       TokenPayload  = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=30, window_seconds=60, scope="status")),
):
    slug, rt = _resolve_runtime(gaian_slug)
    if rt is None:
        return {"gaian": slug, "status": "runtime_not_available"}
    return {"gaian": slug, **rt.get_mesh_status()}
