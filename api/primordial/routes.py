"""
api/primordial/routes.py
========================
FastAPI router for the primordial simulation engine.

Endpoints:
  POST /primordial/simulate   — run a single simulation
  POST /primordial/recover    — run a recovery simulation
  GET  /primordial/archetypes — run and return all five archetypes
  GET  /primordial/canon      — return canon log summary
  GET  /primordial/canon/entries — return recent canon entries
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from core.primordial.archetypes import run_all_archetypes
from core.primordial.canon_log import append_to_canon, canon_summary, read_canon
from core.primordial.entity import PrimordialEntity
from core.primordial.recovery import Intervention, InterventionType, RecoverySimulation
from core.primordial.simulation import PrimordialSimulation

from .schemas import (
    ArchetypeResponse,
    CanonSummaryResponse,
    RecoverRequest,
    RecoverResponse,
    SimulateRequest,
    SimulateResponse,
)

router = APIRouter(prefix="/primordial", tags=["primordial"])


# ---------------------------------------------------------------------------
# POST /primordial/simulate
# ---------------------------------------------------------------------------

@router.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest) -> dict[str, Any]:
    """Run a single primordial simulation."""
    entity = PrimordialEntity(
        name=req.name,
        love=req.love,
        life=req.life,
        integrity=req.integrity,
        hope=req.hope,
        truth=req.truth,
        burden=req.burden,
    )
    outcome = PrimordialSimulation().run(entity)
    result  = outcome.to_dict()
    result["run_at"] = datetime.now(timezone.utc).isoformat()

    if req.save_to_canon:
        append_to_canon(result)

    return result


# ---------------------------------------------------------------------------
# POST /primordial/recover
# ---------------------------------------------------------------------------

@router.post("/recover", response_model=RecoverResponse)
def recover(req: RecoverRequest) -> dict[str, Any]:
    """Run a recovery simulation with optional interventions."""
    valid_types = {t.value for t in InterventionType}
    for iv in req.interventions:
        if iv.intervention_type not in valid_types:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid intervention_type '{iv.intervention_type}'. "
                       f"Must be one of: {sorted(valid_types)}",
            )

    entity = PrimordialEntity(
        name=req.name,
        love=req.love,
        life=req.life,
        integrity=req.integrity,
        hope=req.hope,
        truth=req.truth,
        burden=req.burden,
    )
    interventions = [
        Intervention(
            intervention_type=InterventionType(iv.intervention_type),
            intensity=iv.intensity,
        )
        for iv in req.interventions
    ]
    outcome = RecoverySimulation().run(entity, interventions)
    result  = outcome.to_dict()
    result["run_at"] = datetime.now(timezone.utc).isoformat()

    if req.save_to_canon:
        append_to_canon({"type": "recovery", **result})

    return result


# ---------------------------------------------------------------------------
# GET /primordial/archetypes
# ---------------------------------------------------------------------------

@router.get("/archetypes", response_model=list[ArchetypeResponse])
def archetypes() -> list[dict[str, Any]]:
    """Run and return all five primordial archetypes."""
    results = run_all_archetypes()
    return [r.to_dict() for r in results]


# ---------------------------------------------------------------------------
# GET /primordial/canon
# ---------------------------------------------------------------------------

@router.get("/canon", response_model=CanonSummaryResponse)
def canon() -> dict[str, Any]:
    """Return aggregate statistics from the canon log."""
    summary = canon_summary()
    if summary.get("total", 0) == 0:
        return {
            "total": 0, "survived": 0, "collapsed": 0,
            "survival_rate": 0.0, "avg_emergent_order": 0.0,
            "top_insights": [],
        }
    return summary


# ---------------------------------------------------------------------------
# GET /primordial/canon/entries
# ---------------------------------------------------------------------------

@router.get("/canon/entries")
def canon_entries(
    limit: int = Query(default=20, ge=1, le=200),
) -> list[dict[str, Any]]:
    """Return the most recent N entries from the canon log."""
    return read_canon(limit=limit)
