"""
core/infra/memory_consolidation.py

Memory tier promotion: SHORT_TERM → LONG_TERM.

Runs as a recurring scheduler task.  After each pass it re-submits
itself so the loop continues without external orchestration.

Promotion criteria:
  - MemoryTier.SHORT_TERM items
  - older than CONSOLIDATION_AGE_HOURS (default 1 h)
  - importance >= CONSOLIDATION_MIN_IMPORTANCE (default 0.5)
  - kind in CONSOLIDATION_KINDS (MESSAGE, REFLECTION, FACT)

After promotion in SQLite the item is upserted into the Gaian’s
ChromaDB collection so POST /memory/context can retrieve it via
vector search on future turns.

The consolidation task is submitted once at session start by calling
schedule_consolidation(rt, user_id) from the chat router.
Subsequent passes self-reschedule via the on_success callback.

Canon: C17 (Memory), Doc 21 (Sovereignty)
"""

from __future__ import annotations

import logging
import time
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONSOLIDATION_AGE_HOURS      = 1.0        # promote items older than this
CONSOLIDATION_MIN_IMPORTANCE = 0.5        # minimum importance to promote
CONSOLIDATION_INTERVAL_S     = 3600.0     # re-run every hour
CONSOLIDATION_KINDS          = {"message", "reflection", "fact"}


# ---------------------------------------------------------------------------
# ChromaDB upsert helpers
# ---------------------------------------------------------------------------

def _get_chroma_collection(gaian_slug: str):
    """
    Return the ChromaDB collection for *gaian_slug*, or None if ChromaDB
    is unavailable.  Collection name mirrors the convention used by
    core/memory/memory_chroma.py: f"gaian_{gaian_slug}".
    """
    try:
        from core.memory.memory_store import get_memory_store
        ms = get_memory_store()
        client = getattr(ms, "_chroma_client", None)
        if client is None:
            # Try the module-level singleton used by memory_chroma.py
            import chromadb
            from core.config import settings
            client = chromadb.HttpClient(
                host=getattr(settings, "CHROMA_HOST", "localhost"),
                port=int(getattr(settings, "CHROMA_PORT", 8000)),
            )
        collection_name = f"gaian_{gaian_slug}"
        return client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as exc:
        log.debug("[Consolidation] ChromaDB collection unavailable: %s", exc)
        return None


