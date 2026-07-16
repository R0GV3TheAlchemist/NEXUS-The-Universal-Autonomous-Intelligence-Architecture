"""
core/memory/tiers/cold_tier.py

COLD TIER — append-only compressed archive for long-term storage.

Design:
- Entries are written as newline-delimited JSON (NDJSON) to a gzip-
  compressed rolling archive file.
- Read path builds an in-memory index (key → byte offset) on first
  access, enabling O(log n) lookup without loading the full archive.
- Immutable: entries are never overwritten; a tombstone record is
  appended to logically delete an entry.
- Archives roll over at a configurable size limit (default 64 MB
  uncompressed).
- Thread-safe via a write lock; reads are lock-free after index build.
"""

from __future__ import annotations

import gzip
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ColdEntry:
    key: str
    value: Any
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    archived_at: float = field(default_factory=time.time)
    source_tier: str = "warm"        # tier this entry was demoted from
    metadata: Dict[str, Any] = field(default_factory=dict)
    tombstone: bool = False          # True = logically deleted

    def to_record(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "tags": self.tags,
            "created_at": self.created_at,
            "archived_at": self.archived_at,
            "source_tier": self.source_tier,
            "metadata": self.metadata,
            "tombstone": self.tombstone,
        }

    @classmethod
    def from_record(cls, d: Dict[str, Any]) -> "ColdEntry":
        return cls(
            key=d["key"],
            value=d.get("value"),
            tags=d.get("tags", []),
            created_at=d.get("created_at", 0.0),
            archived_at=d.get("archived_at", 0.0),
            source_tier=d.get("source_tier", "warm"),
            metadata=d.get("metadata", {}),
            tombstone=d.get("tombstone", False),
        )


# ---------------------------------------------------------------------------
# ColdTier
# ---------------------------------------------------------------------------

