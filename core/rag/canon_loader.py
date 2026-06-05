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
_DEFAULT_REF = "feat/obs-rag"
_MIN_CHUNK_CHARS = 80   # discard whitespace-only / very short fragments
_MAX_CHUNK_CHARS = 4000 # hard ceiling; split further if exceeded
_REQUEST_DELAY = 0.05   # polite pause between raw-content requests (seconds)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CanonChunk:
    """A single retrievable unit from the Canon corpus."""

    canon_id: str        # full filename stem, e.g. "C140_Tool_Orchestration_as_Prehension_Implementation_Spec"
    source: str          # relative path within repo, e.g. "canon/C140_..."
    chunk_index: int     # 0-based position within the source file
    text: str            # the actual paragraph text
    size_bytes: int = 0  # original file size for provenance
    metadata: dict = field(default_factory=dict)

    @property
    def uid(self) -> str:
        return f"{self.canon_id}::{self.chunk_index}"

    def citation_header(self) -> str:
        """Short prefix injected into retrieved context blocks."""
        return f"[Canon: {self.canon_id}]"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_text(url: str) -> Optional[str]:
    """Return decoded text from *url* or None on failure."""
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
    """Return parsed JSON from *url* or None on failure."""
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
    """Derive a stable canon_id from the repo-relative file path."""
    return PurePosixPath(path).stem  # strips .md extension


def _split_into_chunks(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> List[str]:
    """
    Split *text* into paragraph chunks.

    Strategy:
    1. Split on blank lines (\n\n+) to get natural paragraphs.
    2. If any paragraph exceeds *max_chars*, further split on single\n.
    3. Filter out chunks shorter than _MIN_CHUNK_CHARS.
    """
    raw_paras = re.split(r"\n{2,}", text)
    chunks: List[str] = []
    for para in raw_paras:
        para = para.strip()
        if not para or len(para) < _MIN_CHUNK_CHARS:
            continue
        if len(para) <= max_chars:
            chunks.append(para)
        else:
            # Sub-split on single newline
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
    >>> loader = CanonLoader(ref="feat/obs-rag")
    >>> chunks = loader.load_all()
    >>> print(len(chunks), "chunks loaded")
    """

    def __init__(self, ref: str = _DEFAULT_REF) -> None:
        self.ref = ref
        self._loaded: bool = False
        self._chunks: List[CanonChunk] = []

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _list_canon_files(self) -> List[dict]:
        """
        Return GitHub tree entries for all *.md files under canon/.
        Falls back to empty list on API failure.
        """
        url = _GITHUB_API_TREE.format(ref=self.ref)
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

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_file(self, entry: dict) -> Iterator[CanonChunk]:
        """
        Fetch one Canon file and yield its chunks.
        *entry* is a GitHub tree blob dict with at minimum 'path' and 'size'.
        """
        path: str = entry["path"]
        size: int = entry.get("size", 0)
        canon_id = _canon_id_from_path(path)
        filename = PurePosixPath(path).name
        url = _CANON_BASE_URL.format(ref=self.ref, filename=filename)

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
                    "ref": self.ref,
                    "filename": filename,
                    "total_chunks": len(chunks),
                },
            )
        time.sleep(_REQUEST_DELAY)

    def load_all(self, force: bool = False) -> List[CanonChunk]:
        """
        Load all Canon chunks.  Cached after first call unless *force=True*.

        Returns
        -------
        List[CanonChunk]
            All paragraph chunks from all Canon documents, ordered by
            (canon_id, chunk_index).
        """
        if self._loaded and not force:
            return self._chunks

        entries = self._list_canon_files()
        if not entries:
            logger.warning("canon_loader: no Canon files discovered — check ref=%s", self.ref)
            return []

        logger.info("canon_loader: discovered %d Canon files on ref=%s", len(entries), self.ref)

        seen_uids: set = set()
        chunks: List[CanonChunk] = []
        for entry in entries:
            for chunk in self._load_file(entry):
                if chunk.uid in seen_uids:
                    continue  # idempotent re-ingestion guard
                seen_uids.add(chunk.uid)
                chunks.append(chunk)

        chunks.sort(key=lambda c: (c.canon_id, c.chunk_index))
        self._chunks = chunks
        self._loaded = True
        logger.info("canon_loader: loaded %d chunks from %d files", len(chunks), len(entries))
        return self._chunks

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def chunk_count(self) -> int:
        return len(self._chunks)

    def sources(self) -> List[str]:
        """Unique canon_ids present in the loaded corpus."""
        return sorted({c.canon_id for c in self._chunks})
