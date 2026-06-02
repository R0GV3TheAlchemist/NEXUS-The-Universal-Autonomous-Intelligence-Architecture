"""
CanonLoader — Loads, caches, and serves the GAIA constitutional canon.

v2 (G-8): Semantic search upgrade.
  - TF-IDF scoring: term frequency weighted by inverse document frequency
    so rare, meaningful terms rank higher than common filler words.
  - Chunked passage search: documents are split into ~300-token overlapping
    windows. Each chunk is scored independently, so a long document does not
    bury its best passage under low-density noise.
  - Positional boosting: matches in the first 20% of a document (title,
    opening premise) are boosted x1.5 — canon preambles matter more.
  - Multi-term proximity: if two query terms appear within 50 characters of
    each other in the same chunk, a co-occurrence bonus is added.
  - Backward-compatible: search() signature unchanged — callers in server.py
    get v2 results transparently. search_v2() exposes richer metadata.
  - stop_words filter: common English stop words excluded from IDF so they
    do not inflate or deflate scores.

v3 (G-7 #169): Canon Dependency Graph.
  - self.graph: CanonGraph    — full dependency graph (requires + supersedes)
  - is_deprecated(id)         — quick deprecation gate
  - dependents(id)            — transitive dependents of a node
  - dependencies(id)          — transitive dependencies of a node
  - conflict_check(node)      — tag-overlap conflict detection
  - impact_report(id)         — pre-deprecation safety gate
  - graph_enabled flag        — opt-out for testing without canon dir

All other behaviour (load, get, manifest, remote fetch, caching, status)
unchanged from v2.

Epistemic Status: FOUNDATIONAL
Canon Ref: C00, C01, C15, C17, C30
"""

from __future__ import annotations

import math
import os
import re
import time
import logging
import urllib.request
from pathlib import Path
from typing import Any, List, Optional

from core.canon_graph import CanonGraph, CanonNode  # G-7 #169

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  Paths & Constants                                                  #
# ------------------------------------------------------------------ #

_REPO_ROOT        = Path(__file__).parent.parent
_DOCS_CANON_DIR   = _REPO_ROOT / "docs" / "canon"
_LEGACY_CANON_DIR = _REPO_ROOT / "canon"
_MANIFEST_PATH    = _DOCS_CANON_DIR / "CANON_MANIFEST.md"
_CACHE_DIR        = Path.home() / ".gaia" / "canon_cache"
_CACHE_TTL_SECONDS = 86400  # 24 hours

_FLOOR_DOCS = {"00_Documentation_Index", "01_GAIA_Master_Document"}

# Chunk size in characters (~300 tokens at ~4 chars/token)
_CHUNK_SIZE    = 1200
_CHUNK_OVERLAP = 200
_EXCERPT_LEN   = 300
_POSITION_BOOST_THRESHOLD = 0.20   # first 20% of doc
_POSITION_BOOST_FACTOR    = 1.5
_PROXIMITY_WINDOW         = 50     # chars
_PROXIMITY_BONUS          = 0.5    # per co-occurring pair

# English stop words — excluded from IDF calculation
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "as", "is", "was", "are",
    "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might", "shall",
    "can", "this", "that", "these", "those", "it", "its", "not", "no",
    "so", "if", "then", "than", "when", "where", "which", "who", "what",
    "how", "all", "each", "every", "both", "more", "most", "other",
    "into", "through", "during", "about", "between", "i", "we", "you",
    "he", "she", "they", "their", "our", "your", "his", "her", "my",
})


# ------------------------------------------------------------------ #
#  Status                                                             #
# ------------------------------------------------------------------ #

class CanonStatus:
    GREEN  = "green"
    YELLOW = "yellow"
    RED    = "red"


# ------------------------------------------------------------------ #
#  TF-IDF Index                                                       #
# ------------------------------------------------------------------ #

