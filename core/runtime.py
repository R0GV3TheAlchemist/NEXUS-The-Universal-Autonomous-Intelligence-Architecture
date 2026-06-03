"""
core.runtime
============
GAIA singleton runtime — owns long-lived resources (MemoryStore, pruner, …)
that must be shared across all FastAPI request handlers.

Usage (in any router)
---------------------
    from core.runtime import get_runtime

    rt = get_runtime()           # raises RuntimeError if not initialised
    store = rt.memory_store      # MemoryStore instance

Initialisation (in main.py lifespan)
-------------------------------------
    from core.runtime import GAIARuntime
    runtime = GAIARuntime()
    runtime.init()
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

log = logging.getLogger("gaia.runtime")

# ---------------------------------------------------------------------------
# Singleton holder
# ---------------------------------------------------------------------------

_runtime: Optional["GAIARuntime"] = None


def get_runtime() -> "GAIARuntime":
    """Return the initialised GAIARuntime singleton."""
    if _runtime is None or not _runtime.ready:
        raise RuntimeError(
            "GAIARuntime is not initialised. "
            "Call GAIARuntime().init() during application lifespan."
        )
    return _runtime


# ---------------------------------------------------------------------------
# Runtime class
# ---------------------------------------------------------------------------

class GAIARuntime:
    """
    Central resource manager for the GAIA sidecar process.

    Owns:
      - MemoryStore   (SQLite + sqlite-vec)
      - MemoryPruner  (background eviction)

    Environment variables
    ---------------------
    GAIA_EMBEDDER            : 'sentence' (default) | 'ollama' | 'openai' | 'fallback'
    GAIA_DB_PATH             : path to SQLite DB  (default: data/gaia_memory.db)
    GAIA_MEMORY_CAPACITY     : int, soft row cap  (default: 100000)
    GAIA_ALLOW_HASH_FALLBACK : set to '1' to permit FallbackEmbedder (dev/CI only).
                               If unset, a missing sentence-transformers installation
                               raises RuntimeError at startup instead of silently
                               degrading to hash-based vectors.
    OLLAMA_BASE_URL          : base URL for Ollama (default: http://localhost:11434)
    OLLAMA_EMBED_MODEL       : model name         (default: nomic-embed-text)
    OPENAI_API_KEY           : required for openai embedder
    OPENAI_EMBED_MODEL       : model name         (default: text-embedding-3-small)
    SENTENCE_EMBED_MODEL     : sentence-transformers model (default: all-MiniLM-L6-v2)
    """

    def __init__(self) -> None:
        self._store: Optional[object]  = None
        self._pruner: Optional[object] = None
        self.ready: bool = False

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def init(self) -> None:
        """Initialise all subsystems.  Call once during FastAPI lifespan."""
        global _runtime

        embedder = self._build_embedder()

        db_path  = Path(
            os.environ.get("GAIA_DB_PATH", "data/gaia_memory.db")
        )
        capacity = int(os.environ.get("GAIA_MEMORY_CAPACITY", "100000"))

        from core.memory import MemoryStore, MemoryPruner
        self._store  = MemoryStore(db_path=db_path, embedder=embedder, capacity=capacity)
        self._pruner = MemoryPruner(self._store, capacity=capacity)

        self.ready = True
        _runtime = self

        log.info(
            "GAIARuntime ready — embedder=%s  db=%s  capacity=%d",
            os.environ.get("GAIA_EMBEDDER", "sentence"), db_path, capacity,
        )

    def shutdown(self) -> None:
        """Release resources.  Call during FastAPI lifespan teardown."""
        if self._store is not None:
            try:
                self._store.close()  # type: ignore[attr-defined]
            except Exception as exc:
                log.warning("GAIARuntime.shutdown: store.close() raised %s", exc)
        self.ready = False
        log.info("GAIARuntime shut down.")

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def memory_store(self):
        """The live MemoryStore instance."""
        if self._store is None:
            raise RuntimeError("MemoryStore not initialised.")
        return self._store

    @property
    def memory_pruner(self):
        """The live MemoryPruner instance."""
        if self._pruner is None:
            raise RuntimeError("MemoryPruner not initialised.")
        return self._pruner

    # -----------------------------------------------------------------------
    # Embedder factory
    # -----------------------------------------------------------------------

    @staticmethod
    def _allow_hash_fallback() -> bool:
        """Return True only when the operator has explicitly opted in.

        Set ``GAIA_ALLOW_HASH_FALLBACK=1`` in your environment to permit
        FallbackEmbedder (hash-only vectors).  This flag MUST NOT be set
        in production — it exists solely for local dev and CI pipelines
        that run without sentence-transformers installed.
        """
        return os.environ.get("GAIA_ALLOW_HASH_FALLBACK", "").strip() == "1"

    def _build_sentence_embedder(self):
        """Construct a SentenceTransformerEmbedder, or fail loudly.

        Unlike the old inline try/except, this helper surfaces a
        *RuntimeError* at startup when sentence-transformers is absent
        and the hash-fallback guard is not set.  That makes the
        misconfiguration visible immediately rather than at query time
        when wrong vectors are silently stored.

        If ``GAIA_ALLOW_HASH_FALLBACK=1`` is set (dev/CI only), the
        FallbackEmbedder is returned instead with an explicit WARNING.
        """
        try:
            from core.memory import SentenceTransformerEmbedder
            model = os.environ.get("SENTENCE_EMBED_MODEL", "all-MiniLM-L6-v2")
            log.info(
                "Embedder: SentenceTransformerEmbedder  model=%s", model
            )
            return SentenceTransformerEmbedder(model_name=model)
        except ImportError as exc:
            if self._allow_hash_fallback():
                from core.memory import FallbackEmbedder
                log.warning(
                    "sentence-transformers not installed — using FallbackEmbedder "
                    "(GAIA_ALLOW_HASH_FALLBACK=1 is set).  "
                    "Vectors carry NO semantic meaning.  "
                    "Install sentence-transformers before deploying: "
                    "pip install sentence-transformers"
                )
                return FallbackEmbedder()
            raise RuntimeError(
                "sentence-transformers is required for the default 'sentence' embedder "
                "but is not installed.\n"
                "Fix one of the following:\n"
                "  1. pip install sentence-transformers          (recommended)\n"
                "  2. export GAIA_EMBEDDER=ollama               (local Ollama daemon)\n"
                "  3. export GAIA_EMBEDDER=openai               (OpenAI API key required)\n"
                "  4. export GAIA_ALLOW_HASH_FALLBACK=1         "
                "(dev/CI only — vectors have NO semantic meaning)"
            ) from exc

    def _build_embedder(self):
        """Select and construct the configured embedding backend.

        Resolution order
        ----------------
        GAIA_EMBEDDER=ollama    → OllamaEmbedder
        GAIA_EMBEDDER=openai    → OpenAIEmbedder  (falls back to sentence if
                                                   OPENAI_API_KEY is unset)
        GAIA_EMBEDDER=fallback  → FallbackEmbedder  (requires
                                                     GAIA_ALLOW_HASH_FALLBACK=1)
        GAIA_EMBEDDER=sentence  → SentenceTransformerEmbedder  (default)
        <unset>                 → same as 'sentence'
        """
        backend = os.environ.get("GAIA_EMBEDDER", "sentence").lower().strip()

        # ── Ollama ──────────────────────────────────────────────────────────
        if backend == "ollama":
            from core.memory import OllamaEmbedder
            model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
            base  = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            log.info("Embedder: OllamaEmbedder  model=%s", model)
            return OllamaEmbedder(model=model, base_url=base)

        # ── OpenAI ──────────────────────────────────────────────────────────
        if backend == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
            model   = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
            if not api_key:
                log.warning(
                    "GAIA_EMBEDDER=openai but OPENAI_API_KEY is not set — "
                    "falling back to SentenceTransformerEmbedder."
                )
                return self._build_sentence_embedder()
            from core.memory import OpenAIEmbedder
            log.info("Embedder: OpenAIEmbedder  model=%s", model)
            return OpenAIEmbedder(api_key=api_key, model=model)

        # ── Explicit hash fallback (dev/CI only) ─────────────────────────
        if backend == "fallback":
            if not self._allow_hash_fallback():
                raise RuntimeError(
                    "GAIA_EMBEDDER=fallback is set but GAIA_ALLOW_HASH_FALLBACK=1 "
                    "is not.\n"
                    "FallbackEmbedder produces hash-only vectors with NO semantic "
                    "meaning and MUST NOT run in production.\n"
                    "Set GAIA_ALLOW_HASH_FALLBACK=1 explicitly if you intend to use "
                    "it in a dev or CI environment."
                )
            from core.memory import FallbackEmbedder
            log.warning(
                "Embedder: FallbackEmbedder (hash-only — not for production!)"
            )
            return FallbackEmbedder()

        # ── Default: sovereign offline sentence-transformers ─────────────
        return self._build_sentence_embedder()