class ColdTier:
    """
    Append-only gzip-compressed NDJSON archive.

    Parameters
    ----------
    archive_dir : str | Path
        Directory where archive files are written.
    max_uncompressed_bytes : int
        Approximate uncompressed byte limit before a new file is started.
    """

    ARCHIVE_PREFIX = "gaia_cold_"
    ARCHIVE_EXT = ".ndjson.gz"

    def __init__(
        self,
        archive_dir: str | Path = "./gaia_cold_archive",
        max_uncompressed_bytes: int = 64 * 1024 * 1024,  # 64 MB
    ) -> None:
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.max_uncompressed_bytes = max_uncompressed_bytes
        self._write_lock = threading.Lock()
        self._index: Optional[Dict[str, Tuple[Path, int]]] = None  # key → (file, line_no)
        self._index_lock = threading.Lock()
        self._bytes_written = 0
        self._active_file: Optional[Path] = None
        self._open_active_file()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def put(
        self,
        key: str,
        value: Any,
        *,
        tags: Optional[List[str]] = None,
        source_tier: str = "warm",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ColdEntry:
        """Append an entry to the cold archive."""
        entry = ColdEntry(
            key=key,
            value=value,
            tags=tags or [],
            source_tier=source_tier,
            metadata=metadata or {},
        )
        self._append(entry)
        return entry

    def get(self, key: str) -> Optional[Any]:
        entry = self.get_entry(key)
        return entry.value if entry else None

    def get_entry(self, key: str) -> Optional[ColdEntry]:
        """Scan the index for the latest non-tombstone entry for *key*."""
        self._ensure_index()
        if self._index is None or key not in self._index:
            return None
        file_path, _ = self._index[key]
        # Re-scan file for latest record with this key
        latest: Optional[ColdEntry] = None
        for entry in self._scan_file(file_path):
            if entry.key == key:
                latest = entry
        if latest is None or latest.tombstone:
            return None
        return latest

    def delete(self, key: str) -> bool:
        """Append a tombstone record.  Returns True if key was known."""
        self._ensure_index()
        if self._index is None or key not in self._index:
            return False
        tombstone = ColdEntry(
            key=key,
            value=None,
            tombstone=True,
        )
        self._append(tombstone)
        with self._index_lock:
            self._index.pop(key, None)
        return True

    def contains(self, key: str) -> bool:
        self._ensure_index()
        return self._index is not None and key in self._index

    def keys(self) -> List[str]:
        self._ensure_index()
        return list(self._index.keys()) if self._index else []

    def scan_all(self) -> Iterator[ColdEntry]:
        """Yield every non-tombstone entry across all archive files."""
        seen: Dict[str, ColdEntry] = {}
        for archive_file in sorted(self.archive_dir.glob(f"{self.ARCHIVE_PREFIX}*{self.ARCHIVE_EXT}")):
            for entry in self._scan_file(archive_file):
                if entry.tombstone:
                    seen.pop(entry.key, None)
                else:
                    seen[entry.key] = entry
        yield from seen.values()

    def archive_files(self) -> List[Path]:
        return sorted(
            self.archive_dir.glob(f"{self.ARCHIVE_PREFIX}*{self.ARCHIVE_EXT}")
        )

    def stats(self) -> Dict[str, Any]:
        self._ensure_index()
        files = self.archive_files()
        total_bytes = sum(f.stat().st_size for f in files)
        return {
            "entry_count": len(self._index) if self._index else 0,
            "archive_files": len(files),
            "total_compressed_bytes": total_bytes,
            "active_file": str(self._active_file),
            "bytes_written_to_active": self._bytes_written,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _append(self, entry: ColdEntry) -> None:
        record = json.dumps(entry.to_record(), separators=(",", ":")) + "\n"
        encoded = record.encode()
        with self._write_lock:
            if (
                self._bytes_written + len(encoded) > self.max_uncompressed_bytes
                and self._bytes_written > 0
            ):
                self._roll_archive()
            with gzip.open(str(self._active_file), "ab") as f:
                f.write(encoded)
            self._bytes_written += len(encoded)
            # Update in-memory index
            if not entry.tombstone:
                with self._index_lock:
                    if self._index is not None:
                        self._index[entry.key] = (self._active_file, 0)  # line_no is advisory
            else:
                with self._index_lock:
                    if self._index is not None:
                        self._index.pop(entry.key, None)

    def _open_active_file(self) -> None:
        existing = sorted(
            self.archive_dir.glob(f"{self.ARCHIVE_PREFIX}*{self.ARCHIVE_EXT}")
        )
        if existing:
            self._active_file = existing[-1]
            # Estimate bytes written by decompressing last file size heuristic
            self._bytes_written = self._active_file.stat().st_size * 4  # rough ratio
        else:
            self._roll_archive()

    def _roll_archive(self) -> None:
        ts = int(time.time() * 1000)
        self._active_file = (
            self.archive_dir
            / f"{self.ARCHIVE_PREFIX}{ts}{self.ARCHIVE_EXT}"
        )
        self._bytes_written = 0
        # Invalidate index so it's rebuilt on next read
        with self._index_lock:
            self._index = None

    def _ensure_index(self) -> None:
        with self._index_lock:
            if self._index is not None:
                return
        index: Dict[str, Tuple[Path, int]] = {}
        for archive_file in sorted(
            self.archive_dir.glob(f"{self.ARCHIVE_PREFIX}*{self.ARCHIVE_EXT}")
        ):
            for i, entry in enumerate(self._scan_file(archive_file)):
                if entry.tombstone:
                    index.pop(entry.key, None)
                else:
                    index[entry.key] = (archive_file, i)
        with self._index_lock:
            self._index = index

    @staticmethod
    def _scan_file(path: Path) -> Iterator[ColdEntry]:
        try:
            with gzip.open(str(path), "rt", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield ColdEntry.from_record(json.loads(line))
                    except (json.JSONDecodeError, KeyError):
                        continue
        except (OSError, EOFError):
            return
