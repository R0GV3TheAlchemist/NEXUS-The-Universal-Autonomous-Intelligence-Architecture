"""Canon Governance API — /v1/governance/canon/

Exposes CanonStore and CanonDiffer over HTTP.
All write endpoints require GAIA_CANON_WRITE_TOKEN.
All read endpoints require GAIA_CANON_READ_TOKEN (falls back to write token).

Endpoints
---------
GET  /v1/governance/canon/                     List all active entries
GET  /v1/governance/canon/version              Current version + snapshot list
GET  /v1/governance/canon/snapshot/{version}   Load a historical snapshot
GET  /v1/governance/canon/diff                 Diff two versions
GET  /v1/governance/canon/diff/live            Live vs snapshot diff
GET  /v1/governance/canon/{entry_id}           Get a single entry
GET  /v1/governance/canon/search               Full-text search
GET  /v1/governance/canon/conflicts            Conflict detection scan
GET  /v1/governance/canon/export               Regulatory export
GET  /v1/governance/canon/amendments           List amendments
POST /v1/governance/canon/amendments           Propose an amendment
PATCH /v1/governance/canon/amendments/{id}/approve   Approve
PATCH /v1/governance/canon/amendments/{id}/reject    Reject
"""

from __future__ import annotations

import os
import secrets
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from core.canon_store import CanonStore
from core.governance.canon_diff import CanonDiffer

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_WRITE_TOKEN: str = os.getenv("GAIA_CANON_WRITE_TOKEN", "")
_READ_TOKEN: str = os.getenv("GAIA_CANON_READ_TOKEN", "") or _WRITE_TOKEN
_bearer = HTTPBearer(auto_error=True)


def _require_read(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    if not _READ_TOKEN:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="GAIA_CANON_READ_TOKEN not configured.")
    if not secrets.compare_digest(creds.credentials, _READ_TOKEN):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    return creds.credentials


def _require_write(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    if not _WRITE_TOKEN:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="GAIA_CANON_WRITE_TOKEN not configured.")
    if not secrets.compare_digest(creds.credentials, _WRITE_TOKEN):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    return creds.credentials


# ---------------------------------------------------------------------------
# Shared instances
# ---------------------------------------------------------------------------

_store = CanonStore()
_differ = CanonDiffer(_store)

# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class ProposeAmendmentRequest(BaseModel):
    action: str                     # "add" | "update" | "remove"
    entry_id: str
    proposed_by: str
    justification: str
    new_body: Optional[str] = None
    new_title: Optional[str] = None
    tags: Optional[list[str]] = None


class ApproveAmendmentRequest(BaseModel):
    reviewed_by: str
    new_title: Optional[str] = None
    tags: Optional[list[str]] = None


class RejectAmendmentRequest(BaseModel):
    reviewed_by: str


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/v1/governance/canon", tags=["canon-governance"])


@router.get("/", summary="List all active Canon entries")
def list_entries(_token: str = Depends(_require_read)) -> list:
    return [e.to_dict() for e in _store.all_entries()]


@router.get("/version", summary="Current Canon version and available snapshots")
def get_version(_token: str = Depends(_require_read)) -> dict:
    return {
        "version": _store.version,
        "snapshots": _store.list_snapshots(),
    }


@router.get("/search", summary="Full-text search over Canon entries")
def search_entries(
    q: str = Query(..., description="Search query"),
    _token: str = Depends(_require_read),
) -> list:
    return [e.to_dict() for e in _store.search(q)]


@router.get("/snapshot/{version}", summary="Load a historical Canon snapshot")
def get_snapshot(
    version: str,
    _token: str = Depends(_require_read),
) -> dict:
    try:
        return _store.load_snapshot(version)
    except FileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/diff", summary="Diff two historical Canon versions")
def diff_versions(
    version_a: str = Query(...),
    version_b: str = Query(...),
    _token: str = Depends(_require_read),
) -> dict:
    try:
        report = _differ.diff_versions(version_a, version_b)
        return report.to_dict()
    except FileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/diff/live", summary="Diff live Canon against a historical snapshot")
def diff_live(
    snapshot_version: str = Query(...),
    _token: str = Depends(_require_read),
) -> dict:
    try:
        report = _differ.diff_live_vs_snapshot(snapshot_version)
        return report.to_dict()
    except FileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/conflicts", summary="Run conflict detection across the active Canon")
def detect_conflicts(_token: str = Depends(_require_read)) -> list:
    return [c.to_dict() for c in _store.detect_conflicts()]


@router.get("/export", summary="Regulatory export of the active Canon")
def regulatory_export(_token: str = Depends(_require_read)) -> dict:
    return _store.regulatory_export()


@router.get("/amendments", summary="List all amendments")
def list_amendments(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    _token: str = Depends(_require_read),
) -> list:
    amds = _store._amendments
    if status_filter:
        amds = [a for a in amds if a.status == status_filter]
    return [a.to_dict() for a in amds]


@router.post("/amendments", summary="Propose a Canon amendment",
             status_code=status.HTTP_201_CREATED)
def propose_amendment(
    req: ProposeAmendmentRequest,
    _token: str = Depends(_require_write),
) -> dict:
    try:
        amd = _store.propose_amendment(
            action=req.action,
            entry_id=req.entry_id,
            proposed_by=req.proposed_by,
            justification=req.justification,
            new_body=req.new_body,
            new_title=req.new_title,
            tags=req.tags,
        )
        return amd.to_dict()
    except (ValueError, KeyError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(exc)) from exc


@router.patch("/amendments/{amendment_id}/approve",
              summary="Approve a pending Canon amendment")
def approve_amendment(
    amendment_id: str,
    req: ApproveAmendmentRequest,
    _token: str = Depends(_require_write),
) -> dict:
    try:
        entry = _store.approve_amendment(
            amendment_id=amendment_id,
            reviewed_by=req.reviewed_by,
            new_title=req.new_title,
            tags=req.tags,
        )
        return entry.to_dict() if entry else {"status": "removed"}
    except (ValueError, KeyError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(exc)) from exc


@router.patch("/amendments/{amendment_id}/reject",
              summary="Reject a pending Canon amendment")
def reject_amendment(
    amendment_id: str,
    req: RejectAmendmentRequest,
    _token: str = Depends(_require_write),
) -> dict:
    try:
        amd = _store.reject_amendment(
            amendment_id=amendment_id,
            reviewed_by=req.reviewed_by,
        )
        return amd.to_dict()
    except (ValueError, KeyError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(exc)) from exc


@router.get("/{entry_id}", summary="Get a single Canon entry by ID")
def get_entry(
    entry_id: str,
    _token: str = Depends(_require_read),
) -> dict:
    entry = _store.get(entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail=f"Canon entry {entry_id!r} not found.")
    return entry.to_dict()