def _embed_texts(texts: list[str]) -> list[list[float]] | None:
    """
    Embed a list of texts using the same model as memory_chroma.py
    (sentence-transformers all-MiniLM-L6-v2).
    Returns None if the embedding model is unavailable.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    except Exception as exc:
        log.debug("[Consolidation] Embedding model unavailable: %s", exc)
        return None


def _chroma_upsert_batch(
    items: list[Any],
    gaian_slug: str,
    summary: dict,
) -> None:
    """
    Upsert a batch of promoted MemoryItems into the Gaian’s ChromaDB
    collection.

    Document IDs use the pattern 'mem:{item.id}' to avoid collisions
    with other collection entries.

    Metadata stored per document (all fields the /memory/context
    ranking formula reads):
      - gaian_slug, kind, importance, session_id, emotion, timestamp

    Failure is non-fatal — promotion in SQLite is the source of truth.
    summary['chroma_upserted'] and summary['chroma_errors'] are updated
    in-place.
    """
    if not items:
        return

    collection = _get_chroma_collection(gaian_slug)
    if collection is None:
        # ChromaDB offline — skip silently, items remain in SQLite
        log.debug(
            "[Consolidation] ChromaDB unavailable — skipping upsert for %d items",
            len(items),
        )
        return

    texts = [getattr(item, "text", "") or "" for item in items]
    embeddings = _embed_texts(texts)

    ids: list[str]       = []
    documents: list[str] = []
    metadatas: list[dict] = []
    embed_list: list[list[float]] = []

    for idx, item in enumerate(items):
        item_id    = str(getattr(item, "id", f"{gaian_slug}_{idx}"))
        text       = texts[idx]
        kind       = str(getattr(item, "kind", "message")).lower()
        importance = float(getattr(item, "importance", 0.5))
        session_id = str(getattr(item, "session_id", "") or "")
        metadata   = getattr(item, "metadata", {}) or {}
        emotion    = str(metadata.get("emotion", "neutral"))

        # Derive timestamp — prefer created_at, fall back to now
        created_at = getattr(item, "created_at", None)
        if created_at is not None:
            ts = created_at.timestamp() if hasattr(created_at, "timestamp") else float(created_at)
        else:
            ts = time.time()

        ids.append(f"mem:{item_id}")
        documents.append(text)
        metadatas.append({
            "gaian_slug":  gaian_slug,
            "kind":        kind,
            "importance":  importance,
            "session_id":  session_id,
            "emotion":     emotion,
            "timestamp":   ts,
            "tier":        "LONG_TERM",
            "source":      "consolidation",
        })
        if embeddings is not None:
            embed_list.append(embeddings[idx])

    try:
        upsert_kwargs: dict = {
            "ids":       ids,
            "documents": documents,
            "metadatas": metadatas,
        }
        if embed_list:
            upsert_kwargs["embeddings"] = embed_list
        # When no embeddings are provided ChromaDB uses its built-in
        # embedding function (if configured on the collection).
        collection.upsert(**upsert_kwargs)
        summary["chroma_upserted"] = summary.get("chroma_upserted", 0) + len(ids)
        log.info(
            "[Consolidation] ChromaDB upsert: %d fragments → collection='gaian_%s'",
            len(ids), gaian_slug,
        )
    except Exception as exc:
        summary["chroma_errors"] = summary.get("chroma_errors", 0) + len(ids)
        log.warning(
            "[Consolidation] ChromaDB batch upsert failed for slug='%s': %s",
            gaian_slug, exc,
        )


# ---------------------------------------------------------------------------
# Consolidation coroutine
# ---------------------------------------------------------------------------

async def consolidate_memory(store: Any, user_id: str, gaian_slug: str = "") -> dict:
    """
    Promote eligible SHORT_TERM memory items to LONG_TERM in SQLite,
    then upsert the promoted items into ChromaDB.

    Uses the MemoryStore’s existing retrieve + update_tier interface.
    Falls back gracefully if the store doesn’t support tier promotion
    (older schema versions).

    Returns a summary dict with keys:
      scanned, promoted, skipped, errors, chroma_upserted, chroma_errors.
    """
    import asyncio

    summary: dict = {
        "scanned":         0,
        "promoted":        0,
        "skipped":         0,
        "errors":          0,
        "chroma_upserted": 0,
        "chroma_errors":   0,
    }
    cutoff_ts = time.time() - (CONSOLIDATION_AGE_HOURS * 3600)
    promoted_items: list[Any] = []  # collect for batch ChromaDB upsert

    # retrieve_sync is available on all MemoryStore versions
    try:
        candidates = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: store.retrieve_sync(
                query="",
                user_id=user_id,
                top_k=200,
                tier="SHORT_TERM",
            ),
        )
    except TypeError:
        # Older MemoryStore doesn’t accept tier kwarg — retrieve all and filter
        candidates = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: store.retrieve_sync(query="", user_id=user_id, top_k=200),
        )

    for item in candidates:
        summary["scanned"] += 1
        tier = getattr(item, "tier", None)
        if tier is not None and str(tier).upper() not in ("SHORT_TERM", "SHORT"):
            summary["skipped"] += 1
            continue

        kind = str(getattr(item, "kind", "")).lower()
        if kind not in CONSOLIDATION_KINDS:
            summary["skipped"] += 1
            continue

        importance = float(getattr(item, "importance", 0.0))
        if importance < CONSOLIDATION_MIN_IMPORTANCE:
            summary["skipped"] += 1
            continue

        created_ts = getattr(item, "created_at", None)
        if created_ts is not None:
            ts = created_ts.timestamp() if hasattr(created_ts, "timestamp") else float(created_ts)
            if ts > cutoff_ts:
                summary["skipped"] += 1
                continue

        # ── Tier promotion in SQLite ────────────────────────────────────────
        try:
            if hasattr(store, "update_tier"):
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda i=item: store.update_tier(i.id, "LONG_TERM"),
                )
                summary["promoted"] += 1
                promoted_items.append(item)  # queue for ChromaDB upsert
                log.debug(
                    "[Consolidation] promoted item id=%s kind=%s importance=%.2f",
                    getattr(item, "id", "?"), kind, importance,
                )
            else:
                log.debug(
                    "[Consolidation] MemoryStore has no update_tier — skipping"
                )
                summary["skipped"] += 1
        except Exception as exc:
            log.warning(
                "[Consolidation] promotion error for item=%s: %s",
                getattr(item, "id", "?"), exc,
            )
            summary["errors"] += 1

    # ── Batch ChromaDB upsert for all promoted items ──────────────────────
    # Runs synchronously but is fast (single network call per batch).
    # gaian_slug falls back to user_id when not explicitly provided
    # because the scheduler submits tasks with user_id=gaian_slug.
    slug = gaian_slug or user_id
    if promoted_items:
        _chroma_upsert_batch(promoted_items, slug, summary)

    log.info(
        "[Consolidation] user=%s scanned=%d promoted=%d skipped=%d "
        "errors=%d chroma_upserted=%d chroma_errors=%d",
        user_id,
        summary["scanned"],
        summary["promoted"],
        summary["skipped"],
        summary["errors"],
        summary["chroma_upserted"],
        summary["chroma_errors"],
    )
    return summary


# ---------------------------------------------------------------------------
# Scheduler submission
# ---------------------------------------------------------------------------

_CONSOLIDATION_REGISTERED: set[tuple] = set()


def schedule_consolidation(rt: Any, user_id: str) -> bool:
    """
    Submit a self-rescheduling memory consolidation task to rt._scheduler.

    Safe to call on every turn — only submits once per (runtime, user_id)
    pair per process lifetime.  Returns True if a new task was submitted.
    """
    key = (id(rt), user_id)
    if key in _CONSOLIDATION_REGISTERED:
        return False

    _CONSOLIDATION_REGISTERED.add(key)
    _submit_consolidation_task(rt, user_id)
    log.info("[Consolidation] scheduled recurring consolidation for user=%s", user_id)
    return True


def _submit_consolidation_task(rt: Any, user_id: str) -> None:
    """Submit one consolidation task.  The on_success callback re-submits it."""
    from core.planner.scheduler import Task
    import asyncio

    store      = rt._memory_store
    gaian_slug = getattr(rt, "slug", user_id)  # runtime always carries its slug

    async def _run():
        await asyncio.sleep(CONSOLIDATION_INTERVAL_S)
        return await consolidate_memory(store, user_id, gaian_slug=gaian_slug)

    async def _on_success(result):
        _submit_consolidation_task(rt, user_id)

    task = Task(
        name=f"memory:consolidation:{user_id}",
        coroutine=_run,
        priority=2,
        on_success=_on_success,
        ttl_seconds=None,
        max_retries=2,
        backoff_sec=60.0,
        context={"user_id": user_id, "gaian_slug": gaian_slug, "type": "memory_consolidation"},
    )
    rt._scheduler.submit(task)
