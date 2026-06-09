"""
canon_loader.py
~~~~~~~~~~~~~~~
Loads every Canon document from the canon/ directory of the GAIA-OS
GitHub repository, splits each file into paragraph-level chunks, and
returns a list of CanonChunk objects ready for vector-store ingestion.

Design decisions
----------------
* Uses the GitHub raw-content URL so the loader works both in CI and at
  runtime without requiring a local checkout.
* Splits on double-newline (paragraph boundary) rather than fixed token
  windows so Canon headings stay attached to their first paragraph —
  this preserves semantic coherence for embedding.
* Deduplicates by (canon_id, chunk_index) so re-ingestion is idempotent.
* Gracefully skips files that return non-200 HTTP status rather than
  raising, so a single bad file never blocks the full corpus load.
"""

from __future__ import annotations

import logging
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterator, List, Optional

try:
    import httpx
    _HTTP_CLIENT = "httpx"
except ImportError:  # pragma: no cover
    import urllib.request as _urllib
    _HTTP_CLIENT = "urllib"

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CANON_BASE_URL = (
    "https://raw.githubusercontent.com/R0GV3TheAlchemist/GAIA-OS/"
    "{ref}/canon/{filename}"
)
_GITHUB_API_TREE = (
    "https://api.github.com/repos/R0GV3TheAlchemist/GAIA-OS/"
    "git/trees/{ref}?recursive=1"
)
_DEFAULT_REF = "main"
_MIN_CHUNK_CHARS = 80
_MAX_CHUNK_CHARS = 4000
_REQUEST_DELAY = 0.05


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CanonChunk:
    """A single retrievable unit from the Canon corpus."""

    canon_id:    str
    source:      str
    chunk_index: int
    text:        str
    size_bytes:  int  = 0
    metadata:    dict = field(default_factory=dict)

    @property
    def uid(self) -> str:
        return f"{self.canon_id}::{self.chunk_index}"

    def citation_header(self) -> str:
        return f"[Canon: {self.canon_id}]"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """
    Tokenise *text* into lowercase alphanumeric tokens.

    Tokens shorter than 2 characters are discarded to reduce noise.
    """
    return [tok for tok in re.findall(r"[a-z0-9]+", text.lower()) if len(tok) > 1]


def _term_freq(text: str) -> dict[str, float]:
    """
    Return relative term frequencies for *text*.

    Each token's frequency is its count divided by the total number of
    tokens, giving a value in the range (0, 1].  An empty or
    whitespace-only string returns an empty dict.
    """
    tokens = _tokenize(text)
    if not tokens:
        return {}
    total = len(tokens)
    return {term: count / total for term, count in Counter(tokens).items()}


