"""
tests/test_rag.py

Full test coverage for the GAIA-OS RAG Pipeline (Issues #217, #218).
Tests: chunker, embedder, index, retriever, pipeline.
"""
import json
import tempfile
from pathlib import Path

import pytest

from core.rag.chunker import chunk_text, chunk_file, chunk_directory, Chunk
from core.rag.embedder import FallbackEmbedder, cosine_similarity, _l2_normalize
from core.rag.index import VectorIndex
from core.rag.retriever import Retriever, RetrievalResult
from core.rag.pipeline import RAGPipeline


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------

SAMPLE_MD = """# GAIA Elemental Star

## Overview

The Elemental Star is a septagram framework.
It maps seven elements to physical, quantum, and metaphysical dimensions.

## The Seven Points

1. Fire — transformation
2. Water — coherence
3. Earth — structure
4. Air — communication
5. Aether — quintessence
6. Synthesia — will made matter
7. The Gate — the crossing
"""


class TestChunker:
    def test_chunk_text_returns_chunks(self):
        chunks = chunk_text(SAMPLE_MD, "test.md", chunk_size=200, overlap=20)
        assert len(chunks) >= 1
        for c in chunks:
            assert isinstance(c, Chunk)
            assert c.text
            assert c.source == "test.md"

    def test_chunk_ids_are_deterministic(self):
        chunks1 = chunk_text(SAMPLE_MD, "test.md")
        chunks2 = chunk_text(SAMPLE_MD, "test.md")
        for c1, c2 in zip(chunks1, chunks2):
            assert c1.chunk_id == c2.chunk_id

    def test_doc_title_extracted(self):
        chunks = chunk_text(SAMPLE_MD, "test.md")
        assert chunks[0].doc_title == "GAIA Elemental Star"

    def test_section_extraction(self):
        chunks = chunk_text(SAMPLE_MD, "test.md", chunk_size=100, overlap=0)
        sections = {c.section for c in chunks}
        assert len(sections) >= 1

    def test_provenance_dict(self):
        chunks = chunk_text(SAMPLE_MD, "test.md")
        prov = chunks[0].provenance()
        assert "chunk_id" in prov
        assert "source" in prov
        assert "doc_title" in prov

    def test_chunk_file(self):
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_MD)
            fpath = Path(f.name)
        chunks = chunk_file(fpath)
        assert len(chunks) >= 1
        fpath.unlink()

    def test_chunk_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.md").write_text(SAMPLE_MD, encoding="utf-8")
            (Path(tmpdir) / "b.txt").write_text("plain text content", encoding="utf-8")
            chunks = chunk_directory(Path(tmpdir))
        assert len(chunks) >= 2

    def test_unsupported_extension_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "skip.py").write_text("print('hi')", encoding="utf-8")
            chunks = chunk_directory(Path(tmpdir))
        assert len(chunks) == 0


# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------

class TestEmbedder:
    def test_embed_after_fit(self):
        emb = FallbackEmbedder()
        corpus = ["the quick brown fox", "jumps over the lazy dog", "gaia crystal consciousness"]
        emb.fit(corpus)
        vec = emb.embed("quick fox")
        assert isinstance(vec, list)
        assert len(vec) == emb.vocab_size

    def test_embed_returns_normalized_vector(self):
        emb = FallbackEmbedder()
        emb.fit(["water fire earth air aether"])
        vec = emb.embed("water fire")
        norm = sum(x * x for x in vec) ** 0.5
        assert abs(norm - 1.0) < 0.01 or norm == 0.0

    def test_cosine_similarity_identical(self):
        vec = [1.0, 0.0, 0.0]
        assert cosine_similarity(vec, vec) == 1.0

    def test_cosine_similarity_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_similarity(a, b) == 0.0

    def test_embed_batch(self):
        emb = FallbackEmbedder()
        texts = ["alpha", "beta", "gamma"]
        emb.fit(texts)
        vecs = emb.embed_batch(texts)
        assert len(vecs) == 3


# ---------------------------------------------------------------------------
# VectorIndex
# ---------------------------------------------------------------------------

