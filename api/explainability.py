"""Explainability API — /v1/governance/explain/

All endpoints require a bearer token (GAIA_EXPLAIN_TOKEN env var).
If GAIA_EXPLAIN_TOKEN is unset, all endpoints return 503.

Endpoints
---------
GET  /v1/governance/explain/report/{correlation_id}
     Full DecisionReport (plain-language + CoT + Canon citations)

GET  /v1/governance/explain/trace/{correlation_id}
     Raw TraceRecord export for a session

GET  /v1/governance/explain/citations/{correlation_id}
     Canon citations for a session, sorted by frequency

GET  /v1/governance/explain/counterfactual/{correlation_id}
     Counterfactual analysis: what changes if a Canon ref is absent?

GET  /v1/governance/explain/dashboard
     Gaian-facing summary of recent decision sessions
"""

from __future__ import annotations

import os
import secrets
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from core.governance.explainability import (
    DecisionExplainer,
)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_EXPLAIN_TOKEN: str = os.getenv("GAIA_EXPLAIN_TOKEN", "")
_bearer = HTTPBearer(auto_error=True)


def _require_token(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    if not _EXPLAIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GAIA_EXPLAIN_TOKEN is not configured.",
        )
    if not secrets.compare_digest(creds.credentials, _EXPLAIN_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid explainability token.",
        )
    return creds.credentials


# ---------------------------------------------------------------------------
# Shared explainer instance
# ---------------------------------------------------------------------------

_explainer = DecisionExplainer()


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------


class CanonCitationOut(BaseModel):
    ref: str
    trace_ids: list
    event_types: list
    frequency: int


class DecisionStepOut(BaseModel):
    trace_id: str
    event: str
    started_at: str
    latency_ms: Optional[float]
    canon_refs: list
    inputs_summary: str
    outputs_summary: str
    error: Optional[str]


class DecisionReportOut(BaseModel):
    session_id: str
    generated_at: str
    total_steps: int
    canon_citations: list[CanonCitationOut]
    chain_of_thought: list[DecisionStepOut]
    plain_language_summary: str
    error_count: int
    total_latency_ms: float


class CounterfactualOut(BaseModel):
    counterfactual_ref: str
    affected_steps: list
    affected_event_types: list
    impact_summary: str
    canon_dependency_depth: int


class DashboardEntryOut(BaseModel):
    session_id: str
    started_at: str
    step_count: int
    error_count: int
    top_canon_refs: list
    total_latency_ms: float
    plain_summary: str


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/v1/governance/explain", tags=["explainability"])


@router.get(
    "/report/{correlation_id}",
    response_model=DecisionReportOut,
    summary="Full decision report for a session",
    description=(
        "Returns a plain-language explanation of all reasoning steps taken "
        "in the session identified by correlation_id, including Canon citations "
        "and a full chain-of-thought trace."
    ),
)
def get_report(
    correlation_id: str,
    gaian_id: Optional[str] = Query(default=None),
    _token: str = Depends(_require_token),
) -> DecisionReportOut:
    report = _explainer.explain_session(
        correlation_id=correlation_id, gaian_id=gaian_id
    )
    return DecisionReportOut(**asdict(report))


@router.get(
    "/trace/{correlation_id}",
    summary="Raw CoT trace export for a session",
)
def export_trace(
    correlation_id: str,
    gaian_id: Optional[str] = Query(default=None),
    _token: str = Depends(_require_token),
) -> list:
    return _explainer.export_trace(
        correlation_id=correlation_id, gaian_id=gaian_id
    )


@router.get(
    "/citations/{correlation_id}",
    response_model=list[CanonCitationOut],
    summary="Canon citations for a session",
)
def get_citations(
    correlation_id: str,
    _token: str = Depends(_require_token),
) -> list[CanonCitationOut]:
    citations = _explainer.canon_citations_for_session(correlation_id)
    return [CanonCitationOut(**asdict(c)) for c in citations]


@router.get(
    "/counterfactual/{correlation_id}",
    response_model=CounterfactualOut,
    summary="Counterfactual: what changes if a Canon ref were absent?",
    description=(
        "Analyse the impact of removing a specific Canon passage from the "
        "session's reasoning. Identifies which steps relied on it and provides "
        "a plain-language impact summary."
    ),
)
def get_counterfactual(
    correlation_id: str,
    absent_ref: str = Query(
        ..., description="Canon reference to remove, e.g. C01"
    ),
    _token: str = Depends(_require_token),
) -> CounterfactualOut:
    result = _explainer.counterfactual(
        correlation_id=correlation_id,
        absent_canon_ref=absent_ref,
    )
    return CounterfactualOut(**asdict(result))


@router.get(
    "/dashboard",
    response_model=list[DashboardEntryOut],
    summary="Gaian-facing decision dashboard",
    description=(
        "Returns a list of recent decision sessions with plain-language "
        "summaries, Canon references, and performance metrics."
    ),
)
def get_dashboard(
    since: Optional[str] = Query(
        default=None,
        description="ISO-8601 timestamp; only sessions after this date are returned",
    ),
    gaian_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    _token: str = Depends(_require_token),
) -> list[DashboardEntryOut]:
    entries = _explainer.dashboard(
        since_iso=since, gaian_id=gaian_id, limit=limit
    )
    return [DashboardEntryOut(**asdict(e)) for e in entries]
