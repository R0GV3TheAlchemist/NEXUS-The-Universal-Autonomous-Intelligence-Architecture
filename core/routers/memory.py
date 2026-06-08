"""
core/routers/memory.py

C17-governed persistent memory endpoints:
  GET    /memory/list          — list all active memories
  POST   /memory/add           — add a new memory
  POST   /memory/store         — store a raw text fragment to ChromaDB
  GET    /memory/recall        — semantic similarity search (?q=&top_k=5)
  POST   /memory/context       — build ranked context block for LLM injection  ★ NEW
  PUT    /memory/{id}          — edit a memory (new_content query param)
  DELETE /memory/{id}          — soft-delete a memory (+ ChromaDB forget)
  GET    /memory/audit         — full audit log
  POST   /memory/{id}/freeze   — freeze for appeal review
  POST   /memory/{id}/unfreeze — lift freeze after resolution

All endpoints are intentionally unauthenticated at the router level
so the local Tauri frontend can call them without a token.

Canon Ref: C17 (Persistent Memory and Identity Architecture)
"""

from __future__ import annotations

import datetime
import hashlib
import math
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.memory_chroma import get_chroma
from core.memory_store import get_memory_store

router = APIRouter(prefix="/memory", tags=["memory"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class AddMemoryRequest(BaseModel):
    content: str
    source: str = "explicit"       # explicit | inferred | session | conversation
    purposes: list[str] = ["general"]
    confidence: float = 1.0


class StoreMemoryRequest(BaseModel):
    text: str
    source: str = "conversation"
    emotion: str = "neutral"
    gaian_slug: str = "gaia"
    session_id: str = ""


class MemoryContextRequest(BaseModel):
    """
    Body for POST /memory/context.

    The chat pipeline sends this before every LLM stream call.
    The returned `context_block` is injected verbatim into the system prompt
    so the model has grounded, ranked memory of the user.
    """
    query: str = Field(..., description="The current user message or intent summary.")
    gaian_slug: str = Field("gaia", description="Which Gaian's ChromaDB collection to search.")
    top_k: int = Field(8, ge=1, le=30, description="Max candidate fragments from ChromaDB.")
    affect_state: str = Field(
        "neutral",
        description="Current affect/emotion label (e.g. 'grief', 'joy'). "
                    "Used to boost emotionally-resonant memories.",
    )
    session_id: str = Field("", description="Current session ID — used to de-prioritise same-session repeats.")
    max_tokens: int = Field(
        600,
        ge=50,
        le=2000,
        description="Soft token budget for the context block (1 token ≈ 4 chars).",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_AFFECT_KEYWORDS: dict[str, list[str]] = {
    "grief":    ["loss", "death", "grief", "father", "mother", "gone", "miss"],
    "joy":      ["happy", "celebrat", "excit", "achiev", "proud", "wonderful"],
    "anxiety":  ["anxious", "worry", "fear", "stress", "overwhelm", "panic"],
    "anger":    ["anger", "frustrat", "rage", "unfair", "betray"],
    "longing":  ["miss", "wish", "hope", "long", "want", "dream"],
    "curiosity":["question", "wonder", "curious", "discover", "learn", "why"],
}


def _affect_boost(text: str, affect: str) -> float:
    """Return a small additive boost (0.0–0.15) if the fragment resonates with the current affect."""
    keywords = _AFFECT_KEYWORDS.get(affect.lower(), [])
    if not keywords:
        return 0.0
    t = text.lower()
    matches = sum(1 for kw in keywords if kw in t)
    return min(0.15, matches * 0.05)


def _recency_score(idx: int, total: int, metadata: dict[str, Any]) -> float:
    """
    Derive a 0–1 recency score.

    ChromaDB returns fragments ordered by cosine distance (closest first).
    When a stored `timestamp` is available we use it; otherwise we fall back
    to position-based decay so the top recalled hit scores highest.
    """
    ts = metadata.get("timestamp") or metadata.get("created_at")
    if ts:
        try:
            dt = datetime.datetime.fromisoformat(str(ts))
            age_hours = (datetime.datetime.utcnow() - dt).total_seconds() / 3600
            # Half-life: 7 days → score 0.5 at 168 hours; recent → 1.0
            return math.exp(-age_hours / 168)
        except Exception:
            pass
    # Fallback: linear decay by position
    if total <= 1:
        return 1.0
    return 1.0 - (idx / (total - 1)) * 0.5


def _build_context_block(fragments: list[dict[str, Any]], max_chars: int) -> tuple[str, bool]:
    """
    Format ranked fragments into the XML-style context block.
    Returns (block_text, truncated_flag).
    """
    if not fragments:
        return "", False

    lines = ["<memory>"]
    used = len("<memory>\n</memory>")
    truncated = False

    for i, frag in enumerate(fragments, start=1):
        text = frag.get("text", "").strip()
        score = frag.get("final_score", 0.0)
        line = f"  [{i}] (relevance={score:.2f}) {text}"
        if used + len(line) + 1 > max_chars:
            truncated = True
            break
        lines.append(line)
        used += len(line) + 1

    lines.append("</memory>")
    return "\n".join(lines), truncated


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/list")
def memory_list():
    """Return all active (non-deleted) C17-governed memory entries."""
    store = get_memory_store()
    return store.list_all()


@router.post("/add")
def memory_add(req: AddMemoryRequest):
    """Add a new governed memory entry (JSON store + ChromaDB)."""
    if not req.content.strip():
        raise HTTPException(status_code=422, detail="content must not be empty")
    store = get_memory_store()
    entry = store.add(
        content    = req.content.strip(),
        source     = req.source,
        purposes   = req.purposes,
        confidence = max(0.0, min(1.0, req.confidence)),
    )
    # Mirror to ChromaDB for semantic recall
    chroma = get_chroma()
    chroma.store(
        text=entry.content,
        memory_id=entry.id,
        source=entry.source,
        gaian_slug="gaia",
    )
    return entry.to_dict()


@router.post("/store")
def memory_store_endpoint(req: StoreMemoryRequest):
    """
    Store a raw text fragment directly to ChromaDB.
    Used by auto-store after conversation turns.
    Does NOT create a C17 governed entry — use /add for that.
    """
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="text must not be empty")
    chroma = get_chroma()
    if not chroma.available:
        return {"status": "skipped", "reason": "ChromaDB not available"}
    uid = hashlib.sha256(
        f"{req.gaian_slug}:{req.session_id}:{req.text[:64]}:{datetime.datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:16]
    ok = chroma.store(
        text=req.text,
        memory_id=uid,
        source=req.source,
        emotion=req.emotion,
        gaian_slug=req.gaian_slug,
        session_id=req.session_id,
    )
    return {"status": "stored" if ok else "failed", "id": uid, "chroma_count": chroma.count()}


@router.post("/context")
def memory_context(req: MemoryContextRequest):
    """
    Build a ranked, formatted memory context block for LLM injection.

    The chat pipeline calls this before every stream request.  The response's
    `context_block` is inserted into the system prompt between GAIA's identity
    preamble and the current user message so the model has grounded recall.

    Ranking algorithm
    -----------------
    For each ChromaDB hit:
      relevance_score = 1.0 - cosine_distance   (ChromaDB returns distance 0–2)
      recency_score   = exponential decay by age (fallback: position decay)
      affect_boost    = 0.0–0.15 if fragment text resonates with affect_state
      final_score     = 0.70 * relevance + 0.30 * recency + affect_boost

    Fragments from the current session are de-prioritised by 0.1 to avoid
    echo-chamber repetition within a single conversation.

    Canon Ref: C17
    """
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")

    chroma = get_chroma()
    if not chroma.available:
        return {
            "context_block": "",
            "fragments": [],
            "count": 0,
            "chroma_available": False,
            "truncated": False,
        }

    raw_hits: list[dict[str, Any]] = chroma.recall(
        query=req.query,
        top_k=req.top_k,
        gaian_slug=req.gaian_slug,
    )

    if not raw_hits:
        return {
            "context_block": "",
            "fragments": [],
            "count": 0,
            "chroma_available": True,
            "truncated": False,
        }

    total = len(raw_hits)
    scored: list[dict[str, Any]] = []

    for idx, hit in enumerate(raw_hits):
        distance = float(hit.get("distance", 1.0))
        relevance = max(0.0, min(1.0, 1.0 - (distance / 2.0)))

        metadata = hit.get("metadata") or {}
        recency = _recency_score(idx, total, metadata)

        boost = _affect_boost(hit.get("text", ""), req.affect_state)

        same_session_penalty = (
            0.10
            if req.session_id and metadata.get("session_id") == req.session_id
            else 0.0
        )

        final = 0.70 * relevance + 0.30 * recency + boost - same_session_penalty
        final = max(0.0, min(1.0, final))

        scored.append({
            "text":        hit.get("text", ""),
            "memory_id":   hit.get("id") or hit.get("memory_id", ""),
            "source":      metadata.get("source", "conversation"),
            "distance":    distance,
            "relevance":   round(relevance, 4),
            "recency":     round(recency, 4),
            "affect_boost": round(boost, 4),
            "final_score": round(final, 4),
            "metadata":    metadata,
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    scored = [f for f in scored if f["final_score"] >= 0.10]

    max_chars = req.max_tokens * 4
    context_block, truncated = _build_context_block(scored, max_chars)

    return {
        "context_block":   context_block,
        "fragments":       scored,
        "count":           len(scored),
        "chroma_available": True,
        "truncated":       truncated,
    }


@router.get("/recall")
def memory_recall(q: str, top_k: int = 5, gaian_slug: str = "gaia"):
    """
    Semantic similarity search over ChromaDB.
    Returns top_k most relevant memory fragments for the query.
    """
    if not q.strip():
        raise HTTPException(status_code=422, detail="q must not be empty")
    chroma = get_chroma()
    if not chroma.available:
        return {"results": [], "chroma_available": False}
    hits = chroma.recall(query=q, top_k=min(top_k, 20), gaian_slug=gaian_slug)
    return {
        "results": hits,
        "count": len(hits),
        "chroma_available": True,
        "chroma_total": chroma.count(),
    }


@router.put("/{memory_id}")
def memory_edit(memory_id: str, new_content: str):
    """Edit the content of a governed memory entry."""
    if not new_content.strip():
        raise HTTPException(status_code=422, detail="new_content must not be empty")
    store = get_memory_store()
    ok = store.edit(memory_id, new_content.strip())
    if not ok:
        raise HTTPException(
            status_code=404,
            detail=f"Memory '{memory_id}' not found, deleted, or frozen.",
        )
    chroma = get_chroma()
    chroma.store(text=new_content.strip(), memory_id=memory_id, source="explicit")
    return {"status": "updated", "id": memory_id}


@router.delete("/{memory_id}")
def memory_delete(memory_id: str):
    """Soft-delete a governed memory. Also removes from ChromaDB. C17 24h guarantee."""
    store = get_memory_store()
    ok = store.delete(memory_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail=f"Memory '{memory_id}' not found or already deleted.",
        )
    get_chroma().forget(memory_id)
    return {"status": "deleted", "id": memory_id}


@router.get("/audit")
def memory_audit():
    """Return the full immutable audit log."""
    store = get_memory_store()
    return store.get_audit_log()


@router.post("/{memory_id}/freeze")
def memory_freeze(memory_id: str):
    """Freeze a memory during an appeal review."""
    store = get_memory_store()
    ok = store.freeze(memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return {"status": "frozen", "id": memory_id}


@router.post("/{memory_id}/unfreeze")
def memory_unfreeze(memory_id: str):
    """Lift a freeze after appeal resolution."""
    store = get_memory_store()
    ok = store.unfreeze(memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return {"status": "unfrozen", "id": memory_id}
