"""
tests/test_canon_search.py
Unit tests for G-8 Canon v2 semantic search.

Covers:
  - _tokenize: lowercasing, punctuation stripping, min-length filter
  - _tokenize: normalisation, empty input
  - _chunk_text: single chunk, multi-chunk, overlap correctness
  - _best_excerpt: term-centred extraction, fallback to head
  - _TFIDFIndex.build: chunk count, IDF smoke test
  - _TFIDFIndex.query: returns results, de-dups by doc, stop-word handling,
                        empty corpus, all-stop-word query fallback
  - CanonLoader.search: empty corpus returns [], relevant doc ranks first,
                         max_results respected, backward-compatible keys present
  - CanonLoader.search_v2: min_score filter, over-fetch + trim
  - Position boost: top-of-doc chunk scores higher than mid-doc chunk
  - Proximity bonus: co-located terms score higher than spread terms
"""

import math
import pytest

from core.canon_loader import (
    _tokenize,
    _tokenize,
    _chunk_text,
    _best_excerpt,
    _TFIDFIndex,
    CanonLoader,
    CanonStatus,
    _CHUNK_SIZE,
    _CHUNK_OVERLAP,
)


# ================================================================== #
#  _tokenize                                                          #
# ================================================================== #

class TestTokenize:
    def test_lowercases(self):
        assert "sovereignty" in _tokenize("Sovereignty")

    def test_strips_punctuation(self):
        assert "canon" in _tokenize("canon.")
        assert "gaia" in _tokenize("GAIA!")

    def test_filters_single_chars(self):
        tokens = _tokenize("a b c the")
        assert "a" not in tokens
        assert "b" not in tokens

    def test_empty_string(self):
        assert _tokenize("") == []


# ================================================================== #
#  _tokenize                                                         #
# ================================================================== #

class TestTermFreq:
    def test_normalised(self):
        tf = _tokenize("sovereignty sovereignty canon")
        assert abs(tf["sovereignty"] - 2/3) < 1e-6
        assert abs(tf["canon"] - 1/3) < 1e-6

    def test_empty(self):
        assert _tokenize("") == {}


# ================================================================== #
#  _chunk_text                                                        #
# ================================================================== #

class TestChunkText:
    def test_short_doc_single_chunk(self):
        chunks = _chunk_text("hello world")
        assert len(chunks) == 1
        assert chunks[0][1] == 0   # offset == 0

    def test_long_doc_multiple_chunks(self):
        text   = "x" * (_CHUNK_SIZE * 3)
        chunks = _chunk_text(text)
        assert len(chunks) > 1

    def test_overlap_offsets(self):
        text   = "a" * (_CHUNK_SIZE + _CHUNK_OVERLAP + 100)
        chunks = _chunk_text(text)
        step   = _CHUNK_SIZE - _CHUNK_OVERLAP
        assert chunks[1][1] == step

    def test_empty_string(self):
        chunks = _chunk_text("")
        assert chunks == [("", 0)]


# ================================================================== #
#  _best_excerpt                                                      #
# ================================================================== #

class TestBestExcerpt:
    def test_centres_on_first_term(self):
        text    = "padding " * 50 + "sovereignty is the core" + " filler" * 50
        excerpt = _best_excerpt(text, ["sovereignty"])
        assert "sovereignty" in excerpt

    def test_fallback_to_head(self):
        text    = "hello world and more text here"
        excerpt = _best_excerpt(text, ["zzznomatch"])
        assert excerpt.startswith("hello")

    def test_strips_newlines(self):
        text    = "line one\nline two\ncanon here"
        excerpt = _best_excerpt(text, ["canon"])
        assert "\n" not in excerpt


# ================================================================== #
#  _TFIDFIndex                                                        #
# ================================================================== #

def _make_docs(*texts):
    return {
        f"doc{i}": {"content": t, "title": f"Doc {i}"}
        for i, t in enumerate(texts)
    }


