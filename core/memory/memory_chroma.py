"""
core/memory/memory_chroma.py
(formerly core/memory_chroma.py — Phase C physical migration)

ChromaDB-backed semantic memory layer for GAIA.

Sits alongside the C17-governed MemoryStore (JSON, full audit, GDPR).
This layer adds:
  - Embedding + vector similarity recall (top-k)
  - Auto-store after every conversation turn
  - LLM system-prompt injection of recalled context

Falls back gracefully if ChromaDB is not installed — all calls
become no-ops so the rest of the server is unaffected.

Canon Ref: C17 (Persistent Memory and Identity Architecture)
"""

from __future__ import annotations

import datetime
import os
import pathlib
from typing import Optional

# ---------------------------------------------------------------------------
# Optional ChromaDB import — graceful degradation
# ---------------------------------------------------------------------------

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False


# ---------------------------------------------------------------------------
# Storage path
# ---------------------------------------------------------------------------

def _chroma_path() -> pathlib.Path:
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home() / "AppData" / "Roaming"))
    else:
        base = pathlib.Path(os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local" / "share"))
    return base / "GAIA" / "chroma"


# ---------------------------------------------------------------------------
# ChromaMemory
# ---------------------------------------------------------------------------

class ChromaMemory:
    """
    Thin wrapper around a ChromaDB persistent client.
    Uses the default all-MiniLM-L6-v2 embedding function (downloaded once,
    cached locally by chromadb's sentence-transformers integration).

    If ChromaDB is not installed, every method is a no-op and
    recall() always returns [].
    """

    COLLECTION_NAME = "gaia_episodic"

    def __init__(self, path: Optional[pathlib.Path] = None):
        self._path = path or _chroma_path()
        self._client = None
        self._collection = None
        self._ready = False
        if _CHROMA_AVAILABLE:
            self._init()

    def _init(self) -> None:
        try:
            self._path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(self._path),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            self._ready = True
        except Exception as e:
            # ChromaDB init failed — degrade gracefully
            self._ready = False
            import logging
            logging.getLogger(__name__).warning(f"ChromaDB init failed, semantic recall disabled: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        return self._ready

    def store(
        self,
        text: str,
        memory_id: str,
        source: str = "conversation",
        emotion: str = "neutral",
        gaian_slug: str = "gaia",
        session_id: str = "",
    ) -> bool:
        """
        Embed and store a memory fragment.
        Returns True on success, False if unavailable or on error.
        """
        if not self._ready or not text.strip():
            return False
        try:
            ts = datetime.datetime.utcnow().isoformat()
            self._collection.upsert(
                ids=[memory_id],
                documents=[text],
                metadatas=[{
                    "source":     source,
                    "emotion":    emotion,
                    "gaian":      gaian_slug,
                    "session_id": session_id,
                    "timestamp":  ts,
                }],
            )
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"ChromaDB store error: {e}")
            return False

    def recall(
        self,
        query: str,
        top_k: int = 5,
        gaian_slug: Optional[str] = None,
    ) -> list[dict]:
        """
        Semantic similarity search.
        Returns a list of dicts: {id, text, score, metadata}.
        Returns [] if unavailable or on error.
        """
        if not self._ready or not query.strip():
            return []
        try:
            where = {"gaian": gaian_slug} if gaian_slug else None
            results = self._collection.query(
                query_texts=[query],
                n_results=min(top_k, max(1, self._collection.count())),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            items = []
            for i, doc in enumerate(results["documents"][0]):
                dist = results["distances"][0][i]
                # cosine distance → similarity score 0-1
                score = round(1.0 - dist, 4)
                items.append({
                    "id":       results["ids"][0][i],
                    "text":     doc,
                    "score":    score,
                    "metadata": results["metadatas"][0][i],
                })
            # Sort descending by score
            items.sort(key=lambda x: x["score"], reverse=True)
            return items
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"ChromaDB recall error: {e}")
            return []

    def forget(self, memory_id: str) -> bool:
        """Remove a single memory by ID. Mirrors C17 deletion."""
        if not self._ready:
            return False
        try:
            self._collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False

    def count(self) -> int:
        if not self._ready:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_chroma: Optional[ChromaMemory] = None


def get_chroma() -> ChromaMemory:
    global _chroma
    if _chroma is None:
        _chroma = ChromaMemory()
    return _chroma


# ---------------------------------------------------------------------------
# Convenience helpers used by routers
# ---------------------------------------------------------------------------

def store_turn(
    user_message: str,
    gaian_response: str,
    gaian_slug: str,
    session_id: str = "",
    emotion: str = "neutral",
) -> None:
    """
    Auto-store a conversation turn as two memory fragments:
    one for the user message, one for the GAIAN response.
    Both are tagged source='conversation'.
    """
    chroma = get_chroma()
    if not chroma.available:
        return

    import hashlib
    import time
    base = f"{session_id}:{gaian_slug}:{time.time()}"

    uid_user = hashlib.sha256(f"user:{base}".encode()).hexdigest()[:16]
    chroma.store(
        text=f"User said: {user_message}",
        memory_id=uid_user,
        source="conversation",
        emotion=emotion,
        gaian_slug=gaian_slug,
        session_id=session_id,
    )

    uid_gaian = hashlib.sha256(f"gaian:{base}".encode()).hexdigest()[:16]
    chroma.store(
        text=f"{gaian_slug.upper()} responded: {gaian_response}",
        memory_id=uid_gaian,
        source="conversation",
        emotion=emotion,
        gaian_slug=gaian_slug,
        session_id=session_id,
    )


def recall_for_prompt(
    query: str,
    gaian_slug: str,
    top_k: int = 5,
) -> list[str]:
    """
    Return a list of plain-text memory snippets suitable for
    injection into an LLM system prompt.
    """
    chroma = get_chroma()
    hits = chroma.recall(query, top_k=top_k, gaian_slug=gaian_slug)
    return [h["text"] for h in hits if h["score"] > 0.20]