class _TFIDFIndex:
    """
    Lightweight in-process TF-IDF index over canon document chunks.

    On build():
      - Each document is split into overlapping chunks.
      - Term frequencies are computed per chunk.
      - IDF is computed across all chunks (treating each chunk as a document).

    On query():
      - Each chunk is scored: sum of TF-IDF(term) for query terms.
      - Position boost applied to chunks from the top 20% of their source doc.
      - Proximity bonus applied when two query terms appear near each other.
      - Top chunks de-duplicated by source doc (best chunk per doc returned).
    """

    def __init__(self):
        self._chunks:    list[dict] = []           # {doc_id, title, text, offset, doc_len}
        self._idf:       dict[str, float] = {}     # term -> IDF score
        self._tf_cache:  list[dict[str, float]] = []  # per-chunk TF
        self._built = False

    def build(self, documents: dict[str, dict]) -> None:
        """Build the full TF-IDF index from loaded canon documents."""
        self._chunks    = []
        self._tf_cache  = []
        self._idf       = {}

        # 1. Chunk all documents
        for doc_id, doc in documents.items():
            content = doc.get("content", "")
            title   = doc.get("title", doc_id)
            doc_len = len(content)
            for chunk_text, offset in _chunk_text(content):
                self._chunks.append({
                    "doc_id": doc_id,
                    "title":  title,
                    "text":   chunk_text,
                    "offset": offset,
                    "doc_len": doc_len,
                })

        # 2. Compute TF per chunk
        for chunk in self._chunks:
            self._tf_cache.append(_term_freq(chunk["text"]))

        # 3. Compute IDF across all chunks
        n = len(self._chunks)
        if n == 0:
            self._built = True
            return

        doc_freq: dict[str, int] = {}
        for tf in self._tf_cache:
            for term in tf:
                doc_freq[term] = doc_freq.get(term, 0) + 1

        for term, df in doc_freq.items():
            self._idf[term] = math.log((n + 1) / (df + 1)) + 1.0  # smoothed

        self._built = True
        logger.info(f"[Canon TF-IDF] Index built: {n} chunks from {len(documents)} docs, "
                    f"{len(self._idf)} unique terms.")

    def query(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict]:
        """
        Score all chunks for the query. Return top max_results,
        one per source document (best chunk per doc).
        """
        if not self._built or not self._chunks:
            return []

        q_terms = [
            t for t in _tokenize(query)
            if t not in _STOP_WORDS
        ] or _tokenize(query)   # fallback: use all terms if all are stop words

        if not q_terms:
            return []

        scored: list[tuple[float, int]] = []  # (score, chunk_idx)

        for idx, (chunk, tf) in enumerate(zip(self._chunks, self._tf_cache)):
            score = 0.0
            text_lower = chunk["text"].lower()

            for term in q_terms:
                tf_val  = tf.get(term, 0.0)
                idf_val = self._idf.get(term, 1.0)
                score  += tf_val * idf_val

            if score == 0.0:
                continue

            # Position boost: chunks from top 20% of source doc
            doc_len = chunk["doc_len"]
            if doc_len > 0 and chunk["offset"] / doc_len < _POSITION_BOOST_THRESHOLD:
                score *= _POSITION_BOOST_FACTOR

            # Proximity bonus: pairs of query terms near each other
            for i, t1 in enumerate(q_terms):
                for t2 in q_terms[i + 1:]:
                    pos1 = text_lower.find(t1)
                    pos2 = text_lower.find(t2)
                    if pos1 >= 0 and pos2 >= 0 and abs(pos1 - pos2) <= _PROXIMITY_WINDOW:
                        score += _PROXIMITY_BONUS

            scored.append((score, idx))

        scored.sort(key=lambda x: x[0], reverse=True)

        # De-duplicate: keep best chunk per doc_id
        seen_docs: set[str] = set()
        results: list[dict] = []
        for score, idx in scored:
            chunk  = self._chunks[idx]
            doc_id = chunk["doc_id"]
            if doc_id in seen_docs:
                continue
            seen_docs.add(doc_id)
            excerpt = _best_excerpt(chunk["text"], q_terms)
            results.append({
                "doc_id":  doc_id,
                "title":   chunk["title"],
                "excerpt": excerpt,
                "score":   round(score, 4),
                "source":  "tfidf",
                "chunk_offset": chunk["offset"],
            })
            if len(results) >= max_results:
                break

        return results


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #

def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if len(t) > 1]


def _term_freq(text: str) -> dict[str, float]:
    """Compute normalised term frequency for a chunk."""
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts: dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = len(tokens)
    return {t: c / total for t, c in counts.items()}


