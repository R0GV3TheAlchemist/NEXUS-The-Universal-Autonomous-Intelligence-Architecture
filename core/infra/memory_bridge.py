"""
core/infra/memory_bridge.py

Memory Unification Bridge — C-TODAY Sprint, Task 2
===================================================

Provides drop-in replacements for the legacy core/memory_chroma.py
convenience helpers (recall_for_prompt, store_turn) that route through
the authoritative Phase-3 MemoryStore (core/memory/store.py) instead
of the ChromaDB singleton.

Why this exists
---------------
Before this bridge, chat.py called two separate memory systems on every
turn:

  1. core/memory/memory_chroma.py  (ChromaDB, legacy, sentence-transformers)
  2. core/memory/store.py          (SQLite + sqlite-vec, Phase 3, full audit)

Both systems wrote independently and read independently — memories stored
by the runtime were never retrieved by the router, and vice versa.

After this bridge, all recall and storage flows through a single source
of truth: the MemoryStore instance that lives inside the GAIANRuntime for
the relevant slug. ChromaDB is retained as a graceful fallback only —
it activates if no runtime is registered for the requested slug (e.g.
anonymous /query/stream calls without a GAIAN).

API contract (identical to core/memory/memory_chroma.py helpers)
---------------------------------------------------------------
  recall_for_prompt(query, gaian_slug, top_k=5) -> list[str]
  store_turn(user_message, gaian_response, gaian_slug,
             session_id="", emotion="neutral")  -> None

Canon Ref: C17 (Persistent Memory and Identity Architecture)
"""

from __future__ import annotations

import logging

from core.memory.taxonomy import MemoryKind, MemoryTier

log = logging.getLogger(__name__)

# Importance scores assigned to each fragment type
_IMPORTANCE_USER_MSG  = 0.55
_IMPORTANCE_GAIAN_RSP = 0.60   # GAIAN responses are slightly more important
                                # for future recall — they carry synthesised insight


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_memory_store(gaian_slug: str):
    """
    Return the MemoryStore instance from the live GAIANRuntime for *gaian_slug*.
    Returns None if the runtime is not yet registered (fallback to ChromaDB).
    Deferred import avoids circular dependency at module load time.
    """
    try:
        from core.infra.server_state import _RUNTIME_REGISTRY
        rt = _RUNTIME_REGISTRY.get(gaian_slug)
        if rt is not None:
            store = getattr(rt, "_memory_store", None)
            if store is not None:
                return store
    except Exception as exc:
        log.debug("[MemoryBridge] Could not access runtime registry: %s", exc)
    return None


def _chroma_fallback_recall(query: str, gaian_slug: str, top_k: int) -> list[str]:
    """Fall back to ChromaDB recall when no runtime MemoryStore is available."""
    try:
        from core.memory.memory_chroma import recall_for_prompt as _chroma_recall
        return _chroma_recall(query=query, gaian_slug=gaian_slug, top_k=top_k)
    except Exception as exc:
        log.debug("[MemoryBridge] ChromaDB fallback recall failed: %s", exc)
        return []


def _chroma_fallback_store(
    user_message: str,
    gaian_response: str,
    gaian_slug: str,
    session_id: str,
    emotion: str,
) -> None:
    """Fall back to ChromaDB store when no runtime MemoryStore is available."""
    try:
        from core.memory.memory_chroma import store_turn as _chroma_store
        _chroma_store(
            user_message=user_message,
            gaian_response=gaian_response,
            gaian_slug=gaian_slug,
            session_id=session_id,
            emotion=emotion,
        )
    except Exception as exc:
        log.debug("[MemoryBridge] ChromaDB fallback store failed: %s", exc)


# ---------------------------------------------------------------------------
# Public API — drop-in replacements for core/memory/memory_chroma.py helpers
# ---------------------------------------------------------------------------

def recall_for_prompt(
    query: str,
    gaian_slug: str,
    top_k: int = 5,
) -> list[str]:
    """
    Return a list of plain-text memory snippets for injection into an
    LLM system prompt.

    Routes through the GAIANRuntime's MemoryStore (SQLite + sqlite-vec)
    for the richest, most semantically accurate recall.  Falls back to
    ChromaDB if the runtime is not yet registered.

    Return type is identical to core/memory/memory_chroma.recall_for_prompt.
    """
    store = _get_memory_store(gaian_slug)

    if store is not None:
        try:
            items = store.retrieve_sync(
                user_id=gaian_slug,
                query=query,
                top_k=top_k,
                kinds=[MemoryKind.MESSAGE, MemoryKind.REFLECTION, MemoryKind.FACT],
            )
            snippets = [item.text for item in items if item.text.strip()]
            log.debug(
                "[MemoryBridge] MemoryStore recalled %d items for slug='%s'",
                len(snippets), gaian_slug,
            )
            return snippets
        except Exception as exc:
            log.warning(
                "[MemoryBridge] MemoryStore recall failed for slug='%s', "
                "falling back to ChromaDB: %s", gaian_slug, exc,
            )

    # Fallback
    snippets = _chroma_fallback_recall(query=query, gaian_slug=gaian_slug, top_k=top_k)
    log.debug(
        "[MemoryBridge] ChromaDB fallback recalled %d items for slug='%s'",
        len(snippets), gaian_slug,
    )
    return snippets


def store_turn(
    user_message: str,
    gaian_response: str,
    gaian_slug: str,
    session_id: str = "",
    emotion: str = "neutral",
) -> None:
    """
    Persist both sides of a conversation turn into the authoritative
    MemoryStore for this GAIAN.

    Stores two MemoryItems:
      - The user message  (kind=MESSAGE, tier=SHORT_TERM, role='user')
      - The GAIAN response (kind=MESSAGE, tier=SHORT_TERM, role='assistant')

    Falls back to ChromaDB if the runtime MemoryStore is unavailable.
    This is a no-op on any exception — memory persistence must never
    crash the response path.
    """
    store = _get_memory_store(gaian_slug)

    if store is not None:
        try:
            store.remember_sync(
                user_id=gaian_slug,
                text=f"User said: {user_message}",
                role="user",
                kind=MemoryKind.MESSAGE,
                tier=MemoryTier.SHORT_TERM,
                importance=_IMPORTANCE_USER_MSG,
                session_id=session_id or None,
                metadata={"emotion": emotion, "source": "conversation"},
            )
            store.remember_sync(
                user_id=gaian_slug,
                text=f"{gaian_slug.upper()} responded: {gaian_response}",
                role="assistant",
                kind=MemoryKind.MESSAGE,
                tier=MemoryTier.SHORT_TERM,
                importance=_IMPORTANCE_GAIAN_RSP,
                session_id=session_id or None,
                metadata={"emotion": emotion, "source": "conversation"},
            )
            log.debug(
                "[MemoryBridge] Stored turn in MemoryStore for slug='%s'", gaian_slug
            )
            return
        except Exception as exc:
            log.warning(
                "[MemoryBridge] MemoryStore store_turn failed for slug='%s', "
                "falling back to ChromaDB: %s", gaian_slug, exc,
            )

    # Fallback
    _chroma_fallback_store(
        user_message=user_message,
        gaian_response=gaian_response,
        gaian_slug=gaian_slug,
        session_id=session_id,
        emotion=emotion,
    )
