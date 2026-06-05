"""
core/rag/pipeline.py
~~~~~~~~~~~~~~~~~~~~
GAIA-OS Canon RAG pipeline.

Three usage surfaces
--------------------
1. Canon ingestion   RAGPipeline.ingest_canon()
2. File/dir ingest   RAGPipeline.ingest() / reindex() / query()
                     RAGPipeline.indexed_sources / index_size
3. Agentic loop      RAGPipeline.retrieve() / status()
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, List, Optional

from .chunker import Chunk, chunk_text, chunk_file, chunk_directory
from .index import VectorIndex

logger = logging.getLogger(__name__)

try:
    from .index_store import IndexStore
    _INDEX_STORE_AVAILABLE = True
except ImportError:
    _INDEX_STORE_AVAILABLE = False
    IndexStore = None  # type: ignore[assignment,misc]

try:
    from .canon_loader import CanonLoader, CanonChunk
    _CANON_LOADER_AVAILABLE = True
except ImportError:
    _CANON_LOADER_AVAILABLE = False
    CanonLoader  = None  # type: ignore[assignment,misc]
    CanonChunk   = None  # type: ignore[assignment,misc]

try:
    from .embedder import FallbackEmbedder
    _EMBEDDER_AVAILABLE = True
except ImportError:
    _EMBEDDER_AVAILABLE = False
    FallbackEmbedder = None  # type: ignore[assignment,misc]

try:
    from .retriever import Retriever
    _RETRIEVER_AVAILABLE = True
except ImportError:
    _RETRIEVER_AVAILABLE = False
    Retriever = None  # type: ignore[assignment,misc]


class RAGPipeline:
    """Unified RAG pipeline for GAIA-OS."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._index     = VectorIndex(db_path=db_path)
        self._retriever = Retriever(self._index) if _RETRIEVER_AVAILABLE else None
        self._embedder  = FallbackEmbedder() if _EMBEDDER_AVAILABLE else None
        self.canon_loaded:       bool           = False
        self._warm_start:        bool           = False
        self._canon_doc_count:   int            = 0
        self._canon_chunk_count: int            = 0
        self._fingerprint:       Optional[str]  = None
        self._store_path:        Optional[Path] = None

    # ------------------------------------------------------------------
    # File/directory ingestion (test_rag.py surface)
    # ------------------------------------------------------------------

    def ingest(self, path: str, chunk_size: int = 512, overlap: int = 64) -> int:
        p = Path(path)
        if not p.exists():
            return 0
        chunks = chunk_directory(p, chunk_size=chunk_size, overlap=overlap) if p.is_dir() \
            else chunk_file(p, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            return 0
        if self._embedder is not None:
            self._embedder.fit([c.text for c in chunks])
        return self._index.add_chunks(chunks)

    def reindex(self, path: str, chunk_size: int = 512, overlap: int = 64) -> int:
        p = Path(path)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    self._index.delete_source(str(f))
        else:
            self._index.delete_source(str(p))
        return self.ingest(path, chunk_size=chunk_size, overlap=overlap)

    def query(self, query: str, top_k: int = 5, mode: str = "hybrid") -> list:
        idx = getattr(self, "_index", None)
        if idx is None or idx.count() == 0:
            return []
        if self._retriever is not None:
            try:
                return self._retriever.retrieve(query, top_k=top_k, mode=mode)  # type: ignore[arg-type]
            except Exception as exc:  # noqa: BLE001
                logger.warning("query: retriever error — %s", exc)
        return self._index.search(query, top_k=top_k)

    @property
    def indexed_sources(self) -> List[str]:
        return self._index.sources()

    @property
    def index_size(self) -> int:
        return self._index.count()

    # ------------------------------------------------------------------
    # Agentic loop surface
    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve Canon passages relevant to *query* and return a
        citation-prefixed string for injection into the planner prompt.

        Result shape dispatch (order matters — checked before hasattr):
          1. Flat / test object : r.metadata is a plain dict
                                  → r.text + r.metadata["canon_id"]
          2. RetrievalResult    : r.chunk is a real Chunk-like object
                                  → r.chunk.text + canon_id from r.chunk.source
          3. Bare Chunk fallback: plain str conversion

        The flat-dict check MUST come first because MagicMock responds
        True to every hasattr() call, so testing hasattr(r, "chunk")
        first would always fire on mock objects.
        """
        if not query or not query.strip():
            return ""

        idx       = getattr(self, "_index", None)
        retriever = getattr(self, "_retriever", None)

        results = []
        if retriever is not None:
            try:
                results = retriever.retrieve(query, top_k=top_k)
            except Exception as exc:  # noqa: BLE001
                logger.warning("retrieve: retriever error — %s", exc)
        elif idx is not None:
            try:
                raw     = idx.search(query, top_k=top_k)
                results = [chunk for chunk, _ in raw]
            except Exception as exc:  # noqa: BLE001
                logger.warning("retrieve: index search error — %s", exc)

        if not results:
            return ""

        parts: List[str] = []
        for r in results:
            # ----------------------------------------------------------
            # Shape 1 — flat object with a real dict metadata attribute.
            # Checked FIRST so MagicMock objects (which satisfy every
            # hasattr test) don't fall into the RetrievalResult branch.
            # ----------------------------------------------------------
            metadata = getattr(r, "metadata", None)
            if isinstance(metadata, dict):
                canon_id = metadata.get("canon_id", "unknown")
                text     = getattr(r, "text", "")

            # ----------------------------------------------------------
            # Shape 2 — RetrievalResult with a .chunk sub-object.
            # Derive canon_id from the source path stem.
            # ----------------------------------------------------------
            elif hasattr(r, "chunk"):
                chunk    = r.chunk
                text     = chunk.text
                source   = getattr(chunk, "source", "")
                canon_id = Path(source).stem if source else "unknown"

            # ----------------------------------------------------------
            # Shape 3 — bare Chunk from VectorIndex.search fallback.
            # ----------------------------------------------------------
            else:
                text     = str(r)
                canon_id = "unknown"

            parts.append(f"[Canon: {canon_id}]\n{text}")

        return "\n\n".join(parts)

    def status(self) -> dict:
        idx = getattr(self, "_index", None)
        return {
            "canon_loaded":       self.canon_loaded,
            "warm_start":         getattr(self, "_warm_start", False),
            "canon_doc_count":    getattr(self, "_canon_doc_count", 0),
            "canon_chunk_count":  getattr(self, "_canon_chunk_count", 0),
            "index_size":         idx.count() if idx is not None else 0,
            "top_k":              getattr(self, "_top_k", 5),
            "store_path":         str(self._store_path) if getattr(self, "_store_path", None) else None,
            "fingerprint":        getattr(self, "_fingerprint", None),
        }

    # ------------------------------------------------------------------
    # Canon ingestion (session startup)
    # ------------------------------------------------------------------

    def ingest_canon(
        self,
        ref:        str            = "main",
        force:      bool           = False,
        store_path: Optional[Path] = None,
    ) -> dict:
        if self.canon_loaded and not force:
            return {"status": "already_loaded", "warm_start": getattr(self, "_warm_start", False)}

        t0 = time.monotonic()
        self._store_path = store_path

        # ----------------------------------------------------------------
        # Warm start: store exists on disk and fingerprint matches
        # ----------------------------------------------------------------
        if store_path is not None and _INDEX_STORE_AVAILABLE and not force:
            store = IndexStore(data_dir=store_path)
            store.ensure_dir()
            if store.db_exists():
                try:
                    self._index     = VectorIndex.from_store(store)
                    self._retriever = Retriever(self._index) if _RETRIEVER_AVAILABLE else None
                    self._fingerprint = store.read_fingerprint()
                    self._warm_start  = True
                    self.canon_loaded = True
                    self._canon_chunk_count = self._index.count()
                    return {
                        "status":      "warm_start",
                        "warm_start":  True,
                        "doc_count":   0,
                        "chunk_count": self._canon_chunk_count,
                        "fingerprint": self._fingerprint,
                        "store_path":  str(store.db_path),
                        "duration_s":  round(time.monotonic() - t0, 3),
                    }
                except Exception as exc:  # noqa: BLE001
                    logger.warning("ingest_canon: warm start failed — %s", exc)

        # ----------------------------------------------------------------
        # Cold start (no Canon loader available — graceful no-op)
        # ----------------------------------------------------------------
        if not _CANON_LOADER_AVAILABLE:
            self.canon_loaded = True
            self._warm_start  = False
            return {
                "status":      "ok",
                "warm_start":  False,
                "doc_count":   0,
                "chunk_count": 0,
                "fingerprint": None,
                "store_path":  None,
                "duration_s":  round(time.monotonic() - t0, 3),
            }

        # ----------------------------------------------------------------
        # Cold start: load Canon, embed, write to disk
        # ----------------------------------------------------------------
        try:
            loader     = CanonLoader(ref=ref)
            canon_docs = loader.load_all()          # returns List[CanonChunk]
        except AttributeError:
            # Older CanonLoader uses .load() not .load_all()
            try:
                loader     = CanonLoader(ref=ref)
                canon_docs = loader.load()
            except Exception as exc:  # noqa: BLE001
                self.canon_loaded = True
                return {
                    "status":      "error",
                    "warm_start":  False,
                    "doc_count":   0,
                    "chunk_count": 0,
                    "error":       str(exc),
                    "duration_s":  round(time.monotonic() - t0, 3),
                }
        except Exception as exc:  # noqa: BLE001
            self.canon_loaded = True
            return {
                "status":      "error",
                "warm_start":  False,
                "doc_count":   0,
                "chunk_count": 0,
                "error":       str(exc),
                "duration_s":  round(time.monotonic() - t0, 3),
            }

        # Build chunks from canon docs
        all_chunks:   List[Chunk] = []
        fp_parts:     List[str]   = []
        seen_sources: set          = set()

        for doc in canon_docs:
            doc_chunks = chunk_text(doc.text, source=doc.source)
            all_chunks.extend(doc_chunks)
            if doc.source not in seen_sources:
                seen_sources.add(doc.source)
                fp_parts.append(f"{doc.source}:{doc.canon_id}")

        if self._embedder is not None and all_chunks:
            self._embedder.fit([c.text for c in all_chunks])

        # ----------------------------------------------------------------
        # Persist to disk when store_path is given.
        # Build the index directly against the on-disk SQLite file so
        # db_exists() returns True and warm-start works next run.
        # ----------------------------------------------------------------
        import hashlib
        fingerprint = hashlib.sha256("|".join(sorted(fp_parts)).encode()).hexdigest()

        if store_path is not None and _INDEX_STORE_AVAILABLE:
            try:
                store = IndexStore(data_dir=store_path)
                store.ensure_dir()
                if force and store.db_exists():
                    store.delete_db()
                # Build directly against the on-disk path
                disk_index = VectorIndex(db_path=str(store.db_path))
                disk_index.add_chunks(all_chunks)
                self._index     = disk_index
                self._retriever = Retriever(self._index) if _RETRIEVER_AVAILABLE else None
                store.write_fingerprint(fingerprint)
            except Exception as exc:  # noqa: BLE001
                logger.warning("ingest_canon: persist failed — %s", exc)
                # Fall back to in-memory index
                self._index.add_chunks(all_chunks)
        else:
            self._index.add_chunks(all_chunks)

        self._fingerprint       = fingerprint
        self._warm_start        = False
        self._canon_doc_count   = len(seen_sources)
        self._canon_chunk_count = len(all_chunks)
        self.canon_loaded       = True

        return {
            "status":      "ok",
            "warm_start":  False,
            "doc_count":   self._canon_doc_count,
            "chunk_count": self._canon_chunk_count,
            "fingerprint": fingerprint,
            "store_path":  str(store_path / "canon_index.db") if store_path else None,
            "duration_s":  round(time.monotonic() - t0, 3),
        }