class TestVectorIndex:
    def _make_index(self):
        return VectorIndex(db_path=":memory:")

    def _make_chunks(self):
        return chunk_text(SAMPLE_MD, "test.md", chunk_size=200, overlap=20)

    def test_add_and_count(self):
        idx = self._make_index()
        chunks = self._make_chunks()
        added = idx.add_chunks(chunks)
        assert added == len(chunks)
        assert idx.count() == len(chunks)

    def test_duplicate_chunks_not_added(self):
        idx = self._make_index()
        chunks = self._make_chunks()
        idx.add_chunks(chunks)
        added2 = idx.add_chunks(chunks)
        assert idx.count() == len(chunks)

    def test_search_returns_results(self):
        idx = self._make_index()
        idx.add_chunks(self._make_chunks())
        results = idx.search("elemental star", top_k=3)
        assert len(results) <= 3
        for chunk, score in results:
            assert isinstance(chunk, Chunk)
            assert isinstance(score, float)

    def test_keyword_search(self):
        idx = self._make_index()
        idx.add_chunks(self._make_chunks())
        results = idx.keyword_search("septagram", top_k=5)
        assert len(results) >= 1
        assert any("septagram" in r[0].text.lower() for r in results)

    def test_sources(self):
        idx = self._make_index()
        idx.add_chunks(self._make_chunks())
        sources = idx.sources()
        assert len(sources) >= 1

    def test_delete_source(self):
        idx = self._make_index()
        chunks = self._make_chunks()
        idx.add_chunks(chunks)
        deleted = idx.delete_source(chunks[0].source)
        assert deleted == len(chunks)
        assert idx.count() == 0


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------

class TestRetriever:
    def _make_retriever(self):
        idx = VectorIndex(db_path=":memory:")
        chunks = chunk_text(SAMPLE_MD, "test.md", chunk_size=150, overlap=20)
        idx.add_chunks(chunks)
        return Retriever(idx)

    def test_hybrid_retrieval(self):
        ret = self._make_retriever()
        results = ret.retrieve("elemental star septagram", top_k=3)
        assert len(results) <= 3
        for r in results:
            assert isinstance(r, RetrievalResult)
            assert r.score >= 0

    def test_dense_only_mode(self):
        ret = self._make_retriever()
        results = ret.retrieve("crystal water fire", top_k=3, mode="dense")
        for r in results:
            assert r.retrieval_type == "dense"

    def test_sparse_only_mode(self):
        ret = self._make_retriever()
        results = ret.retrieve("septagram", top_k=5, mode="sparse")
        for r in results:
            assert r.retrieval_type == "sparse"

    def test_provenance_present(self):
        ret = self._make_retriever()
        results = ret.retrieve("transformation fire", top_k=2)
        for r in results:
            prov = r.provenance()
            assert "chunk_id" in prov
            assert "source" in prov
            assert "doc_title" in prov
            assert "score" in prov

    def test_empty_index_returns_empty(self):
        idx = VectorIndex(db_path=":memory:")
        ret = Retriever(idx)
        results = ret.retrieve("anything", top_k=5)
        assert results == []


# ---------------------------------------------------------------------------
# RAGPipeline (integration)
# ---------------------------------------------------------------------------

class TestRAGPipeline:
    def test_ingest_file(self):
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_MD)
            fpath = Path(f.name)
        rag = RAGPipeline()
        count = rag.ingest(str(fpath))
        assert count > 0
        assert rag.index_size == count
        fpath.unlink()

    def test_ingest_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "doc1.md").write_text(SAMPLE_MD, encoding="utf-8")
            (Path(tmpdir) / "doc2.md").write_text("# Crystal Safety\n\nQuartz is safe.", encoding="utf-8")
            rag = RAGPipeline()
            count = rag.ingest(tmpdir)
        assert count > 0

    def test_query_returns_results(self):
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_MD)
            fpath = Path(f.name)
        rag = RAGPipeline()
        rag.ingest(str(fpath))
        results = rag.query("elemental star")
        assert isinstance(results, list)
        fpath.unlink()

    def test_query_empty_index_returns_empty(self):
        rag = RAGPipeline()
        results = rag.query("anything")
        assert results == []

    def test_query_never_raises(self):
        rag = RAGPipeline()
        try:
            rag.query("even with empty index this must not raise")
        except Exception as e:
            pytest.fail(f"query raised unexpectedly: {e}")

    def test_ingest_nonexistent_path_returns_zero(self):
        rag = RAGPipeline()
        count = rag.ingest("/nonexistent/path/that/does/not/exist")
        assert count == 0

    def test_reindex(self):
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_MD)
            fpath = Path(f.name)
        rag = RAGPipeline()
        first = rag.ingest(str(fpath))
        second = rag.reindex(str(fpath))
        assert second == first
        assert rag.index_size == first
        fpath.unlink()

    def test_indexed_sources(self):
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_MD)
            fpath = Path(f.name)
        rag = RAGPipeline()
        rag.ingest(str(fpath))
        assert len(rag.indexed_sources) >= 1
        fpath.unlink()