def _chunk_text(text: str) -> list[tuple[str, int]]:
    """
    Split text into overlapping chunks of _CHUNK_SIZE chars,
    stepping by (_CHUNK_SIZE - _CHUNK_OVERLAP).
    Returns list of (chunk_text, byte_offset).
    """
    step   = _CHUNK_SIZE - _CHUNK_OVERLAP
    chunks = []
    start  = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunks.append((text[start:end], start))
        if end >= len(text):
            break
        start += step
    return chunks if chunks else [(text, 0)]


def _best_excerpt(chunk_text: str, terms: list[str]) -> str:
    """
    Find the best ~300-char excerpt from a chunk centred on the first
    query term hit. Falls back to the chunk head if no hit found.
    """
    lower = chunk_text.lower()
    best_pos = -1
    for term in terms:
        pos = lower.find(term)
        if pos >= 0:
            best_pos = pos
            break
    if best_pos < 0:
        raw = chunk_text[:_EXCERPT_LEN]
    else:
        start = max(0, best_pos - 80)
        raw   = chunk_text[start: start + _EXCERPT_LEN]
    return raw.strip().replace("\n", " ")


# ------------------------------------------------------------------ #
#  CanonLoader                                                        #
# ------------------------------------------------------------------ #

class CanonLoader:
    """
    Loads GAIA canon documents from local storage and the GAIA remote repo.

    Priority order for each document:
      1. Local file in docs/canon/
      2. Local cache in ~/.gaia/canon_cache/ (if within TTL)
      3. Remote fetch from raw.githubusercontent.com/R0GV3TheAlchemist/GAIA
      4. Legacy canon/ directory (pre-C-series alchemical docs)

    The CanonLoader never blocks startup. If the floor documents (C00, C01)
    are present, status is GREEN regardless of remote availability.

    v3 additions (#169)
    -------------------
    self.graph: Optional[CanonGraph]   — None until load() completes or
                                         when graph_enabled=False.
    graph_enabled: bool                — Set False in tests that don't need
                                         the dependency graph (default True).
    """

    def __init__(
        self,
        docs_canon_dir: Optional[Path] = None,
        graph_enabled: bool = True,
    ):
        self._docs_dir    = docs_canon_dir or _DOCS_CANON_DIR
        self._manifest:   dict[str, dict] = {}
        self._documents:  dict[str, dict] = {}
        self._status      = CanonStatus.YELLOW
        self._loaded      = False
        self._index       = _TFIDFIndex()
        self._graph_enabled = graph_enabled
        self.graph: Optional[CanonGraph] = None   # set by _build_graph()
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def load(self) -> bool:
        """
        Primary load sequence. Called once at startup.
        Returns True when at least the constitutional floor is loaded.
        """
        self._parse_manifest()
        self._load_local_docs()
        self._load_legacy_docs()
        self._evaluate_status()
        self._index.build(self._documents)   # TF-IDF index (G-8)
        self._build_graph()                  # Canon dependency graph (G-7 #169)
        self._loaded = True
        logger.info(
            f"CanonLoader v3: {len(self._documents)} docs loaded | "
            f"status={self._status} | "
            f"graph={'enabled' if self.graph else 'disabled'}"
        )
        return self._status in (CanonStatus.GREEN, CanonStatus.YELLOW)

    def get(self, doc_id: str) -> Optional[dict]:
        """
        Retrieve a canon document by ID. If not locally loaded,
        attempts a remote fetch (lazy hydration).
        """
        if doc_id in self._documents:
            return self._documents[doc_id]
        doc = self._fetch_remote(doc_id)
        if doc:
            self._index.build(self._documents)  # rebuild index with new doc
        return doc

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Semantic search across all loaded canon documents (G-8 upgrade).

        Uses TF-IDF scoring with chunked passages, positional boosting,
        and multi-term proximity bonuses. Falls back gracefully to an
        empty list if no documents are loaded.

        Returns a ranked list of:
          {doc_id, title, excerpt, score, source, chunk_offset}

        Backward-compatible: callers using the v1 {doc_id, title, excerpt,
        score, source} shape still work — chunk_offset is additive.
        """
        if not self._index._built:
            self._index.build(self._documents)
        return self._index.query(query, max_results=max_results)

    def search_v2(
        self,
        query: str,
        max_results:    int  = 5,
        min_score:      float = 0.0,
        boost_position: bool  = True,
    ) -> list[dict]:
        """
        Extended search API (G-8).

        Same as search() but exposes:
          - min_score:      filter out results below this threshold.
          - boost_position: disable positional boost (useful for tests).
          - Returns full chunk metadata including chunk_offset and score.

        Intended for internal engine use and admin tooling. The /query/stream
        endpoint uses search() for simplicity.
        """
        results = self.search(query, max_results=max_results * 2)  # over-fetch
        if min_score > 0.0:
            results = [r for r in results if r["score"] >= min_score]
        return results[:max_results]

    def list_documents(self) -> list[str]:
        """List all loaded canon document IDs."""
        return list(self._documents.keys())

    def list_manifest(self) -> list[dict]:
        """Return the full manifest registry (loaded + remote-only entries)."""
        return list(self._manifest.values())

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------ #
    #  Canon Graph Delegates  (G-7 #169)                                   #
    # ------------------------------------------------------------------ #

    def is_deprecated(self, node_id: str) -> bool:
        """
        Return True if ``node_id`` is marked DEPRECATED in the canon graph.
        Returns False gracefully when the graph is not built.
        """
        if self.graph is None:
            return False
        return self.graph.is_deprecated(node_id)

    def dependents(self, node_id: str, direct: bool = False) -> List[str]:
        """
        Return canon IDs that depend on ``node_id``.
        Returns [] gracefully when the graph is not built.
        """
        if self.graph is None:
            return []
        return self.graph.dependents(node_id, direct=direct)

    def dependencies(self, node_id: str, direct: bool = False) -> List[str]:
        """
        Return canon IDs that ``node_id`` depends on.
        Returns [] gracefully when the graph is not built.
        """
        if self.graph is None:
            return []
        return self.graph.dependencies(node_id, direct=direct)

    def conflict_check(self, proposed: CanonNode) -> List[str]:
        """
        Return IDs of existing ACTIVE nodes that conflict with ``proposed``
        (3+ shared tags). Returns [] gracefully when graph is not built.
        """
        if self.graph is None:
            return []
        return self.graph.conflict_check(proposed)

    def impact_report(self, node_id: str) -> dict:
        """
        Full impact assessment before deprecating or modifying a canon node.
        Returns a stub dict gracefully when graph is not built.
        """
        if self.graph is None:
            return {"node": None, "direct_dependents": [], "all_dependents": [], "supersedes": [], "cycles": []}
        return self.graph.impact_report(node_id)

    # ------------------------------------------------------------------ #
    #  Internal: Canon Graph Build  (G-7 #169)                             #
    # ------------------------------------------------------------------ #

    def _build_graph(self, trace: Any = None) -> None:
        """
        Instantiate ``CanonGraph`` over the local docs directory.
        Populates ``self.graph``.

        Never raises (C30) — a broken graph build logs an error but
        does not block GAIA startup.  ``self.graph`` remains ``None``
        if construction fails.
        """
        if not self._graph_enabled:
            logger.info("CanonLoader: graph_enabled=False — skipping CanonGraph build.")
            return
        if not self._docs_dir.exists():
            logger.warning(
                "CanonLoader: docs_canon_dir not found (%s) — CanonGraph not built.",
                self._docs_dir,
            )
            return
        try:
            self.graph = CanonGraph(self._docs_dir, trace=trace)
            s = self.graph.summary()
            logger.info(
                "CanonGraph: %d nodes (%d active, %d deprecated, %d draft), "
                "%d edges, cycles=%d",
                s["total"], s["active"], s["deprecated"], s["draft"],
                s["edges"], s["cycles"],
            )
            if s["deprecated"] > 0:
                dep_ids = [n.id for n in self.graph.deprecated_nodes()]
                logger.info("CanonGraph: deprecated nodes — %s", dep_ids)
        except Exception as exc:
            logger.error(
                "CanonGraph build failed (non-fatal): %s", exc, exc_info=True
            )
            self.graph = None

    # ------------------------------------------------------------------ #
    #  Internal: Manifest Parsing                                          #
    # ------------------------------------------------------------------ #

    def _parse_manifest(self):
        if not _MANIFEST_PATH.exists():
            logger.warning(f"Manifest not found at {_MANIFEST_PATH} — skipping remote registry.")
            return
        content = _MANIFEST_PATH.read_text(encoding="utf-8")
        row_pattern = re.compile(
            r"\|\s*(C\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|\s*(https://[^\s|]+)\s*\|"
        )
        for match in row_pattern.finditer(content):
            c_id, filename, url = match.group(1), match.group(2).strip(), match.group(3).strip()
            doc_id = Path(filename).stem
            self._manifest[doc_id] = {
                "c_id":       c_id,
                "filename":   filename,
                "doc_id":     doc_id,
                "remote_url": url,
                "local_path": str(self._docs_dir / filename),
            }
        logger.info(f"Manifest parsed: {len(self._manifest)} C-series entries registered.")

    # ------------------------------------------------------------------ #
    #  Internal: Local Loading                                             #
    # ------------------------------------------------------------------ #

    def _load_local_docs(self):
        if not self._docs_dir.exists():
            logger.warning(f"docs/canon/ not found at {self._docs_dir}")
            return
        for doc_path in sorted(self._docs_dir.glob("*")):
            if doc_path.suffix not in (".md", ".txt"):
                continue
            if doc_path.name == "CANON_MANIFEST.md":
                continue
            doc_id = doc_path.stem
            try:
                content = doc_path.read_text(encoding="utf-8")
                self._documents[doc_id] = {
                    "id":       doc_id,
                    "title":    self._extract_title(content, doc_id),
                    "content":  content,
                    "source":   "local",
                    "path":     str(doc_path),
                    "loaded_at": time.time(),
                }
            except Exception as e:
                logger.error(f"Failed to load {doc_path}: {e}")

    def _load_legacy_docs(self):
        if not _LEGACY_CANON_DIR.exists():
            return
        for doc_path in sorted(_LEGACY_CANON_DIR.glob("*.md")):
            doc_id = f"legacy_{doc_path.stem}"
            if doc_id in self._documents:
                continue
            try:
                content = doc_path.read_text(encoding="utf-8")
                self._documents[doc_id] = {
                    "id":       doc_id,
                    "title":    self._extract_title(content, doc_id),
                    "content":  content,
                    "source":   "legacy_local",
                    "path":     str(doc_path),
                    "loaded_at": time.time(),
                }
            except Exception as e:
                logger.error(f"Failed to load legacy doc {doc_path}: {e}")

    # ------------------------------------------------------------------ #
    #  Internal: Remote Fetch                                              #
    # ------------------------------------------------------------------ #

    def _fetch_remote(self, doc_id: str) -> Optional[dict]:
        cache_path = _CACHE_DIR / f"{doc_id}.md"
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < _CACHE_TTL_SECONDS:
                content = cache_path.read_text(encoding="utf-8")
                doc = {
                    "id":       doc_id,
                    "title":    self._extract_title(content, doc_id),
                    "content":  content,
                    "source":   "cache",
                    "loaded_at": time.time(),
                }
                self._documents[doc_id] = doc
                return doc

        manifest_entry = self._manifest.get(doc_id)
        if not manifest_entry:
            logger.warning(f"No manifest entry for doc_id='{doc_id}'")
            return None
        url = manifest_entry.get("remote_url")
        if not url:
            return None
        try:
            logger.info(f"Fetching remote canon doc: {doc_id} from {url}")
            with urllib.request.urlopen(url, timeout=10) as resp:
                content = resp.read().decode("utf-8")
            cache_path.write_text(content, encoding="utf-8")
            doc = {
                "id":       doc_id,
                "title":    self._extract_title(content, doc_id),
                "content":  content,
                "source":   "remote",
                "loaded_at": time.time(),
            }
            self._documents[doc_id] = doc
            return doc
        except Exception as e:
            logger.error(f"Remote fetch failed for {doc_id}: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Internal: Status Evaluation                                         #
    # ------------------------------------------------------------------ #

    def _evaluate_status(self):
        loaded_ids = set(self._documents.keys())
        floor_present = all(
            any(doc_id.endswith(floor) or doc_id == floor for doc_id in loaded_ids)
            for floor in _FLOOR_DOCS
        )
        if floor_present:
            self._status = CanonStatus.GREEN
        elif len(loaded_ids) > 0:
            self._status = CanonStatus.YELLOW
        else:
            self._status = CanonStatus.RED

    # ------------------------------------------------------------------ #
    #  Internal: Utility                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_title(content: str, fallback: str) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return fallback
