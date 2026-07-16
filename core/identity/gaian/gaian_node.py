"""
core/identity/gaian/gaian_node.py

GaianNode — a single capability-bearing agent node in the Gaian substrate.

Design:
- Each node has a role (ROOT, STEWARD, AGENT, OBSERVER) that determines
  its maximum authority ceiling.
- Capabilities are named permissions with optional scope constraints.
- Nodes may inherit capabilities from parent nodes via the GaianLattice;
  direct capabilities always override inherited ones.
- Immutable id and created_at; all other fields mutate through logged
  operations that respect consent requirements (C15).

Canon Refs: C01, C03, C08, C15
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional


class NodeRole(str, Enum):
    ROOT     = "root"
    STEWARD  = "steward"
    AGENT    = "agent"
    OBSERVER = "observer"


_ROLE_RANK: Dict[NodeRole, int] = {
    NodeRole.OBSERVER: 0,
    NodeRole.AGENT:    1,
    NodeRole.STEWARD:  2,
    NodeRole.ROOT:     3,
}


@dataclass
class Capability:
    name: str
    scope: FrozenSet[str] = field(default_factory=frozenset)
    expires_at: Optional[float] = None
    granted_by: str = "system"
    granted_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_active(self) -> bool:
        if self.expires_at is None:
            return True
        return time.time() < self.expires_at

    def covers(self, resource: Optional[str] = None) -> bool:
        if not self.is_active():
            return False
        if not self.scope:
            return True
        return resource is not None and resource in self.scope

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "scope": sorted(self.scope),
            "expires_at": self.expires_at,
            "granted_by": self.granted_by,
            "granted_at": self.granted_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Capability":
        return cls(
            name=d["name"],
            scope=frozenset(d.get("scope", [])),
            expires_at=d.get("expires_at"),
            granted_by=d.get("granted_by", "system"),
            granted_at=d.get("granted_at", time.time()),
            metadata=d.get("metadata", {}),
        )


@dataclass
class GaianNode:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    name: str = "unnamed-node"
    role: NodeRole = NodeRole.AGENT
    avatar_id: Optional[str] = None
    capabilities: Dict[str, Capability] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def grant(self, capability: Capability, *, granting_node: Optional["GaianNode"] = None) -> None:
        if granting_node is not None:
            if _ROLE_RANK[granting_node.role] <= _ROLE_RANK[self.role]:
                raise PermissionError(
                    f"Node '{granting_node.id}' (role={granting_node.role.value}) "
                    f"cannot grant capabilities to '{self.id}' (role={self.role.value})."
                )
        self.capabilities[capability.name] = capability
        self.updated_at = time.time()

    def revoke(self, capability_name: str) -> bool:
        if capability_name in self.capabilities:
            del self.capabilities[capability_name]
            self.updated_at = time.time()
            return True
        return False

    def has_capability(self, name: str, resource: Optional[str] = None, *, include_expired: bool = False) -> bool:
        cap = self.capabilities.get(name)
        if cap is None:
            return False
        if not include_expired and not cap.is_active():
            return False
        return cap.covers(resource)

    def active_capabilities(self) -> List[Capability]:
        return [c for c in self.capabilities.values() if c.is_active()]

    def purge_expired(self) -> int:
        expired = [n for n, c in self.capabilities.items() if not c.is_active()]
        for n in expired:
            del self.capabilities[n]
        if expired:
            self.updated_at = time.time()
        return len(expired)

    def outranks(self, other: "GaianNode") -> bool:
        return _ROLE_RANK[self.role] > _ROLE_RANK[other.role]

    def can_delegate(self) -> bool:
        return self.role in (NodeRole.ROOT, NodeRole.STEWARD)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "name": self.name,
            "role": self.role.value,
            "avatar_id": self.avatar_id,
            "capabilities": {k: v.to_dict() for k, v in self.capabilities.items()},
            "tags": list(self.tags),
            "active": self.active,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GaianNode":
        node = cls(
            id=d["id"],
            created_at=d["created_at"],
            updated_at=d.get("updated_at", d["created_at"]),
            name=d.get("name", "unnamed-node"),
            role=NodeRole(d.get("role", "agent")),
            avatar_id=d.get("avatar_id"),
            tags=d.get("tags", []),
            active=d.get("active", True),
            metadata=d.get("metadata", {}),
        )
        for cap_dict in d.get("capabilities", {}).values():
            cap = Capability.from_dict(cap_dict)
            node.capabilities[cap.name] = cap
        return node
