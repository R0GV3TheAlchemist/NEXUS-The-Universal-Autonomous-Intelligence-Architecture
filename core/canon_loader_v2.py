"""
core/canon_loader_v2.py

Canonical loader for GAIA canon documents (v2 API).

NOTE: This file was accidentally reduced to a one-line patch comment.
This restores the full CanonLoaderV2 class so that api/twin.py and all
dependent tests can import it.

Canon Ref: C01 (Sovereignty), C34 (Presence)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


_DEFAULT_CANON_DIR = Path(__file__).parent.parent / "canon"


class CanonLoaderV2:
    """
    Loads and indexes GAIA canon documents from the filesystem.

    Canon documents are Markdown files living under the /canon directory.
    Each file may have a YAML front-matter block (delimited by ---) that
    carries machine-readable metadata (id, title, tags, etc.).

    Usage::

        loader = CanonLoaderV2()
        doc = loader.get("C01")
        docs = loader.search("sovereignty")
    """

    def __init__(self, canon_dir: Optional[Path] = None) -> None:
        self._canon_dir: Path = canon_dir or _DEFAULT_CANON_DIR
        self._index: Dict[str, Dict[str, Any]] = {}
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Walk the canon directory and index all .md files."""
        if not self._canon_dir.exists():
            return
        for path in sorted(self._canon_dir.rglob("*.md")):
            self._index_file(path)
        self._loaded = True

    def _index_file(self, path: Path) -> None:
        raw = path.read_text(encoding="utf-8", errors="replace")
        meta, body = self._parse_front_matter(raw)
        doc_id = meta.get("id") or path.stem
        self._index[doc_id] = {
            "id":    doc_id,
            "path":  str(path),
            "meta":  meta,
            "body":  body,
            "title": meta.get("title", path.stem),
            "tags":  meta.get("tags", []),
        }

    @staticmethod
    def _parse_front_matter(raw: str):
        """Extract YAML-ish front matter between --- delimiters."""
        meta: Dict[str, Any] = {}
        body = raw
        if raw.startswith("---"):
            end = raw.find("\n---", 3)
            if end != -1:
                fm_block = raw[3:end].strip()
                body = raw[end + 4:].lstrip("\n")
                for line in fm_block.splitlines():
                    if ":" in line:
                        k, _, v = line.partition(":")
                        meta[k.strip()] = v.strip()
        return meta, body

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Return the indexed document for *doc_id*, or None."""
        self._ensure_loaded()
        return self._index.get(doc_id)

    def all(self) -> List[Dict[str, Any]]:
        """Return all indexed documents."""
        self._ensure_loaded()
        return list(self._index.values())

    def search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Naive full-text search across title, tags, and body."""
        self._ensure_loaded()
        q = query.lower()
        results = []
        for _key, doc in self._index.items():
            score = 0
            if q in doc["title"].lower():
                score += 3
            if any(q in str(t).lower() for t in doc["tags"]):
                score += 2
            if q in doc["body"].lower():
                score += 1
            if score:
                results.append((score, doc))
        results.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in results[:max_results]]

    def ids(self) -> List[str]:
        """Return all indexed document IDs."""
        self._ensure_loaded()
        return list(self._index.keys())

    def __len__(self) -> int:
        self._ensure_loaded()
        return len(self._index)

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        self._ensure_loaded()
        return iter(self._index.values())