class TestTFIDFIndex:
    def test_build_sets_built_flag(self):
        idx = _TFIDFIndex()
        idx.build(_make_docs("hello world"))
        assert idx._built is True

    def test_idf_computed(self):
        idx = _TFIDFIndex()
        idx.build(_make_docs("sovereignty is real", "canon defines sovereignty"))
        assert "sovereignty" in idx._idf

    def test_query_returns_results(self):
        idx = _TFIDFIndex()
        idx.build(_make_docs(
            "sovereignty is the first principle of GAIA",
            "unrelated text about something else entirely",
        ))
        results = idx.query("sovereignty GAIA", max_results=2)
        assert len(results) >= 1
        assert results[0]["doc_id"] == "doc0"

    def test_dedup_by_doc(self):
        # Single long doc produces multiple chunks — should appear once in results
        long_text = ("sovereignty " * 20 + "canon " * 20) * 10
        idx = _TFIDFIndex()
        idx.build({"only_doc": {"content": long_text, "title": "Long"}})
        results = idx.query("sovereignty canon", max_results=5)
        doc_ids = [r["doc_id"] for r in results]
        assert doc_ids.count("only_doc") == 1

    def test_empty_corpus(self):
        idx = _TFIDFIndex()
        idx.build({})
        assert idx.query("anything") == []

    def test_all_stop_words_fallback(self):
        idx = _TFIDFIndex()
        idx.build(_make_docs("the is a and or", "real content here"))
        # Should not crash — falls back to using all terms
        results = idx.query("the and or")
        assert isinstance(results, list)


# ================================================================== #
#  CanonLoader.search                                                 #
# ================================================================== #

def _loader_with_docs(*texts):
    loader = CanonLoader.__new__(CanonLoader)
    loader._docs_dir  = None
    loader._manifest  = {}
    loader._documents = {
        f"doc{i}": {"id": f"doc{i}", "content": t, "title": f"Title {i}", "source": "test"}
        for i, t in enumerate(texts)
    }
    loader._status  = CanonStatus.GREEN
    loader._loaded  = True
    loader._index   = _TFIDFIndex()
    loader._index.build(loader._documents)
    return loader


class TestCanonLoaderSearch:
    def test_empty_corpus(self):
        loader = _loader_with_docs()
        assert loader.search("anything") == []

    def test_relevant_doc_ranks_first(self):
        loader = _loader_with_docs(
            "completely unrelated filler text without target words",
            "sovereignty is the foundational canon principle of GAIA consciousness",
        )
        results = loader.search("sovereignty canon")
        assert results[0]["doc_id"] == "doc1"

    def test_max_results_respected(self):
        loader = _loader_with_docs(*(f"sovereignty doc {i}" for i in range(10)))
        assert len(loader.search("sovereignty", max_results=3)) <= 3

    def test_result_has_required_keys(self):
        loader = _loader_with_docs("sovereignty is the core principle")
        results = loader.search("sovereignty")
        assert results
        for key in ("doc_id", "title", "excerpt", "score"):
            assert key in results[0]

    def test_no_results_for_absent_term(self):
        loader = _loader_with_docs("hello world filler text")
        results = loader.search("zzznomatch")
        assert results == []


# ================================================================== #
#  CanonLoader.search_v2                                              #
# ================================================================== #

class TestSearchV2:
    def test_min_score_filters(self):
        loader = _loader_with_docs(
            "sovereignty is the core principle of GAIA",
            "unrelated filler",
        )
        results = loader.search_v2("sovereignty", min_score=999.0)
        assert results == []

    def test_returns_results_without_min_score(self):
        loader = _loader_with_docs("sovereignty is the core principle of GAIA")
        results = loader.search_v2("sovereignty")
        assert len(results) >= 1


# ================================================================== #
#  Position Boost                                                     #
# ================================================================== #

class TestPositionBoost:
    def test_top_of_doc_scores_higher(self):
        """
        Two docs: one has the target term at offset 0, one buries it
        deep. The early-position doc should rank first.
        """
        early = "sovereignty " + "filler " * 400
        late  = "filler " * 400 + "sovereignty "
        loader = _loader_with_docs(early, late)
        results = loader.search("sovereignty", max_results=2)
        assert results[0]["doc_id"] == "doc0"


# ================================================================== #
#  Proximity Bonus                                                    #
# ================================================================== #

class TestProximityBonus:
    def test_adjacent_terms_score_higher(self):
        close   = "sovereignty and canon are adjacent here in this text"
        spread  = "sovereignty " + "filler " * 200 + "canon"
        loader  = _loader_with_docs(close, spread)
        results = loader.search("sovereignty canon", max_results=2)
        assert results[0]["doc_id"] == "doc0"
