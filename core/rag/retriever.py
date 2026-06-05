"""
core/rag/retriever.py

Hybrid retriever for GAIA-OS RAG pipeline.
Combines dense vector search (cosine similarity) + sparse keyword search,
deduplicates results, and returns RetrievalResult objects with full provenance.

RetrievalResult schema:
    text: str           — chunk text
    score: float        — combined relevance score [0, 1]
    source: str         — file path
    doc_title: str      — document title
    section: str        — nearest section heading
    chunk_id: str       — deterministic chunk ID
    retrieval_type: str — 'dense', 'sparse', or 'hybrid'
"""
from dataclasses import dataclass
from typing import List, Optional

from .chunker import Chunk
from .index import VectorIndex


@dataclass
class RetrievalResult:
    text: str
    score: float
    source: str
    doc_title: str
    section: str
    chunk_id: str
    retrieval_type: str

    def provenance(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "doc_title": self.doc_title,
            "section": self.section,
            "score": self.score,
            "retrieval_type": self.retrieval_type,
        }

    def __repr__(self) -> str:
        return (
            f"RetrievalResult(score={self.score:.3f}, "
            f"doc='{self.doc_title}', section='{self.section}', "
            f"source='{self.source}')"
        )


class Retriever:
    """
    Hybrid retriever: runs dense + sparse search, merges and re-ranks.

    Scoring:
        final_score = alpha * dense_score + (1 - alpha) * sparse_score
        alpha = 0.7 (dense-dominant; tune via alpha param)
    """

    def __init__(self, index: VectorIndex, alpha: float = 0.7):
        self.index = index
        self.alpha = alpha

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid",
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Natural language query string.
            top_k: Number of results to return.
            mode: 'dense' | 'sparse' | 'hybrid'

        Returns:
            List of RetrievalResult, sorted by score descending.
            Empty list if index is empty or no results found.
        """
        if self.index.count() == 0:
            return []

        dense_results = {}
        sparse_results = {}

        if mode in ("dense", "hybrid"):
            for chunk, score in self.index.search(query, top_k=top_k * 2):
                dense_results[chunk.chunk_id] = (chunk, score)

        if mode in ("sparse", "hybrid"):
            for chunk, score in self.index.keyword_search(query, top_k=top_k * 2):
                sparse_results[chunk.chunk_id] = (chunk, score)

        all_ids = set(dense_results) | set(sparse_results)
        merged = []

        for cid in all_ids:
            dense_score = dense_results[cid][1] if cid in dense_results else 0.0
            sparse_score = sparse_results[cid][1] if cid in sparse_results else 0.0
            chunk = (
                dense_results[cid][0]
                if cid in dense_results
                else sparse_results[cid][0]
            )

            if mode == "dense":
                final_score = dense_score
                rtype = "dense"
            elif mode == "sparse":
                final_score = sparse_score
                rtype = "sparse"
            else:
                final_score = self.alpha * dense_score + (1 - self.alpha) * sparse_score
                rtype = "hybrid"

            merged.append(
                RetrievalResult(
                    text=chunk.text,
                    score=round(final_score, 4),
                    source=chunk.source,
                    doc_title=chunk.doc_title,
                    section=chunk.section,
                    chunk_id=chunk.chunk_id,
                    retrieval_type=rtype,
                )
            )

        merged.sort(key=lambda r: r.score, reverse=True)
        return merged[:top_k]
