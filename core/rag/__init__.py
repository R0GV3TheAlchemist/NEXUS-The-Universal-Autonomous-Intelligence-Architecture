"""
core/rag — Retrieval-Augmented Generation Pipeline
Public API for GAIA-OS knowledge retrieval.

Usage:
    from core.rag import RAGPipeline

    rag = RAGPipeline()
    rag.ingest("/path/to/canon/dir")
    results = rag.query("What is the Elemental Star?")
    for chunk in results:
        print(chunk.text, chunk.source, chunk.score)

Or via module-level singletons:
    from core.rag import ingest, query
"""
from .pipeline import RAGPipeline
from .chunker import Chunk
from .retriever import RetrievalResult

_pipeline = RAGPipeline()


def ingest(path: str) -> int:
    """Ingest a file or directory into the default RAG pipeline. Returns chunk count."""
    return _pipeline.ingest(path)


def query(text: str, top_k: int = 5) -> list:
    """Query the default RAG pipeline. Returns list of RetrievalResult."""
    return _pipeline.query(text, top_k=top_k)


__all__ = [
    "RAGPipeline",
    "Chunk",
    "RetrievalResult",
    "ingest",
    "query",
]
