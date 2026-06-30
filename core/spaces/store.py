"""SpaceStore — in-memory registry of all active Spaces.

The store is the single source of truth for which Spaces currently exist.
It is intentionally storage-agnostic: a production deployment can swap in
a persistent backend (Redis, Postgres, etc.) by subclassing or replacing
this class. The interface remains identical.

Thread safety: the store uses a simple dict. For concurrent deployments
wrap with a lock or use an async-safe variant.
"""
from __future__ import annotations

from typing import Dict, Iterator, List, Optional

from core.spaces.model import Space, SpaceStatus


class SpaceStore:
    """In-memory store for Space objects.

    Spaces are indexed by space_id (primary key) and name (secondary,
    must be unique). Both indices are kept in sync on every mutation.
    """

    def __init__(self) -> None:
        self._by_id: Dict[str, Space] = {}
        self._id_by_name: Dict[str, str] = {}  # name -> space_id

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def save(self, space: Space) -> None:
        """Insert or update a Space. Updates both indices."""
        existing = self._by_id.get(space.space_id)
        if existing is not None and existing.name != space.name:
            del self._id_by_name[existing.name]
        if space.name in self._id_by_name and self._id_by_name[space.name] != space.space_id:
            raise ValueError(
                f"A different Space with name '{space.name}' already exists."
            )
        self._by_id[space.space_id] = space
        self._id_by_name[space.name] = space.space_id

    def delete(self, space_id: str) -> None:
        """Hard-delete a Space from the store (use set_status(DESTROYED) for soft-delete)."""
        space = self._by_id.pop(space_id, None)
        if space is not None:
            self._id_by_name.pop(space.name, None)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get(self, space_id: str) -> Optional[Space]:
        return self._by_id.get(space_id)

    def get_by_name(self, name: str) -> Optional[Space]:
        sid = self._id_by_name.get(name)
        return self._by_id.get(sid) if sid else None

    def require(self, space_id: str) -> Space:
        space = self.get(space_id)
        if space is None:
            raise KeyError(f"Space '{space_id}' not found.")
        return space

    def list_all(self) -> List[Space]:
        return list(self._by_id.values())

    def list_by_status(self, status: SpaceStatus) -> List[Space]:
        return [s for s in self._by_id.values() if s.status == status]

    def list_for_principal(self, principal_id: str) -> List[Space]:
        return [s for s in self._by_id.values() if s.is_member(principal_id)]

    def search(self, query: str) -> List[Space]:
        q = query.lower()
        return [
            s for s in self._by_id.values()
            if q in s.name.lower()
            or q in s.description.lower()
            or any(q in tag.lower() for tag in s.tags)
        ]

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, space_id: str) -> bool:
        return space_id in self._by_id

    def __iter__(self) -> Iterator[Space]:
        return iter(self._by_id.values())
