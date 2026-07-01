"""
Sentinel API routes — /v1/sentinel/

Endpoints:
  GET  /v1/sentinel/status
       Returns the Sentinel\'s current health: active rules, audit stats,
       and the last N threat events at BLOCK or CRITICAL level.

  GET  /v1/sentinel/audit
       Query the in-memory audit ring with optional filters.
       Query parameters:
         level      — exact level filter (watch|warn|block|critical)
         min_level  — minimum level filter (same values)
         caller_id  — filter by caller
         gaian_id   — filter by GAIAN
         since      — ISO-8601 datetime (events on/after this time)
         limit      — max results to return (default 50, max 500)

  GET  /v1/sentinel/audit/stream
       Server-Sent Events stream: emits a JSON line for every new
       ThreatEvent at WARN level or above as it is recorded.
       Useful for live dashboards and operator alerting.

Access control:
  All three endpoints require operator-level auth (the same Bearer
  token mechanism used by the rest of the server). A GAIAN caller_id
  is never granted access to the audit log — these routes are for
  operators only (enforced by the `require_operator` dependency).
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.sentinel.sentinel import Sentinel
from core.sentinel.threat import ThreatLevel


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/v1/sentinel", tags=["Sentinel"])


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class ThreatEventOut(BaseModel):
    """A single serialised ThreatEvent for the HTTP layer."""
    event_id:    str
    level:       str
    category:    str
    rule_name:   str
    caller_id:   str
    endpoint:    str
    gaian_id:    Optional[str] = None
    description: str
    detail:      dict          = Field(default_factory=dict)
    occurred_at: str
    blocked:     bool

    @classmethod
    def from_event(cls, event) -> "ThreatEventOut":
        return cls(
            event_id=event.event_id,
            level=event.level.value,
            category=event.category.value,
            rule_name=event.rule_name,
            caller_id=event.caller_id,
            endpoint=event.endpoint,
            gaian_id=event.gaian_id,
            description=event.description,
            detail=event.detail,
            occurred_at=event.occurred_at.isoformat(),
            blocked=event.blocked,
        )


class AuditStatsOut(BaseModel):
    total:    int
    watch:    int
    warn:     int
    block:    int
    critical: int


class SentinelStatusOut(BaseModel):
    """Response model for GET /v1/sentinel/status."""
    active_rules:    List[str]
    rule_count:      int
    audit_stats:     AuditStatsOut
    recent_critical: List[ThreatEventOut] = Field(default_factory=list)
    recent_blocked:  List[ThreatEventOut] = Field(default_factory=list)


class AuditQueryOut(BaseModel):
    """Response model for GET /v1/sentinel/audit."""
    count:  int
    events: List[ThreatEventOut]


# ---------------------------------------------------------------------------
# Dependency: sentinel instance
# ---------------------------------------------------------------------------
# The sentinel singleton is set on the router at app startup.
# See server/app.py: router_sentinel.sentinel = sentinel_instance
# ---------------------------------------------------------------------------

def _get_sentinel() -> Sentinel:
    s = getattr(router, "sentinel", None)
    if s is None:
        raise HTTPException(
            status_code=503,
            detail="Sentinel not initialised. Boot sequence incomplete.",
        )
    return s


# ---------------------------------------------------------------------------
# Operator auth dependency
# ---------------------------------------------------------------------------
# Reuses the same Bearer-token auth from server/middleware.py but adds
# the constraint that GAIAN IDs (UUIDs) are not treated as operators.
# Operators are non-UUID tokens defined in GAIA_BEARER_TOKENS.
# ---------------------------------------------------------------------------

import re as _re
_UUID_RE = _re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def require_operator(
    sentinel: Sentinel = Depends(_get_sentinel),
    # caller_id is resolved upstream in server/middleware.py and
    # stored on request.state by the BearerAuthMiddleware.
    # We access it via the FastAPI Request object.
    request: "fastapi.Request" = Depends(lambda r: r),
) -> Sentinel:
    """
    Dependency that guards Sentinel routes from GAIAN callers.
    GAIAN IDs are UUIDs; operator tokens are not.
    An unauthenticated request is also rejected.
    """
    caller_id: str = getattr(request.state, "caller_id", "")
    if not caller_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to access Sentinel routes.",
        )
    if _UUID_RE.match(caller_id):
        raise HTTPException(
            status_code=403,
            detail="GAIANs may not access the Sentinel audit log. "
                   "This is an operator-only interface.",
        )
    return sentinel


# ---------------------------------------------------------------------------
# GET /v1/sentinel/status
# ---------------------------------------------------------------------------

@router.get(
    "/status",
    response_model=SentinelStatusOut,
    summary="Sentinel health and active rule summary",
    description=(
        "Returns the list of active Sentinel rules, aggregate audit stats "
        "(counts by threat level), and the 10 most recent BLOCK and CRITICAL "
        "events from the in-memory ring buffer. "
        "Operator authentication required."
    ),
)
def get_sentinel_status(
    sentinel: Sentinel = Depends(require_operator),
) -> SentinelStatusOut:
    raw = sentinel.status()
    stats = raw["audit_stats"]

    recent_all = sentinel.audit.recent(200)
    recent_critical = [
        ThreatEventOut.from_event(e)
        for e in recent_all
        if e.level == ThreatLevel.CRITICAL
    ][-10:]
    recent_blocked = [
        ThreatEventOut.from_event(e)
        for e in recent_all
        if e.level == ThreatLevel.BLOCK
    ][-10:]

    return SentinelStatusOut(
        active_rules=raw["rules"],
        rule_count=raw["rule_count"],
        audit_stats=AuditStatsOut(
            total=stats["total"],
            watch=stats["watch"],
            warn=stats["warn"],
            block=stats["block"],
            critical=stats["critical"],
        ),
        recent_critical=recent_critical,
        recent_blocked=recent_blocked,
    )


# ---------------------------------------------------------------------------
# GET /v1/sentinel/audit
# ---------------------------------------------------------------------------

_VALID_LEVELS = {"watch", "warn", "block", "critical"}


@router.get(
    "/audit",
    response_model=AuditQueryOut,
    summary="Query the Sentinel audit log",
    description=(
        "Returns ThreatEvents from the in-memory ring buffer (last 1,000 "
        "events). Filter by level, min_level, caller_id, gaian_id, or since. "
        "For historical queries spanning multiple days, read the JSONL files "
        "at GAIA_ROOT/sentinel/audit/ directly. "
        "Operator authentication required."
    ),
)
def get_sentinel_audit(
    sentinel:  Sentinel = Depends(require_operator),
    level:     Optional[str] = Query(
        None,
        description="Exact threat level: watch | warn | block | critical",
    ),
    min_level: Optional[str] = Query(
        None,
        description="Minimum threat level (inclusive): watch | warn | block | critical",
    ),
    caller_id: Optional[str] = Query(None, description="Filter by caller ID"),
    gaian_id:  Optional[str] = Query(None, description="Filter by GAIAN ID"),
    since:     Optional[str] = Query(
        None,
        description="ISO-8601 datetime — only events at or after this time",
    ),
    limit:     int = Query(
        50,
        ge=1,
        le=500,
        description="Maximum number of events to return (1–500, default 50)",
    ),
) -> AuditQueryOut:
    # Validate level strings
    level_enum     = _parse_level(level, "level")
    min_level_enum = _parse_level(min_level, "min_level")

    # Parse since datetime
    since_dt: Optional[datetime] = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid 'since' datetime: '{since}'. "
                       f"Use ISO-8601 format, e.g. 2026-06-30T19:00:00Z",
            )

    events = sentinel.audit.filter(
        level=level_enum,
        min_level=min_level_enum,
        caller_id=caller_id,
        gaian_id=gaian_id,
        since=since_dt,
    )

    # Most recent first, then limit
    events = list(reversed(events))[:limit]

    return AuditQueryOut(
        count=len(events),
        events=[ThreatEventOut.from_event(e) for e in events],
    )


# ---------------------------------------------------------------------------
# GET /v1/sentinel/audit/stream  — Server-Sent Events
# ---------------------------------------------------------------------------

@router.get(
    "/audit/stream",
    summary="Live SSE stream of Sentinel threat events",
    description=(
        "Server-Sent Events stream. Emits a JSON object for every ThreatEvent "
        "at WARN level or above as it is recorded by the Sentinel. "
        "Connect with EventSource in a browser or `curl -N`. "
        "Operator authentication required."
    ),
    response_class=StreamingResponse,
)
async def stream_sentinel_audit(
    sentinel: Sentinel = Depends(require_operator),
    min_level: Optional[str] = Query(
        "warn",
        description="Minimum level to stream: watch | warn | block | critical",
    ),
) -> StreamingResponse:
    min_level_enum = _parse_level(min_level, "min_level") or ThreatLevel.WARN

    _LEVEL_ORDER = [
        ThreatLevel.WATCH, ThreatLevel.WARN,
        ThreatLevel.BLOCK, ThreatLevel.CRITICAL,
    ]
    min_idx = _LEVEL_ORDER.index(min_level_enum) if min_level_enum in _LEVEL_ORDER else 1

    # We push events via an asyncio.Queue populated by an audit hook.
    queue: asyncio.Queue = asyncio.Queue(maxsize=256)

    def _hook(event) -> None:
        lvl_list = [ThreatLevel.WATCH, ThreatLevel.WARN,
                    ThreatLevel.BLOCK, ThreatLevel.CRITICAL]
        if event.level not in lvl_list:
            return
        if lvl_list.index(event.level) < min_idx:
            return
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass  # drop if consumer is slow

    sentinel.audit.add_hook(_hook)

    async def _generate() -> AsyncGenerator[str, None]:
        # Send a heartbeat comment every 15 s to keep the connection alive
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    data = json.dumps(event.to_dict(), default=str)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"  # SSE comment, no client event
        except asyncio.CancelledError:
            pass
        finally:
            # Remove hook when client disconnects
            try:
                sentinel.audit._hooks.remove(_hook)
            except ValueError:
                pass

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_level(
    value: Optional[str],
    param_name: str,
) -> Optional[ThreatLevel]:
    if value is None:
        return None
    normed = value.lower()
    if normed not in _VALID_LEVELS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid '{param_name}' value: '{value}'. "
                   f"Must be one of: {sorted(_VALID_LEVELS)}",
        )
    return ThreatLevel(normed)
