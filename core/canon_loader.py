"""
core/canon_loader.py
Canon Loader — loads canon entries from various sources into memory.

Provides CanonStatus enum, CanonLoader class, TF-IDF semantic search,
RegisterSignal enum, and helper functions used by tests.
"""
from __future__ import annotations

import logging
import math
import re
import string
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.canon.canon_entry import CanonEntry

log = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  Text-processing constants                                          #
# ------------------------------------------------------------------ #

_CHUNK_SIZE:    int = 400   # characters per chunk
_CHUNK_OVERLAP: int = 80    # overlap between consecutive chunks

_STOP_WORDS: frozenset = frozenset({
    "the", "and", "for", "are", "but", "not", "you", "all",
    "can", "her", "was", "one", "our", "out", "day", "get",
    "has", "him", "his", "how", "its", "had", "may", "new",
    "now", "old", "see", "two", "way", "who", "did", "its",
    "let", "put", "too", "use", "with", "this", "that", "from",
    "have", "they", "will", "what", "when", "your", "said",
    "each", "she", "been", "than", "then", "were", "also",
})

_PUNCT_RE = re.compile(r"[^\w\s]")


# ------------------------------------------------------------------ #
#  Text-processing helpers (exported for tests)                       #
# ------------------------------------------------------------------ #

