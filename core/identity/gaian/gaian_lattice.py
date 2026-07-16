"""
core/identity/gaian/gaian_lattice.py

GaianLattice — directed acyclic graph (DAG) of GaianNodes.

Capability inheritance: a node inherits all active capabilities of its
ancestors; direct capabilities take precedence (override).
Cycle detection on every edge addition (DFS).
Thread-safe via RLock.
Exactly one ROOT node per lattice.

Canon Refs: C01, C03, C08
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Set

from .gaian_node import GaianNode, NodeRole, Capability


@dataclass
class LatticeEdge:
    parent_id: str
    child_id: str
    created_at: float = field(default_factory=time.time)
    label: str = "delegates"
    metadata: Dict[str, Any] = field(default_factory=dict)


class GaianLattice:
    def __init__(self) -> None:
        self._nodes: Dict[str, GaianNode] = {}
        self._edges: List[LatticeEdge] = []
        self._children: Dict[str, Set[str]] = {}
        self._parents: Dict[str, Set[str]] = {}
        self._root_id: Optional[str] = None
        self._lock = threading.RLock()

    def add_node(self, node: GaianNode) -> GaianNode:
        with self._lock:
            if node.id in self._nodes:
                raise ValueError(f"Node '{node.id}' already in lattice.")
            if node.role == NodeRole.ROOT:
                if self._root_id is not None:
                    raise PermissionError(f"ROOT node already exists: {self._root_id}.")
                self._root_id = node.id
            self._nodes[node.id] = node
            self._children[node.id] = set()
            self._parents[node.id] = set()
        return node

    def remove_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id not in self._nodes:
                return False
            self._edges = [e for e in self._edges if e.parent_id != node_id and e.child_id != node_id]
            for cid in list(self._children.get(node_id, [])):
                self._parents[cid].discard(node_id)
            for pid in list(self._parents.get(node_id, [])):
                self._children[pid].discard(node_id)
            del self._children[node_id]
            del self._parents[node_id]
            if node_id == self._root_id:
                self._root_id = None
            del self._nodes[node_id]
        return True

    def get_node(self, node_id: str) -> Optional[GaianNode]:
        with self._lock:
            return self._nodes.get(node_id)

    def all_nodes(self) -> List[GaianNode]:
        with self._lock:
            return list(self._nodes.values())

    def root(self) -> Optional[GaianNode]:
        with self._lock:
            return self._nodes.get(self._root_id) if self._root_id else None

    def add_edge(self, parent_id: str, child_id: str, *, label: str = "delegates", metadata: Optional[Dict[str, Any]] = None) -> LatticeEdge:
        with self._lock:
            if parent_id not in self._nodes:
                raise KeyError(f"Parent node '{parent_id}' not in lattice.")
            if child_id not in self._nodes:
                raise KeyError(f"Child node '{child_id}' not in lattice.")
            if parent_id == child_id:
                raise ValueError("Self-edges are not allowed.")
            if self._would_cycle(parent_id, child_id):
                raise ValueError(f"Adding edge {parent_id} -> {child_id} would create a cycle.")
            edge = LatticeEdge(parent_id=parent_id, child_id=child_id, label=label, metadata=metadata or {})
            self._edges.append(edge)
            self._children[parent_id].add(child_id)
            self._parents[child_id].add(parent_id)
        return edge

    def remove_edge(self, parent_id: str, child_id: str) -> bool:
        with self._lock:
            before = len(self._edges)
            self._edges = [e for e in self._edges if not (e.parent_id == parent_id and e.child_id == child_id)]
            if len(self._edges) < before:
                self._children[parent_id].discard(child_id)
                self._parents[child_id].discard(parent_id)
                return True
        return False

    def ancestors(self, node_id: str) -> List[GaianNode]:
        with self._lock:
            visited: List[GaianNode] = []
            queue = list(self._parents.get(node_id, []))
            seen: Set[str] = set()
            while queue:
                pid = queue.pop(0)
                if pid in seen:
                    continue
                seen.add(pid)
                node = self._nodes.get(pid)
                if node:
                    visited.append(node)
                queue.extend(self._parents.get(pid, []))
            return visited

    def descendants(self, node_id: str) -> List[GaianNode]:
        with self._lock:
            visited: List[GaianNode] = []
            queue = list(self._children.get(node_id, []))
            seen: Set[str] = set()
            while queue:
                cid = queue.pop(0)
                if cid in seen:
                    continue
                seen.add(cid)
                node = self._nodes.get(cid)
                if node:
                    visited.append(node)
                queue.extend(self._children.get(cid, []))
            return visited

    def effective_capabilities(self, node_id: str) -> Dict[str, Capability]:
        with self._lock:
            merged: Dict[str, Capability] = {}
            for ancestor in reversed(self.ancestors(node_id)):
                for name, cap in ancestor.capabilities.items():
                    if cap.is_active():
                        merged[name] = cap
            node = self._nodes.get(node_id)
            if node:
                for name, cap in node.capabilities.items():
                    if cap.is_active():
                        merged[name] = cap
            return merged

    def has_effective_capability(self, node_id: str, cap_name: str, resource: Optional[str] = None) -> bool:
        caps = self.effective_capabilities(node_id)
        cap = caps.get(cap_name)
        return cap is not None and cap.covers(resource)

    def __len__(self) -> int:
        with self._lock:
            return len(self._nodes)

    def __iter__(self) -> Iterator[GaianNode]:
        return iter(self.all_nodes())

    def __contains__(self, node_id: str) -> bool:
        with self._lock:
            return node_id in self._nodes

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "nodes": len(self._nodes),
                "edges": len(self._edges),
                "root_id": self._root_id,
                "roles": {role.value: sum(1 for n in self._nodes.values() if n.role == role) for role in NodeRole},
            }

    def _would_cycle(self, parent_id: str, child_id: str) -> bool:
        visited: Set[str] = set()
        stack = [child_id]
        while stack:
            current = stack.pop()
            if current == parent_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self._children.get(current, []))
        return False
