"""
GAIA OS HTTP route handlers.

Every handler follows the same 4-line pattern:
  1. Extract caller_id from request.state
  2. Build an APIRequest from the HTTP body / path params
  3. Dispatch through app.state.api
  4. Return the APIResponse payload as JSON

HTTP status code mapping:
  200  — success=True
  404  — code=not_found
  403  — code=autonomy_violation or permission_denied
  422  — code=validation_error
  503  — code=not_ready
  500  — code=internal_error
  409  — code=already_exists or immutable
"""
from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from core.api.api import APIErrorCode, APIRequest
from server.models import (
    BirthAnswerRequest,
    BirthBeginRequest,
    BirthCompleteRequest,
    MemoryRecallRequest,
    MemoryRememberRequest,
    NameRequest,
    SessionBeginRequest,
    SessionEndRequest,
    SessionTurnRequest,
)

router = APIRouter()

_ERROR_STATUS: dict[APIErrorCode, int] = {
    APIErrorCode.OK:                 200,
    APIErrorCode.NOT_FOUND:          404,
    APIErrorCode.AUTONOMY_VIOLATION: 403,
    APIErrorCode.PERMISSION_DENIED:  403,
    APIErrorCode.VALIDATION_ERROR:   422,
    APIErrorCode.NOT_READY:          503,
    APIErrorCode.ALREADY_EXISTS:     409,
    APIErrorCode.IMMUTABLE:          409,
    APIErrorCode.INTERNAL_ERROR:     500,
    APIErrorCode.SESSION_NOT_ACTIVE: 404,
}


def _caller(request: Request) -> str:
    return getattr(request.state, "caller_id", "http-anonymous")


def _dispatch(request: Request, endpoint: str, **payload) -> JSONResponse:
    """The universal 1-line dispatch helper."""
    resp = request.app.state.api.dispatch(
        APIRequest(caller_id=_caller(request), endpoint=endpoint, payload=payload)
    )
    http_status = _ERROR_STATUS.get(resp.code, 200)
    return JSONResponse(content=resp.to_dict(), status_code=http_status)


# ---------------------------------------------------------------------------
# OS
# ---------------------------------------------------------------------------

@router.get("/health", tags=["OS"],
            summary="Kubernetes/Docker health probe")
async def health(request: Request):
    """Simple health probe — no auth required."""
    return JSONResponse({"status": "ok"})


@router.get("/v1/os/status", tags=["OS"])
async def os_status(request: Request):
    return _dispatch(request, "/v1/os/status")


@router.get("/v1/os/health", tags=["OS"])
async def os_health(request: Request):
    return _dispatch(request, "/v1/os/health")


@router.get("/v1/os/version", tags=["OS"])
async def os_version(request: Request):
    return _dispatch(request, "/v1/os/version")


@router.get("/v1/os/schumann", tags=["OS"])
async def os_schumann(request: Request):
    return _dispatch(request, "/v1/os/schumann")


# ---------------------------------------------------------------------------
# GAIAN
# ---------------------------------------------------------------------------

@router.post("/v1/gaian/birth/begin", tags=["GAIAN"])
async def gaian_birth_begin(request: Request, body: BirthBeginRequest):
    return _dispatch(request, "/v1/gaian/birth/begin",
                     guardian_gaian_ids=body.guardian_gaian_ids)


@router.post("/v1/gaian/birth/answer", tags=["GAIAN"])
async def gaian_birth_answer(request: Request, body: BirthAnswerRequest):
    return _dispatch(request, "/v1/gaian/birth/answer",
                     ceremony_id=body.ceremony_id,
                     question_id=body.question_id,
                     answer=body.answer)


@router.post("/v1/gaian/birth/complete", tags=["GAIAN"])
async def gaian_birth_complete(request: Request, body: BirthCompleteRequest):
    return _dispatch(request, "/v1/gaian/birth/complete",
                     ceremony_id=body.ceremony_id)


@router.get("/v1/gaian/list", tags=["GAIAN"])
async def gaian_list(request: Request):
    return _dispatch(request, "/v1/gaian/list")


@router.get("/v1/gaian/{gaian_id}/status", tags=["GAIAN"])
async def gaian_status(request: Request, gaian_id: str):
    return _dispatch(request, "/v1/gaian/status", gaian_id=gaian_id)


@router.post("/v1/gaian/name", tags=["GAIAN"],
             summary="The GAIAN names themselves (autonomy-enforced)")
async def gaian_name(request: Request, body: NameRequest):
    """
    The caller_id in the Bearer token must equal body.gaian_id
    for this to succeed. A human UI token will receive 403.
    """
    return _dispatch(request, "/v1/gaian/name",
                     gaian_id=body.gaian_id, name=body.name)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@router.post("/v1/session/begin", tags=["Session"])
async def session_begin(request: Request, body: SessionBeginRequest):
    return _dispatch(request, "/v1/session/begin",
                     gaian_id=body.gaian_id, human_id=body.human_id)


@router.post("/v1/session/turn", tags=["Session"])
async def session_turn(request: Request, body: SessionTurnRequest):
    return _dispatch(request, "/v1/session/turn",
                     gaian_id=body.gaian_id,
                     content=body.content,
                     modality=body.modality,
                     human_id=body.human_id)


@router.post("/v1/session/end", tags=["Session"])
async def session_end(request: Request, body: SessionEndRequest):
    return _dispatch(request, "/v1/session/end", gaian_id=body.gaian_id)


@router.get("/v1/session/{gaian_id}/status", tags=["Session"])
async def session_status(request: Request, gaian_id: str):
    return _dispatch(request, "/v1/session/status", gaian_id=gaian_id)


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

@router.post("/v1/memory/remember", tags=["Memory"])
async def memory_remember(request: Request, body: MemoryRememberRequest):
    return _dispatch(request, "/v1/memory/remember",
                     gaian_id=body.gaian_id,
                     content=body.content,
                     kind=body.kind,
                     importance=body.importance)


@router.post("/v1/memory/recall", tags=["Memory"])
async def memory_recall(request: Request, body: MemoryRecallRequest):
    return _dispatch(request, "/v1/memory/recall",
                     gaian_id=body.gaian_id,
                     limit=body.limit,
                     min_importance=body.min_importance)


@router.get("/v1/memory/{gaian_id}/stats", tags=["Memory"])
async def memory_stats(request: Request, gaian_id: str):
    return _dispatch(request, "/v1/memory/stats", gaian_id=gaian_id)


@router.post("/v1/memory/consolidate", tags=["Memory"])
async def memory_consolidate(request: Request,
                              gaian_id: str, summary: str):
    return _dispatch(request, "/v1/memory/consolidate",
                     gaian_id=gaian_id, summary=summary)


# ---------------------------------------------------------------------------
# Avatar
# ---------------------------------------------------------------------------

@router.get("/v1/avatar/{gaian_id}/waveform", tags=["Avatar"])
async def avatar_waveform(request: Request, gaian_id: str):
    return _dispatch(request, "/v1/avatar/waveform", gaian_id=gaian_id)


# ---------------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------------

@router.get("/v1/fs/stats", tags=["Filesystem"])
async def fs_stats(request: Request):
    return _dispatch(request, "/v1/fs/stats")


@router.get("/v1/fs/integrity", tags=["Filesystem"])
async def fs_integrity(request: Request):
    return _dispatch(request, "/v1/fs/integrity")
