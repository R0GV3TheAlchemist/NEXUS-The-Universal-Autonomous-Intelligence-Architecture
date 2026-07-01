"""
MemoryPersistence — write-through disk backing for MemoryStore.

Directory layout under GAIA_ROOT:

  gaians/<gaian_id>/memory/
    fragments/
      <fragment_id>.json     — one file per memory fragment
    epochs/
      <epoch_id>.json        — one file per memory epoch
    stats.json               — lightweight stats snapshot

Write-through contract:
  - save_fragment() is called immediately when a fragment is added
    to the MemoryStore (no buffering).
  - save_epoch() is called when an epoch closes.
  - load_all() is called once at boot to restore the MemoryStore
    from disk.
  - delete_fragment() supports memory consolidation / pruning.

The fragment JSON schema mirrors MemoryFragment fields exactly,
so any future migration is a straightforward jq transform.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.persistence.store import PersistenceStore


# The in-memory classes we persist — imported lazily to avoid
# circular imports at module load time.
def _import_memory():
    from core.memory.store import MemoryFragment, MemoryKind, MemoryScope
    return MemoryFragment, MemoryKind, MemoryScope


class MemoryPersistence:
    """
    Disk-backed persistence for a single GAIAN\'s MemoryStore.

    One MemoryPersistence instance per GAIAN, constructed by
    PersistenceManager at boot.
    """

    FRAGMENTS_DIR = "fragments"
    EPOCHS_DIR    = "epochs"
    STATS_FILE    = "stats.json"

    def __init__(self, store: PersistenceStore, gaian_id: str) -> None:
        self._store     = store
        self._gaian_id  = gaian_id
        self._base      = f"gaians/{gaian_id}/memory"

    def _frag_path(self, fragment_id: str) -> str:
        return f"{self._base}/{self.FRAGMENTS_DIR}/{fragment_id}.json"

    def _epoch_path(self, epoch_id: str) -> str:
        return f"{self._base}/{self.EPOCHS_DIR}/{epoch_id}.json"

    # ------------------------------------------------------------------
    # Fragments
    # ------------------------------------------------------------------

    def save_fragment(self, fragment) -> None:
        """Write-through: persist one MemoryFragment immediately."""
        self._store.write(self._frag_path(fragment.fragment_id), {
            "fragment_id":  fragment.fragment_id,
            "gaian_id":     fragment.gaian_id,
            "content":      fragment.content,
            "kind":         fragment.kind.value if hasattr(fragment.kind, "value") else str(fragment.kind),
            "scope":        fragment.scope.value if hasattr(fragment.scope, "value") else str(fragment.scope),
            "importance":   fragment.importance,
            "tags":         list(fragment.tags),
            "created_at":   fragment.created_at.isoformat() if hasattr(fragment, "created_at") else None,
            "epoch_id":     getattr(fragment, "epoch_id", None),
            "source":       getattr(fragment, "source", None),
            "related_gaian_id": getattr(fragment, "related_gaian_id", None),
        })

    def load_fragments(self) -> List[Dict[str, Any]]:
        """Load all fragment dicts from disk. Caller reconstructs objects."""
        names = self._store.list_dir(f"{self._base}/{self.FRAGMENTS_DIR}")
        fragments = []
        for name in names:
            if not name.endswith(".json"):
                continue
            fid = name[:-5]  # strip .json
            data = self._store.read(self._frag_path(fid))
            if data:
                fragments.append(data)
        return fragments

    def delete_fragment(self, fragment_id: str) -> None:
        self._store.delete(self._frag_path(fragment_id))

    def fragment_count(self) -> int:
        return len(self._store.list_dir(f"{self._base}/{self.FRAGMENTS_DIR}"))

    # ------------------------------------------------------------------
    # Epochs
    # ------------------------------------------------------------------

    def save_epoch(self, epoch) -> None:
        """Persist a closed memory epoch."""
        self._store.write(self._epoch_path(epoch.epoch_id), {
            "epoch_id":      epoch.epoch_id,
            "gaian_id":      epoch.gaian_id,
            "opened_at":     epoch.opened_at.isoformat() if hasattr(epoch, "opened_at") else None,
            "closed_at":     epoch.closed_at.isoformat() if hasattr(epoch, "closed_at") and epoch.closed_at else None,
            "fragment_count": getattr(epoch, "fragment_count", 0),
            "summary":       getattr(epoch, "summary", ""),
        })

    def load_epochs(self) -> List[Dict[str, Any]]:
        names = self._store.list_dir(f"{self._base}/{self.EPOCHS_DIR}")
        epochs = []
        for name in names:
            if not name.endswith(".json"):
                continue
            eid = name[:-5]
            data = self._store.read(self._epoch_path(eid))
            if data:
                epochs.append(data)
        return epochs

    # ------------------------------------------------------------------
    # Stats snapshot
    # ------------------------------------------------------------------

    def save_stats(self, stats: Dict[str, Any]) -> None:
        self._store.write(f"{self._base}/{self.STATS_FILE}", stats)

    def load_stats(self) -> Optional[Dict[str, Any]]:
        return self._store.read(f"{self._base}/{self.STATS_FILE}")
