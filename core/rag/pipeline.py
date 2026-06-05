"""
core/rag/pipeline.py

High-level RAG pipeline for GAIA-OS.
Instruments every ingest and query call through the obs layer.

Usage:
    from core.rag import RAGPipeline

    rag = RAGPipeline(db_path="/var/gaia/rag.db")
    count = rag.ingest("/path/to/canon")
    results = rag.query("structured water coherence")

Auto-instrumented:
    - Every ingest call → obs audit log (rag.ingest)
    - Every query call → obs structured log + telemetry
    - Trace context propagated from caller
"""
import time
from pathlib import Path
from typing import List, Optional

from .chunker import chunk_file, chunk_directory, Chunk
from .embedder import FallbackEmbedder
from .index import VectorIndex
from .retriever import Retriever, RetrievalResult

try:
    from core.obs import get_logger, get_audit, get_telemetry
    from core.obs.audit import AuditEventType
    from core.obs.tracer import TraceContext
    _OBS_AVAILABLE = True
except ImportError:
    _OBS_AVAILABLE = False


class RAGPipeline:
    """
    Full ingest → index → retrieve pipeline.

    Args:
        db_path: SQLite path for the vector index. Defaults to ':memory:'.
        chunk_size: Characters per chunk.
        overlap: Overlap between consecutive chunks.
        top_k: Default number of results returned by query().
        retrieval_mode: 'dense' | 'sparse' | 'hybrid'
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        chunk_size: int = 512,
        overlap: int = 64,
        top_k: int = 5,
        retrieval_mode: str = "hybrid",
    ):
        self.db_path = db_path
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.default_top_k = top_k
        self.retrieval_mode = retrieval_mode

        self._embedder = FallbackEmbedder()
        self._index = VectorIndex(db_path=db_path, embedder=self._embedder)
        self._retriever = Retriever(self._index)

        self._logger = get_logger() if _OBS_AVAILABLE else None
        self._audit = get_audit() if _OBS_AVAILABLE else None
        self._telemetry = get_telemetry() if _OBS_AVAILABLE else None

    def ingest(self, path: str) -> int:
        """
        Ingest a file or directory into the vector index.
        Returns total chunk count added.
        """
        p = Path(path)
        start = time.monotonic()

        if p.is_dir():
            chunks = chunk_directory(p, self.chunk_size, self.overlap)
        elif p.is_file():
            chunks = chunk_file(p, self.chunk_size, self.overlap)
        else:
            if self._logger:
                self._logger.warning(f"RAG ingest: path not found: {path}", tool="rag.ingest")
            return 0

        added = self._index.add_chunks(chunks)
        elapsed = (time.monotonic() - start) * 1000

        if _OBS_AVAILABLE and self._audit:
            self._audit.record(
                event_type=AuditEventType.RAG_INGEST,
                actor="system",
                action=f"ingest:{path}",
                outcome="ok",
                resource=path,
                meta={"chunks_added": added, "latency_ms": round(elapsed, 2)},
            )
        if _OBS_AVAILABLE and self._telemetry:
            self._telemetry.record("rag.ingest", latency_ms=elapsed)
        if _OBS_AVAILABLE and self._logger:
            self._logger.info(
                f"RAG ingested {added} chunks from {path}",
                tool="rag.ingest",
                latency_ms=round(elapsed, 2),
                outcome="ok",
                meta={"path": path, "chunks": added},
            )

        return added

    def query(
        self,
        text: str,
        top_k: Optional[int] = None,
        mode: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Query the index for relevant chunks.
        Returns list of RetrievalResult with provenance metadata.
        Returns empty list (not exception) if index is empty.
        """
        k = top_k or self.default_top_k
        m = mode or self.retrieval_mode
        start = time.monotonic()

        try:
            results = self._retriever.retrieve(text, top_k=k, mode=m)
            elapsed = (time.monotonic() - start) * 1000
            outcome = "ok"
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            outcome = "error"
            results = []
            if self._logger:
                self._logger.error(
                    f"RAG query failed: {exc}",
                    tool="rag.query",
                    latency_ms=round(elapsed, 2),
                    outcome="error",
                )

        if _OBS_AVAILABLE and self._telemetry:
            self._telemetry.record("rag.query", latency_ms=elapsed, error=(outcome == "error"))
        if _OBS_AVAILABLE and self._logger:
            self._logger.info(
                f"RAG query returned {len(results)} results",
                tool="rag.query",
                latency_ms=round(elapsed, 2),
                outcome=outcome,
                meta={"query": text[:120], "top_k": k, "mode": m, "result_count": len(results)},
            )

        return results

    @property
    def index_size(self) -> int:
        return self._index.count()

    @property
    def indexed_sources(self) -> List[str]:
        return self._index.sources()

    def reindex(self, path: str) -> int:
        """Delete all chunks from source and re-ingest. Returns new chunk count."""
        p = Path(path).resolve()
        self._index.delete_source(str(p))
        return self.ingest(str(p))
