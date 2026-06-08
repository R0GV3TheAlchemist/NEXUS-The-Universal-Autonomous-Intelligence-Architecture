"""
core/rag/retriever.py
~~~~~~~~~~~~~~~~~~~~~
Hybrid retriever for the GAIA-OS RAG pipeline.

Public surface
--------------
RetrievalResult  — dataclass wrapping a Chunk + score + retrieval_type.
Retriever        — hybrid / dense / sparse retrieval over a VectorIndex.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .chunker import Chunk
from .index import VectorIndex


@dataclass
class RetrievalResult:
    chunk:          Chunk
    score:          float
    retrieval_type: str = "hybrid"

    def provenance(self) -> dict:
        return {
            **self.chunk.provenance(),
            "score":          self.score,
            "retrieval_type": self.retrieval_type,
        }


class Retriever:
    """Hybrid retriever with reciprocal-rank fusion."""

    def __init__(self, index: VectorIndex, rrf_k: int = 60) -> None:
        self._index = index
        self._rrf_k = rrf_k

    def retrieve(
        self,
        query:  str,
        top_k:  int = 5,
        mode:   str = "hybrid",
    ) -> List[RetrievalResult]:
        if self._index.count() == 0:
            return []
        if mode == "dense":
            return self._dense(query, top_k)
        if mode == "sparse":
            return self._sparse(query, top_k)
        return self._hybrid(query, top_k)

    def _dense(self, query: str, top_k: int) -> List[RetrievalResult]:
        return [
            RetrievalResult(chunk=c, score=float(s), retrieval_type="dense")
            for c, s in self._index.search(query, top_k=top_k)
        ]

    def _sparse(self, query: str, top_k: int) -> List[RetrievalResult]:
        return [
            RetrievalResult(chunk=c, score=float(s), retrieval_type="sparse")
            for c, s in self._index.keyword_search(query, top_k=top_k)
        ]

    def _hybrid(self, query: str, top_k: int) -> List[RetrievalResult]:
        dense_hits  = self._index.search(query,           top_k=top_k * 2)
        sparse_hits = self._index.keyword_search(query,   top_k=top_k * 2)
        rrf: dict[str, float] = {}
        for rank, (chunk, _) in enumerate(dense_hits):
            rrf[chunk.chunk_id] = rrf.get(chunk.chunk_id, 0.0) + 1.0 / (self._rrf_k + rank + 1)
        for rank, (chunk, _) in enumerate(sparse_hits):
            rrf[chunk.chunk_id] = rrf.get(chunk.chunk_id, 0.0) + 1.0 / (self._rrf_k + rank + 1)
        all_chunks = {c.chunk_id: c for c, _ in dense_hits + sparse_hits}
        ranked = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            RetrievalResult(chunk=all_chunks[cid], score=round(s, 6), retrieval_type="hybrid")
            for cid, s in ranked if cid in all_chunks
        ]
