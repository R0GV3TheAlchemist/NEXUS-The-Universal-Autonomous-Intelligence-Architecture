"""
FastAPI router for the Stage Engine  (Issue #63)

Mount in main.py::

    from stage_engine.router import stage_router, init_stage_engine
    app.include_router(stage_router, prefix="/stage")

Endpoints
---------
GET  /stage/record/{principal_id}   — current StageRecord as JSON
GET  /stage/history/{principal_id}  — list of past StageTransitions
POST /stage/evaluate                — run a full evaluation tick
GET  /stage/health                  — liveness probe
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

stage_router = APIRouter(tags=["stage_engine"])

_engine   = None   # StageEngine singleton
_tracker  = None   # WindowTracker singleton
_memory   = None   # SovereignMemory singleton


def init_stage_engine(memory, engine, tracker) -> None:
    """Call from app lifespan with fully initialised instances."""
    global _engine, _tracker, _memory
    _engine  = engine
    _tracker = tracker
    _memory  = memory
    logger.info("StageEngine router initialised.")


# ─────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    principal_id             : str
    goal_states              : list[str]   = []
    hrv_rmssd_history        : list[float] = []
    alignment_score_history  : list[float] = []
    journal_entries          : list[dict]  = []
    focus_session_minutes    : list[float] = []
    goals_completed          : int         = 0
    goals_abandoned          : int         = 0
    valence_history          : list[float] = []
    schumann_state           : Optional[dict] = None  # SchumannState.to_stage_dict()


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@stage_router.get("/health")
async def health() -> JSONResponse:
    ok = _engine is not None
    return JSONResponse(status_code=200 if ok else 503, content={"ok": ok})


@stage_router.get("/record/{principal_id}")
async def get_record(principal_id: str) -> JSONResponse:
    if _engine is None:
        raise HTTPException(503, "Stage engine not initialised")
    conn = _memory._conn
    row  = conn.execute(
        "SELECT * FROM stage_records WHERE principal_id=?",
        (principal_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"No record for principal '{principal_id}'")
    return JSONResponse(content=dict(row))


@stage_router.get("/history/{principal_id}")
async def get_history(principal_id: str) -> JSONResponse:
    if _engine is None:
        raise HTTPException(503, "Stage engine not initialised")
    history = _engine.get_stage_history(principal_id)
    return JSONResponse(content={"transitions": history})


@stage_router.post("/evaluate")
async def evaluate(req: EvaluateRequest) -> JSONResponse:
    """
    Run a full stage evaluation tick.

    If schumann_state is provided it is converted via schumann_bridge;
    its alignment_score is appended to alignment_score_history and the
    env_modifier is returned in the response metadata.
    """
    if _engine is None:
        raise HTTPException(503, "Stage engine not initialised")

    from .schumann_bridge import schumann_to_alignment
    alignment_history = list(req.alignment_score_history)
    env_modifier = 1.0

    if req.schumann_state is not None:
        sr_score, env_modifier = schumann_to_alignment(req.schumann_state)
        alignment_history.append(sr_score)

    fwd, reg = _tracker.get_and_update(
        principal_id=req.principal_id,
        scores=_engine._score_only(
            goal_states=req.goal_states,
            hrv_rmssd_history=req.hrv_rmssd_history,
            alignment_score_history=alignment_history,
            journal_entries=req.journal_entries,
            focus_session_minutes=req.focus_session_minutes,
            goals_completed=req.goals_completed,
            goals_abandoned=req.goals_abandoned,
            valence_history=req.valence_history,
        ),
        current_stage=_get_current_stage(req.principal_id),
    )

    result = _engine.evaluate(
        principal_id=req.principal_id,
        goal_states=req.goal_states,
        hrv_rmssd_history=req.hrv_rmssd_history,
        alignment_score_history=alignment_history,
        journal_entries=req.journal_entries,
        focus_session_minutes=req.focus_session_minutes,
        goals_completed=req.goals_completed,
        goals_abandoned=req.goals_abandoned,
        valence_history=req.valence_history,
        days_forward_window_met=fwd,
        days_regression_window=reg,
    )

    payload = result.to_dict()
    payload["meta"] = {
        "env_modifier"          : env_modifier,
        "days_forward_window_met": fwd,
        "days_regression_window" : reg,
    }
    return JSONResponse(content=payload)


def _get_current_stage(principal_id: str) -> int:
    conn = _memory._conn
    row  = conn.execute(
        "SELECT current_stage FROM stage_records WHERE principal_id=?",
        (principal_id,),
    ).fetchone()
    return row["current_stage"] if row else 1
