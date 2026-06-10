"""
Canon Loader — loads canon entries from various sources into memory.

Provides CanonStatus enum and CanonLoader class.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from core.canon.canon_entry import CanonEntry

log = logging.getLogger(__name__)


class CanonStatus(str, Enum):
    """Status of a canon entry within the loading pipeline."""

    UNKNOWN = "unknown"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    SKIPPED = "skipped"
    STALE = "stale"


@dataclass
class CanonLoadResult:
    """Result of a single canon-load operation."""

    entry_id: str = ""
    status: CanonStatus = CanonStatus.UNKNOWN
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "status": self.status.value,
            "error": self.error,
            "metadata": self.metadata,
        }


class CanonLoader:
    """Loads and caches CanonEntry objects."""

    def __init__(self) -> None:
        self._entries: Dict[str, CanonEntry] = {}
        log.info("CanonLoader initialised")

    def load(self, entry: CanonEntry) -> CanonLoadResult:
        self._entries[entry.entry_id] = entry
        return CanonLoadResult(
            entry_id=entry.entry_id,
            status=CanonStatus.LOADED,
        )

    def get(self, entry_id: str) -> Optional[CanonEntry]:
        return self._entries.get(entry_id)

    def list_ids(self) -> List[str]:
        return list(self._entries.keys())

    def get_status(self, entry_id: str) -> CanonStatus:
        if entry_id in self._entries:
            return CanonStatus.LOADED
        return CanonStatus.UNKNOWN

    def to_dict(self) -> dict:
        return {eid: e.to_dict() for eid, e in self._entries.items()}


_canon_loader: Optional[CanonLoader] = None


def get_canon_loader() -> CanonLoader:
    global _canon_loader
    if _canon_loader is None:
        _canon_loader = CanonLoader()
    return _canon_loader
