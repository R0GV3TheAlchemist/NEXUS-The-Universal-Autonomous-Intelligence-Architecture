"""
pipeline.py
~~~~~~~~~~~
RAGPipeline: the single interface the agentic loop uses to ingest Canon
documents and retrieve context at reasoning time.

Changes in this revision (persistence)
---------------------------------------
* ingest_canon() now accepts store_path (Path | str | None).
  - If store_path is None  → in-memory index (previous behaviour, good
    for tests and ephemeral runs).
  - If store_path is given → opens a persistent SQLite index at that path.
    On warm start (fingerprint matches) the embed step is skipped entirely
    and the existing index is reused, saving minutes of startup time on a
    full Canon corpus.
* Fingerprint is computed from (canon_id, chunk_count) pairs via
  index_store.compute_fingerprint() and written to a sidecar .fingerprint
  file beside the SQLite db.
* Adds canon_store_path to status() report.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import List, Optional

from .chunker import Chunker, Chunk
from .embedder import Embedder
from .index import VectorIndex
from .retriever import Retriever

try:
    from .canon_loader import CanonLoader, CanonChunk
    _CANON_LOADER_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CANON_LOADER_AVAILABLE = False

try:
    from .index_store import IndexStore, default_store, compute_fingerprint, fingerprints_match
    _STORE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _STORE_AVAILABLE = False

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Orchestrates: ingest → embed → index → retrieve.

    Typical lifecycle
    -----------------
    1. Instantiate once per GAIA session.
    2. Call ingest_canon(store_path=...) at startup.
       - Cold start: fetches Canon, embeds all chunks, writes SQLite + fingerprint.
       - Warm start: fingerprint matches → opens existing SQLite, skips embedding.
    3. Call retrieve(query) from _reason() for every planning step.
    """

    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        index: Optional[VectorIndex] = None,
        retriever: Optional[Retriever] = None,
        chunker: Optional[Chunker] = None,
        top_k: int = 5,
    ) -> None:
        self._embedder: Embedder = embedder or Embedder()
        self._index: VectorIndex = index or VectorIndex()  # in-memory default
        self._retriever: Retriever = retriever or Retriever(
            index=self._index, embedder=self._embedder, top_k=top_k
        )
        self._chunker: Chunker = chunker or Chunker()
        self._top_k = top_k

        # Canon state
        self.canon_loaded: bool = False
        self._canon_doc_count: int = 0
        self._canon_chunk_count: int = 0
        self._ingest_duration_s: float = 0.0
        self._canon_store_path: Optional[str] = None
        self._canon_fingerprint: Optional[str] = None
        self._warm_start: bool = False  # True if we reused an existing index

    # ------------------------------------------------------------------
    # Canon ingestion (with persistence)
    # ------------------------------------------------------------------

    def ingest_canon(
        self,
        loader: Optional["CanonLoader"] = None,
        ref: str = "feat/obs-rag",
        force: bool = False,
        store_path: Optional[Path | str] = None,
    ) -> dict:
        """
        Load all Canon documents and index them.

        Parameters
        ----------
        loader     : CanonLoader, optional.  Supply a pre-built loader
                     (useful for testing with a mock).  If None, a new
                     CanonLoader is created.
        ref        : Git ref to load Canon from.  Defaults to feat/obs-rag.
        force      : Re-ingest even if already loaded / fingerprint matches.
        store_path : Path to persist the SQLite index, e.g.
                     Path.home() / ".gaia" / "data".  If None the index
                     lives in memory only (previous behaviour).

        Returns
        -------
        dict
            Ingestion report: doc_count, chunk_count, duration_s,
            status, warm_start, store_path.
        """
        if self.canon_loaded and not force:
            return self._ingest_report("already_loaded")

        if not _CANON_LOADER_AVAILABLE:
            logger.error("pipeline.ingest_canon: canon_loader module not available")
            return self._ingest_report("error_no_loader")

        try:
            # Resolve store
            store: Optional[IndexStore] = None
            if store_path is not None and _STORE_AVAILABLE:
                store = IndexStore(data_dir=Path(store_path))
                self._canon_store_path = str(store.db_path)

            # Build loader
            if loader is None:
                loader = CanonLoader(ref=ref)

            t0 = time.monotonic()

            # -------------------------------------------------------
            # Warm-start check: if we have a persistent index whose
            # fingerprint matches the current Canon corpus, skip the
            # expensive embed-and-insert phase entirely.
            # -------------------------------------------------------
            if store is not None and store.db_exists() and not force:
                # We need the chunks only to compute the fingerprint.
                # load_all() is cached after the first call, so this is
                # cheap on second ingest_canon() calls within a session.
                chunks: List[CanonChunk] = loader.load_all()
                if chunks and fingerprints_match(chunks, store):
                    # Swap in the persistent index, wire up retriever
                    self._index = VectorIndex.from_store(store, embedder=self._embedder)
                    self._retriever = Retriever(
                        index=self._index,
                        embedder=self._embedder,
                        top_k=self._top_k,
                    )
                    self._warm_start = True
                    self._canon_chunk_count = len(chunks)
                    self._canon_doc_count = len(loader.sources())
                    self._ingest_duration_s = time.monotonic() - t0
                    self.canon_loaded = True
                    logger.info(
                        "pipeline.ingest_canon: warm start — reusing persisted index "
                        "(%d chunks, fingerprint match) in %.3fs",
                        self._canon_chunk_count,
                        self._ingest_duration_s,
                    )
                    return self._ingest_report("warm_start")

            # -------------------------------------------------------
            # Cold start: fetch, embed, persist.
            # -------------------------------------------------------
            chunks = loader.load_all(force=force)
            if not chunks:
                logger.warning("pipeline.ingest_canon: loader returned 0 chunks")
                return self._ingest_report("error_empty_corpus")

            # Convert CanonChunks → generic Chunks
            generic_chunks = [
                Chunk(
                    text=c.text,
                    metadata={
                        "canon_id": c.canon_id,
                        "source": c.source,
                        "chunk_index": c.chunk_index,
                        "uid": c.uid,
                        **c.metadata,
                    },
                )
                for c in chunks
            ]

            # Open persistent index (or keep in-memory)
            if store is not None:
                if force:
                    store.delete_db()  # wipe stale index before rebuild
                self._index = VectorIndex.from_store(store, embedder=self._embedder)
                self._retriever = Retriever(
                    index=self._index,
                    embedder=self._embedder,
                    top_k=self._top_k,
                )

            self._index.add(generic_chunks, embedder=self._embedder)

            # Write fingerprint sidecar
            if store is not None and _STORE_AVAILABLE:
                digest = compute_fingerprint(chunks)
                store.write_fingerprint(digest)
                self._canon_fingerprint = digest
                logger.info(
                    "pipeline.ingest_canon: fingerprint written — %s", digest[:16]
                )

            elapsed = time.monotonic() - t0
            self._canon_chunk_count = len(chunks)
            self._canon_doc_count = len(loader.sources())
            self._ingest_duration_s = elapsed
            self._warm_start = False
            self.canon_loaded = True

            logger.info(
                "pipeline.ingest_canon: cold start — indexed %d chunks from %d Canon docs "
                "in %.2fs (store=%s)",
                self._canon_chunk_count,
                self._canon_doc_count,
                elapsed,
                self._canon_store_path or "memory",
            )
            return self._ingest_report("ok")

        except Exception as exc:  # noqa: BLE001
            logger.exception("pipeline.ingest_canon: unexpected error — %s", exc)
            return self._ingest_report("error_exception")

    def _ingest_report(self, status: str) -> dict:
        return {
            "status": status,
            "canon_loaded": self.canon_loaded,
            "warm_start": self._warm_start,
            "doc_count": self._canon_doc_count,
            "chunk_count": self._canon_chunk_count,
            "duration_s": round(self._ingest_duration_s, 3),
            "store_path": self._canon_store_path,
            "fingerprint": (self._canon_fingerprint or "")[:16] or None,
        }

    # ------------------------------------------------------------------
    # Standard ingest (non-Canon documents)
    # ------------------------------------------------------------------

    def ingest(self, text: str, metadata: Optional[dict] = None) -> int:
        """
        Chunk, embed, and index an arbitrary document.
        Returns the number of chunks added.
        """
        try:
            chunks = self._chunker.split(text, metadata=metadata or {})
            if not chunks:
                return 0
            self._index.add(chunks, embedder=self._embedder)
            return len(chunks)
        except Exception as exc:  # noqa: BLE001
            logger.exception("pipeline.ingest: error — %s", exc)
            return 0

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: Optional[int] = None) -> str:
        """
        Return the top-K most relevant Canon passages for *query*.

        Each passage is prefixed with its [Canon: <canon_id>] citation
        header so the planner always knows provenance.

        Returns an empty string if the index is empty or query is blank.
        """
        if not query or not query.strip():
            logger.debug("pipeline.retrieve: empty query, returning empty context")
            return ""

        try:
            results = self._retriever.retrieve(
                query=query,
                top_k=top_k or self._top_k,
            )
            if not results:
                return ""

            blocks = []
            for r in results:
                canon_id = r.metadata.get("canon_id", "Unknown")
                header = f"[Canon: {canon_id}]"
                blocks.append(f"{header}\n{r.text}")

            return "\n\n---\n\n".join(blocks)

        except Exception as exc:  # noqa: BLE001
            logger.exception("pipeline.retrieve: error — %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def status(self) -> dict:
        return {
            "canon_loaded": self.canon_loaded,
            "warm_start": self._warm_start,
            "canon_doc_count": self._canon_doc_count,
            "canon_chunk_count": self._canon_chunk_count,
            "index_size": self._index.size(),
            "top_k": self._top_k,
            "store_path": self._canon_store_path,
            "fingerprint": (self._canon_fingerprint or "")[:16] or None,
        }
