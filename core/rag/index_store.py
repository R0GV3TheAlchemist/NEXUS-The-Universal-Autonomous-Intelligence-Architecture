"""
core/rag/index_store.py
~~~~~~~~~~~~~~~~~~~~~~~
Resolves and manages the on-disk path for the GAIA-OS Canon vector index.

Responsibilities
----------------
1. Canonical path resolution — one well-known location so every process
   finds the same index file without configuration.
2. Corpus fingerprint — a SHA-256 digest of (canon_id, chunk_count) pairs,
   sorted and concatenated.  If the digest changes between runs the pipeline
   drops the old index and re-embeds from scratch.  This keeps the index
   honest when Canon documents are added, removed, or substantially edited.
3. Sidecar file management — the fingerprint is written to
   <db_path>.fingerprint next to the SQLite file so it survives process
   restarts without an extra DB table.

Design decisions
----------------
* Uses stdlib only (hashlib, pathlib, os) — no new dependencies.
* Thread-safe fingerprint read/write via a simple file-lock convention
  (write to .tmp then atomic rename) on POSIX; on Windows falls back to
  direct write because os.replace() is atomic there too.
* Exposes a clean IndexStore dataclass so callers never hard-code paths.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .canon_loader import CanonChunk

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default directory for all GAIA-OS data files.
_DEFAULT_DATA_DIR = Path.home() / ".gaia" / "data"

#: Filename for the Canon SQLite vector index.
_CANON_DB_FILENAME = "canon_index.db"

#: Sidecar filename for the corpus fingerprint.
_FINGERPRINT_FILENAME = "canon_index.db.fingerprint"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class IndexStore:
    """
    Encapsulates the on-disk location of the Canon vector index.

    Attributes
    ----------
    db_path       : Absolute path to the SQLite file.
    fingerprint_path : Absolute path to the sidecar fingerprint file.
    data_dir      : Parent directory (created on demand).
    """
    data_dir: Path
    db_path: Path = field(init=False)
    fingerprint_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.db_path = self.data_dir / _CANON_DB_FILENAME
        self.fingerprint_path = self.data_dir / _FINGERPRINT_FILENAME

    def ensure_dir(self) -> None:
        """Create the data directory (and parents) if it does not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def db_exists(self) -> bool:
        return self.db_path.exists() and self.db_path.stat().st_size > 0

    def read_fingerprint(self) -> Optional[str]:
        """Return the stored fingerprint string, or None if absent."""
        try:
            return self.fingerprint_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return None

    def write_fingerprint(self, digest: str) -> None:
        """Atomically write *digest* to the sidecar file."""
        self.ensure_dir()
        tmp = self.fingerprint_path.with_suffix(".tmp")
        tmp.write_text(digest, encoding="utf-8")
        os.replace(tmp, self.fingerprint_path)  # atomic on POSIX + Windows

    def delete_db(self) -> None:
        """Remove the SQLite file and fingerprint sidecar (for forced re-ingest)."""
        if self.db_path.exists():
            self.db_path.unlink()
        if self.fingerprint_path.exists():
            self.fingerprint_path.unlink()

    def __str__(self) -> str:
        return str(self.db_path)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def default_store(data_dir: Optional[Path] = None) -> IndexStore:
    """
    Return an IndexStore rooted at *data_dir* (default: ~/.gaia/data/).
    Does NOT create the directory — call store.ensure_dir() when ready to write.
    """
    return IndexStore(data_dir=data_dir or _DEFAULT_DATA_DIR)


# ---------------------------------------------------------------------------
# Fingerprint computation
# ---------------------------------------------------------------------------

def compute_fingerprint(chunks: "List[CanonChunk]") -> str:
    """
    Compute a stable SHA-256 fingerprint of the Canon corpus.

    The fingerprint is derived from a sorted list of
    ``"<canon_id>:<total_chunks>"`` strings, one per unique Canon document.
    Sorting makes it order-independent across discovery runs.

    Returns the hex digest string (64 chars).
    """
    # Build per-document summary: canon_id → number of chunks seen
    doc_chunk_counts: dict = {}
    for chunk in chunks:
        doc_chunk_counts[chunk.canon_id] = doc_chunk_counts.get(chunk.canon_id, 0) + 1

    # Sorted for stability
    entries = sorted(f"{cid}:{cnt}" for cid, cnt in doc_chunk_counts.items())
    payload = "\n".join(entries).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fingerprints_match(
    chunks: "List[CanonChunk]",
    store: IndexStore,
) -> bool:
    """
    Return True if the corpus fingerprint matches what is stored on disk.
    Returns False if the sidecar file is absent, malformed, or stale.
    """
    stored = store.read_fingerprint()
    if stored is None:
        return False
    current = compute_fingerprint(chunks)
    return stored == current
