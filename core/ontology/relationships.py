"""GAIA Relationship Graph Engine — Canon C03 Section 4.

Implements a directed, weighted, mutable graph of ontological relationships.
The canonical relationship tree from C03:

  ATLAS → is served by → GAIA
  GAIA → instantiates → Gaian
  Gaian → partners with → Human Principal
  Gaian → operates via → Runtime
  Gaian → surfaces through → Shell
  Gaian → bounded by → Permission Envelope
  Gaian → acts upon → ATLAS Nodes
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class RelationshipType(str, Enum):
    """Canonical relationship types derived from C03 §4."""
    IS_SERVED_BY = "IS_SERVED_BY"           # ATLAS → GAIA
    INSTANTIATES = "INSTANTIATES"           # GAIA → Gaian
    PARTNERS_WITH = "PARTNERS_WITH"         # Gaian → Human Principal
    OPERATES_VIA = "OPERATES_VIA"           # Gaian → Runtime
    SURFACES_THROUGH = "SURFACES_THROUGH"   # Gaian → Shell
    BOUNDED_BY = "BOUNDED_BY"               # Gaian → Permission Envelope
    ACTS_UPON = "ACTS_UPON"                 # Gaian → ATLAS Node
    CONTAINS = "CONTAINS"                   # General containment
    REFERENCES = "REFERENCES"               # Soft reference (canon cross-ref)
    SUPERSEDES = "SUPERSEDES"               # Amendment / version hierarchy


@dataclass
class Relationship:
    """A single directed, weighted, typed relationship between two entities."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    type: RelationshipType = RelationshipType.REFERENCES
    weight: float = 1.0          # 0.0 = minimal coupling, 1.0 = full dependence
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"<Relationship {self.source_id[:8]}→{self.target_id[:8]} "
            f"type={self.type.value} weight={self.weight:.2f}>"
        )


class RelationshipGraph:
    """Directed, weighted, mutable graph of GAIA ontological relationships.

    The graph is the living map of how all GAIA entities relate to one another.
    It is the backbone of the World Fabric — C14 §3.
    """

    def __init__(self) -> None:
        # adjacency: source_id → list of Relationship
        self._outgoing: dict[str, list[Relationship]] = {}
        # reverse index: target_id → list of Relationship
        self._incoming: dict[str, list[Relationship]] = {}
        # id → Relationship for O(1) lookup
        self._index: dict[str, Relationship] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType,
        weight: float = 1.0,
        metadata: Optional[dict] = None,
    ) -> Relationship:
        """Create and register a new directed relationship."""
        rel = Relationship(
            source_id=source_id,
            target_id=target_id,
            type=rel_type,
            weight=max(0.0, min(1.0, weight)),
            metadata=metadata or {},
        )
        self._outgoing.setdefault(source_id, []).append(rel)
        self._incoming.setdefault(target_id, []).append(rel)
        self._index[rel.id] = rel
        return rel

    def remove_relationship(self, relationship_id: str) -> bool:
        """Deactivate a relationship by ID. Returns True if found."""
        rel = self._index.get(relationship_id)
        if not rel:
            return False
        rel.is_active = False
        return True

    def update_weight(self, relationship_id: str, new_weight: float) -> bool:
        """Adjust the coupling weight of an existing relationship."""
        rel = self._index.get(relationship_id)
        if not rel:
            return False
        rel.weight = max(0.0, min(1.0, new_weight))
        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_outgoing(
        self,
        entity_id: str,
        rel_type: Optional[RelationshipType] = None,
        active_only: bool = True,
    ) -> list[Relationship]:
        """All relationships where entity_id is the source."""
        rels = self._outgoing.get(entity_id, [])
        if active_only:
            rels = [r for r in rels if r.is_active]
        if rel_type:
            rels = [r for r in rels if r.type == rel_type]
        return rels

    def get_incoming(
        self,
        entity_id: str,
        rel_type: Optional[RelationshipType] = None,
        active_only: bool = True,
    ) -> list[Relationship]:
        """All relationships where entity_id is the target."""
        rels = self._incoming.get(entity_id, [])
        if active_only:
            rels = [r for r in rels if r.is_active]
        if rel_type:
            rels = [r for r in rels if r.type == rel_type]
        return rels

    def get_neighbors(
        self,
        entity_id: str,
        direction: str = "outgoing",
        rel_type: Optional[RelationshipType] = None,
    ) -> list[str]:
        """Return IDs of neighboring entities. direction: 'outgoing' | 'incoming' | 'both'."""
        neighbors: list[str] = []
        if direction in ("outgoing", "both"):
            neighbors += [r.target_id for r in self.get_outgoing(entity_id, rel_type)]
        if direction in ("incoming", "both"):
            neighbors += [r.source_id for r in self.get_incoming(entity_id, rel_type)]
        return list(dict.fromkeys(neighbors))  # deduplicate preserving order

    def traverse(
        self,
        root_id: str,
        max_depth: int = 3,
        rel_type: Optional[RelationshipType] = None,
    ) -> dict[str, int]:
        """BFS traversal from root. Returns {entity_id: depth} map."""
        visited: dict[str, int] = {root_id: 0}
        queue = [root_id]
        while queue:
            current = queue.pop(0)
            depth = visited[current]
            if depth >= max_depth:
                continue
            for neighbor in self.get_neighbors(current, rel_type=rel_type):
                if neighbor not in visited:
                    visited[neighbor] = depth + 1
                    queue.append(neighbor)
        return visited

    def find_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: Optional[RelationshipType] = None,
    ) -> Optional[Relationship]:
        """Find the first active relationship between source and target."""
        for rel in self.get_outgoing(source_id, rel_type):
            if rel.target_id == target_id:
                return rel
        return None

    def has_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: Optional[RelationshipType] = None,
    ) -> bool:
        return self.find_relationship(source_id, target_id, rel_type) is not None

    def all_relationships(self, active_only: bool = True) -> list[Relationship]:
        """Return all relationships in the graph."""
        rels = list(self._index.values())
        if active_only:
            rels = [r for r in rels if r.is_active]
        return rels

    def entity_count(self) -> int:
        """Number of unique entity IDs registered in the graph."""
        all_ids = set(self._outgoing.keys()) | set(self._incoming.keys())
        return len(all_ids)

    def __repr__(self) -> str:
        return (
            f"<RelationshipGraph entities={self.entity_count()} "
            f"relationships={len(self.all_relationships())}>"
        )
