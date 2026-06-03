"""FastAPI routes for the Agent Telemetry Hub.

Endpoints:
  GET  /telemetry/stream          — SSE live event stream (Glass Room)
  GET  /telemetry/session/{id}    — Full session trace (JSON)
  GET  /telemetry/skill/{id}      — Skill health report
  GET  /telemetry/dq              — Recent DQ scores
  GET  /telemetry/oe              — Orchestration Efficiency metric
  GET  /telemetry/recent          — Last N events
  POST /telemetry/export/{id}     — Export session trace as JSON download
  DELETE /telemetry/range         — User-initiated deletion (right to erasure)
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

# TelemetryCollector is injected via FastAPI dependency from main.py
# from src-python.telemetry import TelemetryCollector  (resolved at runtime)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def get_telemetry(request: Request):
    """Dependency: retrieve shared TelemetryCollector from app state."""
    return request.app.state.telemetry


# ---------------------------------------------------------------------------
# SSE live stream — Glass Room feed
# ---------------------------------------------------------------------------

@router.get("/stream")
async def stream_events(request: Request, telemetry=Depends(get_telemetry)):
    """Server-Sent Events stream. Connect from Glass Room frontend."""
    q = telemetry.subscribe()

    async def event_generator():
        try:
            async for event in telemetry.stream_events(q):
                payload = json.dumps(event.to_dict(), default=str)
                yield f"data: {payload}\n\n"
                if await request.is_disconnected():
                    break
        finally:
            telemetry.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Session trace
# ---------------------------------------------------------------------------

@router.get("/session/{session_id}")
async def get_session_trace(session_id: str, telemetry=Depends(get_telemetry)):
    events = await telemetry.get_session_trace(session_id)
    return {"session_id": session_id, "events": [e.to_dict() for e in events]}


# ---------------------------------------------------------------------------
# Skill health
# ---------------------------------------------------------------------------

@router.get("/skill/{skill_id}")
async def get_skill_health(
    skill_id: str,
    window_minutes: int = Query(60, ge=1, le=10080),
    telemetry=Depends(get_telemetry),
):
    report = await telemetry.get_skill_health(skill_id, window_minutes)
    return {
        "skill_id": report.skill_id,
        "circuit_state": report.circuit_state,
        "total_events": report.total_events,
        "error_count": report.error_count,
        "error_rate": report.error_rate,
        "fallback_count": report.fallback_count,
        "avg_duration_ms": report.avg_duration_ms,
        "healthy": report.healthy,
        "last_failure_at": report.last_failure_at.isoformat() if report.last_failure_at else None,
        "window_minutes": report.window_minutes,
    }


# ---------------------------------------------------------------------------
# DQ history
# ---------------------------------------------------------------------------

@router.get("/dq")
async def get_dq_history(
    limit: int = Query(100, ge=1, le=500),
    telemetry=Depends(get_telemetry),
):
    records = await telemetry.get_dq_history(limit)
    return {"records": records}


# ---------------------------------------------------------------------------
# Orchestration Efficiency
# ---------------------------------------------------------------------------

@router.get("/oe")
async def get_oe(
    window: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    telemetry=Depends(get_telemetry),
):
    oe = await telemetry.compute_oe(window)
    return {
        "window": oe.window,
        "total_tasks": oe.total_tasks,
        "successful_tasks": oe.successful_tasks,
        "failed_tasks": oe.failed_tasks,
        "avg_total_latency_s": oe.avg_total_latency_s,
        "avg_engine_count": oe.avg_engine_count,
        "avg_dq_score": oe.avg_dq_score,
        "degraded_fraction": oe.degraded_fraction,
        "oe_score": oe.oe_score,
        "bottleneck_skill": oe.bottleneck_skill,
    }


# ---------------------------------------------------------------------------
# Recent events (pagination)
# ---------------------------------------------------------------------------

@router.get("/recent")
async def get_recent_events(
    limit: int = Query(50, ge=1, le=200),
    session_id: Optional[str] = Query(None),
    telemetry=Depends(get_telemetry),
):
    events = await telemetry.get_recent_events(limit, session_id)
    return {"events": [e.to_dict() for e in events]}


# ---------------------------------------------------------------------------
# Export (user download)
# ---------------------------------------------------------------------------

@router.post("/export/{session_id}")
async def export_session(
    session_id: str,
    telemetry=Depends(get_telemetry),
):
    json_str = await telemetry.export_session_json(session_id)
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="gaia_session_{session_id}.json"'},
    )


# ---------------------------------------------------------------------------
# User-initiated deletion (Canon C01 — right to erasure)
# ---------------------------------------------------------------------------

@router.delete("/range")
async def delete_range(
    since: str = Query(..., description="ISO 8601 datetime"),
    until: str = Query(..., description="ISO 8601 datetime"),
    telemetry=Depends(get_telemetry),
):
    since_dt = datetime.fromisoformat(since)
    until_dt = datetime.fromisoformat(until)
    count = await telemetry.delete_range(since_dt, until_dt)
    return {"deleted": count, "since": since, "until": until}