def _chunk_text(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> List[str]:
    """
    Split *text* into non-empty chunks of at most *max_chars* characters.

    Splits first on paragraph boundaries (double newline), then on
    single newlines for oversized paragraphs.  Chunks shorter than
    ``_MIN_CHUNK_CHARS`` are silently dropped to avoid noise.
    """
    return _split_into_chunks(text, max_chars=max_chars)


def _best_excerpt(
    text: str,
    query_tokens: List[str],
    window: int = 300,
) -> str:
    """
    Return the best excerpt from *text* for the given *query_tokens*.

    Scans *text* in overlapping windows of *window* characters and returns
    the window with the highest number of query token hits.  Falls back to
    the first *window* characters when no tokens match.

    Parameters
    ----------
    text:
        The full chunk or document text to excerpt from.
    query_tokens:
        Pre-tokenised query terms (lowercase alphanumeric).
    window:
        Character width of the excerpt window.

    Returns
    -------
    str
        Best-matching excerpt, stripped of leading/trailing whitespace.
    """
    if not text:
        return ""
    if not query_tokens or len(text) <= window:
        return text[:window].strip()

    token_set = set(query_tokens)
    best_start = 0
    best_score = -1

    step = max(1, window // 4)
    for start in range(0, len(text) - window + 1, step):
        snippet = text[start : start + window].lower()
        score = sum(1 for tok in token_set if tok in snippet)
        if score > best_score:
            best_score = score
            best_start = start

    return text[best_start : best_start + window].strip()


def _fetch_text(url: str) -> Optional[str]:
    try:
        if _HTTP_CLIENT == "httpx":
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            logger.warning("canon_loader: HTTP %s for %s", resp.status_code, url)
            return None
        else:
            with _urllib.urlopen(url, timeout=15) as r:  # type: ignore[attr-defined]
                if r.status == 200:
                    return r.read().decode("utf-8", errors="replace")
            return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("canon_loader: fetch failed for %s — %s", url, exc)
        return None


def _fetch_json(url: str) -> Optional[dict]:
    try:
        if _HTTP_CLIENT == "httpx":
            resp = httpx.get(url, timeout=20, follow_redirects=True)
            if resp.status_code == 200:
                return resp.json()
            return None
        else:
            import json
            with _urllib.urlopen(url, timeout=20) as r:  # type: ignore[attr-defined]
                if r.status == 200:
                    return json.loads(r.read().decode("utf-8"))
            return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("canon_loader: JSON fetch failed for %s — %s", url, exc)
        return None


def _canon_id_from_path(path: str) -> str:
    return PurePosixPath(path).stem


def _split_into_chunks(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> List[str]:
    raw_paras = re.split(r"\n{2,}", text)
    chunks: List[str] = []
    for para in raw_paras:
        para = para.strip()
        if not para or len(para) < _MIN_CHUNK_CHARS:
            continue
        if len(para) <= max_chars:
            chunks.append(para)
        else:
            for sub in para.split("\n"):
                sub = sub.strip()
                if len(sub) >= _MIN_CHUNK_CHARS:
                    chunks.append(sub[:max_chars])
    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class CanonLoader:
    """
    Discovers and loads all Canon documents from the GAIA-OS repository.

    Usage
    -----
    >>> loader = CanonLoader(ref="main")
    >>> chunks = loader.load()          # or loader.load_all()
    >>> print(len(chunks), "chunks loaded")
    """

    def __init__(self, ref: str = _DEFAULT_REF) -> None:
        self.ref      = ref
        self._loaded: bool           = False
        self._chunks: List[CanonChunk] = []

    def _list_canon_files(self) -> List[dict]:
        url  = _GITHUB_API_TREE.format(ref=self.ref)
        data = _fetch_json(url)
        if not data or "tree" not in data:
            logger.error("canon_loader: could not fetch repo tree from %s", url)
            return []
        return [
            entry for entry in data["tree"]
            if entry.get("type") == "blob"
            and entry["path"].startswith("canon/")
            and entry["path"].endswith(".md")
        ]

    def _load_file(self, entry: dict) -> Iterator[CanonChunk]:
        path:     str = entry["path"]
        size:     int = entry.get("size", 0)
        canon_id      = _canon_id_from_path(path)
        filename      = PurePosixPath(path).name
        url           = _CANON_BASE_URL.format(ref=self.ref, filename=filename)

        text = _fetch_text(url)
        if not text:
            logger.warning("canon_loader: skipping %s (empty or fetch error)", path)
            return

        chunks = _split_into_chunks(text)
        for idx, chunk_text in enumerate(chunks):
            yield CanonChunk(
                canon_id=canon_id,
                source=path,
                chunk_index=idx,
                text=chunk_text,
                size_bytes=size,
                metadata={
                    "ref":          self.ref,
                    "filename":     filename,
                    "total_chunks": len(chunks),
                },
            )
        time.sleep(_REQUEST_DELAY)

    def load_all(self, force: bool = False) -> List[CanonChunk]:
        """
        Load all Canon chunks.  Cached after first call unless *force=True*.
        """
        if self._loaded and not force:
            return self._chunks

        entries = self._list_canon_files()
        if not entries:
            logger.warning("canon_loader: no Canon files discovered — check ref=%s", self.ref)
            return []

        logger.info("canon_loader: discovered %d Canon files on ref=%s", len(entries), self.ref)

        seen_uids: set        = set()
        chunks: List[CanonChunk] = []
        for entry in entries:
            for chunk in self._load_file(entry):
                if chunk.uid in seen_uids:
                    continue
                seen_uids.add(chunk.uid)
                chunks.append(chunk)

        chunks.sort(key=lambda c: (c.canon_id, c.chunk_index))
        self._chunks  = chunks
        self._loaded  = True
        logger.info("canon_loader: loaded %d chunks from %d files", len(chunks), len(entries))
        return self._chunks

    def load(self, force: bool = False) -> List[CanonChunk]:
        """Alias for load_all(). Called by RAGPipeline.ingest_canon()."""
        return self.load_all(force=force)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def chunk_count(self) -> int:
        return len(self._chunks)

    def sources(self) -> List[str]:
        return sorted({c.canon_id for c in self._chunks})