def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, filter single-char and stop words."""
    text = _PUNCT_RE.sub(" ", text.lower())
    return [t for t in text.split() if len(t) > 1]


def _term_freq(text: str) -> Dict[str, float]:
    """Return normalised term-frequency dict for *text*."""
    tokens = _tokenize(text)
    if not tokens:
        return {}
    n = len(tokens)
    counts: Dict[str, int] = defaultdict(int)
    for t in tokens:
        counts[t] += 1
    return {t: c / n for t, c in counts.items()}


def _chunk_text(text: str) -> List[Tuple[str, int]]:
    """Split *text* into (chunk, char_offset) pairs with overlap."""
    if not text:
        return [("", 0)]
    chunks: List[Tuple[str, int]] = []
    step   = _CHUNK_SIZE - _CHUNK_OVERLAP
    offset = 0
    while offset < len(text):
        chunk = text[offset: offset + _CHUNK_SIZE]
        chunks.append((chunk, offset))
        offset += step
    return chunks


def _best_excerpt(
    text:   str,
    terms:  List[str],
    radius: int = 200,
) -> str:
    """Return a ~radius-char excerpt centred on the first matching term."""
    lower = text.lower()
    best_pos = -1
    for term in terms:
        idx = lower.find(term.lower())
        if idx != -1:
            best_pos = idx
            break
    if best_pos == -1:
        excerpt = text[:radius * 2]
    else:
        start   = max(0, best_pos - radius)
        excerpt = text[start: start + radius * 2]
    return excerpt.replace("\n", " ").strip()


# ------------------------------------------------------------------ #
#  TF-IDF index                                                       #
# ------------------------------------------------------------------ #

class _TFIDFIndex:
    """Lightweight in-process TF-IDF index over canon documents."""

    def __init__(self) -> None:
        self._built:  bool                         = False
        self._idf:    Dict[str, float]             = {}
        # doc_id -> list of (chunk_text, offset, tf_dict)
        self._chunks: Dict[str, List[Tuple[str, int, Dict[str, float]]]] = {}

    def build(self, documents: Dict[str, Dict[str, Any]]) -> None:
        self._chunks = {}
        df: Dict[str, int] = defaultdict(int)
        for doc_id, doc in documents.items():
            content  = doc.get("content", "")
            raw_chunks = _chunk_text(content)
            cdicts: List[Tuple[str, int, Dict[str, float]]] = []
            seen_terms_this_doc: set = set()
            for chunk_text, offset in raw_chunks:
                tf = _term_freq(chunk_text)
                cdicts.append((chunk_text, offset, tf))
                for term in tf:
                    if term not in seen_terms_this_doc:
                        df[term] += 1
                        seen_terms_this_doc.add(term)
            self._chunks[doc_id] = cdicts
        n_docs = max(1, len(documents))
        self._idf = {
            term: math.log((n_docs + 1) / (freq + 1)) + 1.0
            for term, freq in df.items()
        }
        self._built = True

    def query(
        self,
        query_text: str,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        if not self._built or not self._chunks:
            return []
        q_tokens = [t for t in _tokenize(query_text) if t not in _STOP_WORDS]
        if not q_tokens:
            q_tokens = _tokenize(query_text)  # fallback: use all tokens
        if not q_tokens:
            return []

        # Score every chunk; keep best chunk per doc
        best_per_doc: Dict[str, Tuple[float, str, int]] = {}
        n_docs = len(self._chunks)
        for doc_id, cdicts in self._chunks.items():
            for chunk_text, offset, tf in cdicts:
                # TF-IDF
                score = 0.0
                for term in q_tokens:
                    score += tf.get(term, 0.0) * self._idf.get(term, 0.0)

                # Position boost: earlier chunks score higher
                pos_boost = 1.0 / (1.0 + offset / max(1, _CHUNK_SIZE))
                score *= (1.0 + 0.15 * pos_boost)

                # Proximity bonus: reward terms appearing within 100 chars of each other
                if len(q_tokens) > 1 and score > 0:
                    lower = chunk_text.lower()
                    positions = []
                    for term in q_tokens:
                        idx = lower.find(term)
                        if idx != -1:
                            positions.append(idx)
                    if len(positions) >= 2:
                        span = max(positions) - min(positions)
                        if span < 100:
                            score *= 1.20

                prev = best_per_doc.get(doc_id)
                if prev is None or score > prev[0]:
                    best_per_doc[doc_id] = (score, chunk_text, offset)

        # Sort and trim
        ranked = sorted(best_per_doc.items(), key=lambda x: -x[1][0])
        out: List[Dict[str, Any]] = []
        for doc_id, (score, chunk_text, offset) in ranked:
            if score <= 0:
                continue
            out.append({
                "doc_id":  doc_id,
                "score":   score,
                "excerpt": _best_excerpt(chunk_text, q_tokens),
                "offset":  offset,
            })
            if len(out) >= max_results:
                break
        return out


# ------------------------------------------------------------------ #
#  Enums                                                              #
# ------------------------------------------------------------------ #

class CanonStatus(str, Enum):
    """Status of a canon entry within the loading pipeline."""
    UNKNOWN  = "unknown"
    LOADING  = "loading"
    LOADED   = "loaded"
    FAILED   = "failed"
    SKIPPED  = "skipped"
    STALE    = "stale"
    GREEN    = "green"   # alias used in tests
    AMBER    = "amber"
    RED      = "red"


class RegisterSignal(str, Enum):
    """Signal that accompanies a canon registration event."""
    STANDARD    = "standard"
    PRIORITY    = "priority"
    EXECUTIVE   = "executive"
    PROVISIONAL = "provisional"
    DEPRECATED  = "deprecated"


# ------------------------------------------------------------------ #
#  Data classes                                                       #
# ------------------------------------------------------------------ #

@dataclass
class CanonLoadResult:
    """Result of a single canon-load operation."""
    entry_id: str               = ""
    status:   CanonStatus       = CanonStatus.UNKNOWN
    error:    Optional[str]     = None
    metadata: Dict[str, Any]    = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "status":   self.status.value,
            "error":    self.error,
            "metadata": self.metadata,
        }


# ------------------------------------------------------------------ #
#  CanonLoader                                                        #
# ------------------------------------------------------------------ #

class CanonLoader:
    """Loads and caches CanonEntry objects; supports TF-IDF search."""

    def __init__(self) -> None:
        self._entries:   Dict[str, CanonEntry]        = {}
        self._documents: Dict[str, Dict[str, Any]]    = {}
        self._index:     _TFIDFIndex                  = _TFIDFIndex()
        self._loaded:    bool                         = False
        self._status:    CanonStatus                  = CanonStatus.UNKNOWN
        self._manifest:  Dict[str, Any]               = {}
        self._docs_dir:  Optional[str]                = None
        log.info("CanonLoader initialised")

    # ---- entry-level API ----

    def load(self, entry: Optional[CanonEntry] = None) -> CanonLoadResult:
        """Load a single CanonEntry, or perform a no-op 'load all' when called
        with no arguments (e.g. by server_state at startup)."""
        if entry is None:
            self._loaded = True
            self._status = CanonStatus.GREEN
            return CanonLoadResult(entry_id="", status=CanonStatus.LOADED)
        self._entries[entry.entry_id] = entry
        content = getattr(entry, "content", "") or getattr(entry, "text", "") or ""
        title   = getattr(entry, "title",   getattr(entry, "entry_id", ""))
        self._documents[entry.entry_id] = {
            "id":      entry.entry_id,
            "content": content,
            "title":   title,
            "source":  getattr(entry, "source", ""),
        }
        self._rebuild_index()
        return CanonLoadResult(entry_id=entry.entry_id, status=CanonStatus.LOADED)

    def _rebuild_index(self) -> None:
        self._index.build(self._documents)

    def get(self, entry_id: str) -> Optional[CanonEntry]:
        return self._entries.get(entry_id)

    def list_ids(self) -> List[str]:
        return list(self._entries.keys())

    def get_status(self, entry_id: str) -> CanonStatus:
        return CanonStatus.LOADED if entry_id in self._entries else CanonStatus.UNKNOWN

    def to_dict(self) -> dict:
        return {eid: e.to_dict() for eid, e in self._entries.items()}

    # ---- search API ----

    def search(
        self,
        query:       str,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """TF-IDF semantic search. Returns list of result dicts with
        keys: doc_id, title, excerpt, score."""
        if not self._documents:
            return []
        results = self._index.query(query, max_results=max_results)
        enriched = []
        for r in results:
            doc = self._documents.get(r["doc_id"], {})
            enriched.append({
                "doc_id":  r["doc_id"],
                "title":   doc.get("title", ""),
                "excerpt": r["excerpt"],
                "score":   r["score"],
            })
        return enriched

    def search_v2(
        self,
        query:       str,
        max_results: int = 5,
        min_score:   float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Like search() but supports a min_score threshold."""
        raw = self.search(query, max_results=max_results * 2)
        return [
            r for r in raw if r["score"] >= min_score
        ][:max_results]


# ------------------------------------------------------------------ #
#  Module-level singleton                                             #
# ------------------------------------------------------------------ #

_canon_loader: Optional[CanonLoader] = None


def get_canon_loader() -> CanonLoader:
    global _canon_loader
    if _canon_loader is None:
        _canon_loader = CanonLoader()
    return _canon_loader
