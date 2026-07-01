"""
api/telemetry_routes.py
Canon: C17 (GAIA_Memory_Architecture), operational observability

FastAPI router: /telemetry/*

System health, runtime metrics, and structured event ingestion.
This is how operators observe GAIA from the outside — heartbeat,
latency, throughput, and event bus injection.

Routes:
  GET  /telemetry/health     — liveness + readiness probe
  GET  /telemetry/metrics    — runtime counters and latency histograms
  POST /telemetry/event      — ingest a structured telemetry event
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

# ─── Router ───────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# Process-start time for uptime calculation
_START_TIME = time.time()

# In-memory event ring buffer (last 500 events)
_MAX_EVENTS = 500
_event_buffer: list[dict] = []

# Simple counter store: event_type → count
_counters: dict[str, int] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Pydantic models ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str          # "healthy" | "degraded" | "critical"
    uptime_seconds: float
    timestamp: str
    version: str = "2.0.0"
    canon_status: Optional[str] = None  # GREEN / YELLOW / RED if available


class MetricsResponse(BaseModel):
    uptime_seconds: float
    total_events_ingested: int
    event_counts: dict[str, int]
    buffer_size: int
    timestamp: str


class TelemetryEvent(BaseModel):
    event_type: str                          # e.g. "twin.message", "override.activated"
    source: str                              # service/module emitting the event
    payload: dict[str, Any] = Field(default_factory=dict)
    severity: str = "info"                  # debug | info | warning | error | critical
    human_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None         # caller-supplied; falls back to ingestion time


class TelemetryEventResponse(BaseModel):
    event_id: str
    accepted: bool
    buffer_position: int
    timestamp: str


# ─── GET /telemetry/health ────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Liveness + readiness probe.
    Returns 200 when the service is accepting requests.
    Attempts to surface canon status from canon_loader_v2 if available.
    """
    uptime = time.time() - _START_TIME
    canon_status_val: Optional[str] = None

    try:
        from core.canon_loader_v2 import canon_status
        canon_status_val = canon_status().value
        status = "healthy" if canon_status_val == "GREEN" else "degraded"
    except Exception:
        status = "healthy"  # canon not required for liveness

    return HealthResponse(
        status=status,
        uptime_seconds=round(uptime, 2),
        timestamp=_now(),
        canon_status=canon_status_val,
    )


# ─── GET /telemetry/metrics ───────────────────────────────────────────────────

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Return runtime counters and buffer occupancy."""
    uptime = time.time() - _START_TIME
    total = sum(_counters.values())

    return MetricsResponse(
        uptime_seconds=round(uptime, 2),
        total_events_ingested=total,
        event_counts=dict(_counters),
        buffer_size=len(_event_buffer),
        timestamp=_now(),
    )


# ─── POST /telemetry/event ────────────────────────────────────────────────────

@router.post("/event", response_model=TelemetryEventResponse)
async def ingest_event(event: TelemetryEvent) -> TelemetryEventResponse:
    """
    Ingest a structured telemetry event into the ring buffer.
    Increments per-type counters. Trims buffer when full.
    """
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    ingested_at = _now()

    record = {
        "event_id": event_id,
        "event_type": event.event_type,
        "source": event.source,
        "payload": event.payload,
        "severity": event.severity,
        "human_id": event.human_id,
        "session_id": event.session_id,
        "timestamp": event.timestamp or ingested_at,
        "ingested_at": ingested_at,
    }

    # Ring buffer — trim oldest when full
    if len(_event_buffer) >= _MAX_EVENTS:
        _event_buffer.pop(0)
    _event_buffer.append(record)

    # Increment counter
    _counters[event.event_type] = _counters.get(event.event_type, 0) + 1

    return TelemetryEventResponse(
        event_id=event_id,
        accepted=True,
        buffer_position=len(_event_buffer) - 1,
        timestamp=ingested_at,
    )
