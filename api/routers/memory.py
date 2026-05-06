"""
api.routers.memory
==================
HTTP endpoints for GAIA's semantic memory layer.

All routes are prefixed with /api/memory (see main.py include_router call).

Endpoints
---------
POST   /api/memory/remember           Store a new memory item.
POST   /api/memory/retrieve           Semantic search over memories.
DELETE /api/memory/forget/{item_id}   Soft-delete one item by id.
DELETE /api/memory/forget-user        Soft-delete ALL items for a user.
GET    /api/memory/stats              Row counts and health metadata.
GET    /api/memory/health             Liveness probe for the memory subsystem.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

log = logging.getLogger("gaia.api.memory")

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class RememberRequest(BaseModel):
    """Body for POST /api/memory/remember."""
    user_id:     str   = Field(...,   description="Owner of this memory.")
    text:        str   = Field(...,   min_length=1, description="Text to remember.")
    role:        str   = Field("user", description="'user' | 'gaia' | 'system'")
    kind:        str   = Field("message", description="MemoryKind value (message, fact, preference, goal, …)")
    tier:        str   = Field("short_term", description="MemoryTier value (ephemeral, short_term, long_term, permanent)")
    importance:  float = Field(0.5,  ge=0.0, le=1.0)
    session_id:  Optional[str]  = None
    topic_tag:   Optional[str]  = None
    ttl_seconds: Optional[int]  = None
    metadata:    Optional[Dict[str, Any]] = None


class RememberResponse(BaseModel):
    id:     int
    status: str = "remembered"


class RetrieveRequest(BaseModel):
    """Body for POST /api/memory/retrieve."""
    user_id:          str             = Field(..., description="User whose memories to search.")
    query:            str             = Field(..., min_length=1, description="Natural language query.")
    top_k:            int             = Field(10,  ge=1, le=100)
    kinds:            Optional[List[str]] = None
    tiers:            Optional[List[str]] = None
    topic_tag:        Optional[str]  = None
    since_ts:         Optional[int]  = None
    importance_floor: float           = Field(0.0, ge=0.0, le=1.0)


class MemoryHit(BaseModel):
    id:          int
    text:        str
    kind:        str
    tier:        str
    role:        str
    importance:  float
    score:       float
    created_at:  int
    session_id:  Optional[str]
    topic_tag:   Optional[str]


class RetrieveResponse(BaseModel):
    hits:  List[MemoryHit]
    count: int


class StatsResponse(BaseModel):
    total:       int
    by_kind:     Dict[str, int]
    vec_enabled: bool
    db_path:     str


# ---------------------------------------------------------------------------
# Helper — get live store or raise 503
# ---------------------------------------------------------------------------

def _store():
    try:
        from core.runtime import get_runtime
        return get_runtime().memory_store
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /api/memory/remember
# ---------------------------------------------------------------------------

@router.post("/remember", response_model=RememberResponse, summary="Store a memory item")
async def remember(req: RememberRequest) -> RememberResponse:
    """
    Persist a text chunk as a memory item for *user_id*.

    The store embeds the text asynchronously and writes it into
    SQLite.  Returns the assigned row id on success.
    """
    store = _store()

    from core.memory import MemoryKind, MemoryTier
    try:
        kind = MemoryKind(req.kind)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid kind '{req.kind}'. "
            f"Valid values: {[k.value for k in MemoryKind]}")
    try:
        tier = MemoryTier(req.tier)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid tier '{req.tier}'. "
            f"Valid values: {[t.value for t in MemoryTier]}")

    try:
        item_id = await store.remember(
            user_id     = req.user_id,
            text        = req.text,
            role        = req.role,
            kind        = kind,
            tier        = tier,
            importance  = req.importance,
            session_id  = req.session_id,
            topic_tag   = req.topic_tag,
            ttl_seconds = req.ttl_seconds,
            metadata    = req.metadata,
        )
    except Exception as exc:
        log.exception("remember() failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to store memory.")

    return RememberResponse(id=item_id)


# ---------------------------------------------------------------------------
# POST /api/memory/retrieve
# ---------------------------------------------------------------------------

@router.post("/retrieve", response_model=RetrieveResponse, summary="Semantic memory search")
async def retrieve(req: RetrieveRequest) -> RetrieveResponse:
    """
    Return the *top_k* most relevant memories for *query*.

    Uses hybrid scoring: cosine similarity + importance weight + recency.
    Optional filters: kinds, tiers, topic_tag, since_ts, importance_floor.
    """
    store = _store()

    from core.memory import MemoryKind, MemoryTier
    kinds = None
    if req.kinds:
        try:
            kinds = [MemoryKind(k) for k in req.kinds]
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    tiers = None
    if req.tiers:
        try:
            tiers = [MemoryTier(t) for t in req.tiers]
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    try:
        results = await store.retrieve(
            user_id          = req.user_id,
            query            = req.query,
            top_k            = req.top_k,
            kinds            = kinds,
            tiers            = tiers,
            topic_tag        = req.topic_tag,
            since_ts         = req.since_ts,
            importance_floor = req.importance_floor,
        )
    except Exception as exc:
        log.exception("retrieve() failed: %s", exc)
        raise HTTPException(status_code=500, detail="Memory retrieval failed.")

    hits = []
    for r in results:
        i = r.item
        hits.append(MemoryHit(
            id         = i.id or 0,
            text       = i.text,
            kind       = i.kind.value if hasattr(i.kind, "value") else str(i.kind),
            tier       = i.tier.value if hasattr(i.tier, "value") else str(i.tier),
            role       = i.role,
            importance = i.importance,
            score      = round(r.score, 4),
            created_at = i.created_at,
            session_id = i.session_id,
            topic_tag  = i.topic_tag,
        ))

    return RetrieveResponse(hits=hits, count=len(hits))


# ---------------------------------------------------------------------------
# DELETE /api/memory/forget/{item_id}
# ---------------------------------------------------------------------------

@router.delete("/forget/{item_id}", summary="Soft-delete one memory item")
async def forget_item(
    item_id: int,
    user_id: str = Query(..., description="Owner of the item (safety check)."),
) -> dict:
    """
    Soft-delete a single memory item.  The row is marked `deleted=1`
    and excluded from all future retrievals.

    Hard-deletion happens on the next compaction run.
    """
    store = _store()
    # Verify ownership before deleting
    row = store._conn.execute(
        "SELECT id FROM memory_items WHERE id = ? AND user_id = ? AND deleted = 0",
        (item_id, user_id),
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Memory item {item_id} not found for user '{user_id}'.",
        )
    store.forget(item_id)
    return {"status": "forgotten", "item_id": item_id}


# ---------------------------------------------------------------------------
# DELETE /api/memory/forget-user
# ---------------------------------------------------------------------------

@router.delete("/forget-user", summary="Soft-delete all memories for a user")
async def forget_user(
    user_id: str = Query(..., description="User whose memories to erase."),
) -> dict:
    """
    Soft-delete **all** memory items belonging to *user_id*.
    Useful for a "forget me" / GDPR-style reset.
    """
    store = _store()
    count = store.forget_user(user_id)
    return {"status": "forgotten", "user_id": user_id, "items_deleted": count}


# ---------------------------------------------------------------------------
# GET /api/memory/stats
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsResponse, summary="Memory store statistics")
async def stats(
    user_id: Optional[str] = Query(None, description="Filter stats to one user.")
) -> StatsResponse:
    """Return row counts broken down by kind, plus store metadata."""
    store = _store()
    data = store.stats(user_id=user_id)
    return StatsResponse(
        total       = data["total"],
        by_kind     = data["by_kind"],
        vec_enabled = data["vec_enabled"],
        db_path     = data["db_path"],
    )


# ---------------------------------------------------------------------------
# GET /api/memory/health
# ---------------------------------------------------------------------------

@router.get("/health", summary="Memory subsystem liveness probe")
async def memory_health() -> dict:
    """Quick liveness check for the memory subsystem."""
    try:
        from core.runtime import get_runtime
        rt    = get_runtime()
        store = rt.memory_store
        total = store.count()
        return {
            "status":      "ok",
            "ready":       True,
            "total_items": total,
            "vec_enabled": store._vec_ok,
            "db_path":     str(store._db_path),
        }
    except RuntimeError:
        return {"status": "not_ready", "ready": False}
    except Exception as exc:
        return {"status": "error", "detail": str(exc), "ready": False}
