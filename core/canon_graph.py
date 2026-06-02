"""
core/canon_graph.py
GAIA Canon Dependency Graph — Sprint G-7

Builds and exposes a directed dependency graph of all GAIA canon entries,
enabling safe ontology navigation, deprecation detection, impact analysis,
and conflict checking as the canon grows.

Canon Ref: C01 (Sovereignty — no silent spec drift)
           C30 (No silent failures — deprecations are explicit, not discovered)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator

import networkx as nx  # type: ignore[import]
import yaml  # PyYAML


# ---------------------------------------------------------------------------
# Canon status
# ---------------------------------------------------------------------------

class CanonStatus(str, Enum):
    ACTIVE     = "active"
    DEPRECATED = "deprecated"
    DRAFT      = "draft"


# ---------------------------------------------------------------------------
# Canon node — one entry in the GAIA canon
# ---------------------------------------------------------------------------

@dataclass
class CanonNode:
    """A single GAIA canon entry parsed from a Markdown file with YAML front-matter."""
    id: str
    title: str
    version: int
    status: CanonStatus
    requires: list[str]   = field(default_factory=list)  # this canon depends on these
    supersedes: list[str] = field(default_factory=list)  # this canon replaces these
    upstream: list[str]   = field(default_factory=list)  # thematically upstream context
    tags: list[str]       = field(default_factory=list)
    path: Path | None     = None


# ---------------------------------------------------------------------------
# CanonGraph
# ---------------------------------------------------------------------------

class CanonGraph:
    """
    Directed dependency graph of all GAIA canon entries.

    The graph is built from YAML front-matter embedded in every canon ``.md``
    file::

        ---
        id: C32
        title: Synergy Doctrine
        version: 2
        status: active
        requires: [C01, C14]
        supersedes: []
        upstream: [C29, C34]
        tags: [synergy, orchestration, engines]
        ---

    Files without front-matter are silently skipped — this allows incremental
    migration of the canon without blocking the graph.
    """

    _FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---", re.DOTALL)

    def __init__(self, canon_dir: Path, min_conflict_overlap: int = 3) -> None:
        """
        Parameters
        ----------
        canon_dir:
            Root directory to scan for ``*.md`` files.
        min_conflict_overlap:
            Minimum number of shared tags required for ``conflict_check()``
            to flag an overlap.  Configurable so it can be tuned without
            touching core logic.
        """
        self._graph: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, CanonNode] = {}
        self._min_conflict_overlap = min_conflict_overlap
        self._build(canon_dir)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self, canon_dir: Path) -> None:
        """Scan canon_dir recursively, parse nodes, add edges."""
        for md_file in sorted(canon_dir.glob("**/*.md")):
            node = self._parse_node(md_file)
            if node is None:
                continue
            self._nodes[node.id] = node
            self._graph.add_node(node.id, **{k: v for k, v in vars(node).items() if k != "path"})

        for node in self._nodes.values():
            for dep in node.requires:
                if dep in self._nodes:
                    self._graph.add_edge(dep, node.id, relation="requires")
            for sup in node.supersedes:
                if sup in self._nodes:
                    self._graph.add_edge(node.id, sup, relation="supersedes")

    @classmethod
    def _parse_node(cls, path: Path) -> CanonNode | None:
        """Parse YAML front-matter from a canon Markdown file.

        Returns ``None`` if the file has no front-matter or the front-matter
        is malformed — never raises.
        """
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        match = cls._FRONTMATTER_RE.match(text)
        if not match:
            return None

        try:
            meta = yaml.safe_load(match.group(1))
            if not isinstance(meta, dict) or "id" not in meta:
                return None
            return CanonNode(
                id=str(meta["id"]),
                title=str(meta.get("title", "")),
                version=int(meta.get("version", 1)),
                status=CanonStatus(meta.get("status", "active")),
                requires=list(meta.get("requires", []) or []),
                supersedes=list(meta.get("supersedes", []) or []),
                upstream=list(meta.get("upstream", []) or []),
                tags=list(meta.get("tags", []) or []),
                path=path,
            )
        except (KeyError, ValueError, yaml.YAMLError):
            return None

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get(self, node_id: str) -> CanonNode | None:
        """Return the CanonNode for *node_id*, or None if not found."""
        return self._nodes.get(node_id)

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._nodes

    def __len__(self) -> int:
        return len(self._nodes)

    def all_nodes(self) -> list[CanonNode]:
        """Return all canon nodes in ID-sorted order."""
        return sorted(self._nodes.values(), key=lambda n: n.id)

    def dependents(self, node_id: str) -> list[str]:
        """Return all canon IDs that directly or transitively depend on *node_id*.

        A "dependent" requires *node_id* somewhere in its ancestry.
        """
        if node_id not in self._graph:
            return []
        return sorted(nx.descendants(self._graph, node_id))

    def dependencies(self, node_id: str) -> list[str]:
        """Return all canon IDs that *node_id* transitively depends on."""
        if node_id not in self._graph:
            return []
        return sorted(nx.ancestors(self._graph, node_id))

    def direct_dependents(self, node_id: str) -> list[str]:
        """Return only the immediate successors of *node_id* in the graph."""
        return sorted(self._graph.successors(node_id))

    def is_deprecated(self, node_id: str) -> bool:
        """True if *node_id* exists and has status DEPRECATED."""
        node = self._nodes.get(node_id)
        return node is not None and node.status == CanonStatus.DEPRECATED

    def is_draft(self, node_id: str) -> bool:
        """True if *node_id* exists and has status DRAFT."""
        node = self._nodes.get(node_id)
        return node is not None and node.status == CanonStatus.DRAFT

    def has_cycle(self) -> bool:
        """True if the requires graph contains any cycle (should never happen)."""
        return not nx.is_directed_acyclic_graph(self._graph)

    def find_cycles(self) -> list[list[str]]:
        """Return all simple cycles found in the graph."""
        return list(nx.simple_cycles(self._graph))

    def conflict_check(self, proposed: CanonNode) -> list[str]:
        """Return IDs of active nodes whose tag sets significantly overlap with *proposed*.

        Overlap threshold is set by ``min_conflict_overlap`` (default 3).
        Only ACTIVE nodes are considered — deprecated/draft nodes do not conflict.
        The proposed node's own ID is excluded if it already exists.
        """
        conflicts: list[str] = []
        proposed_tags = set(proposed.tags)
        for nid, node in self._nodes.items():
            if nid == proposed.id:
                continue
            if node.status != CanonStatus.ACTIVE:
                continue
            if len(proposed_tags & set(node.tags)) >= self._min_conflict_overlap:
                conflicts.append(nid)
        return sorted(conflicts)

    def deprecated_nodes(self) -> Iterator[CanonNode]:
        """Iterate over all DEPRECATED canon nodes."""
        return (n for n in self._nodes.values() if n.status == CanonStatus.DEPRECATED)

    def draft_nodes(self) -> Iterator[CanonNode]:
        """Iterate over all DRAFT canon nodes."""
        return (n for n in self._nodes.values() if n.status == CanonStatus.DRAFT)

    def active_nodes(self) -> Iterator[CanonNode]:
        """Iterate over all ACTIVE canon nodes."""
        return (n for n in self._nodes.values() if n.status == CanonStatus.ACTIVE)

    def impact_report(self, node_id: str) -> dict:
        """Full impact assessment before deprecating or modifying a canon node.

        Returns a dict containing:
        - ``node``: the CanonNode itself
        - ``direct_dependents``: IDs of nodes that immediately depend on this one
        - ``all_dependents``: IDs of all transitively-dependent nodes
        - ``supersedes``: CanonNode objects that this node supersedes
        - ``is_deprecated``: current deprecation status
        """
        node = self._nodes.get(node_id)
        return {
            "node": node,
            "direct_dependents": self.direct_dependents(node_id) if node else [],
            "all_dependents": self.dependents(node_id),
            "supersedes": [
                self._nodes[s]
                for s in (node.supersedes if node else [])
                if s in self._nodes
            ],
            "is_deprecated": self.is_deprecated(node_id),
        }

    def validate_refs(self, refs: list[str]) -> list[str]:
        """Given a list of canon IDs (e.g. from a trace), return any that are unknown.

        Used by GAIATrace to validate canon_refs before writing.
        Returns the list of unrecognised IDs; empty list means all refs are valid.
        """
        return [r for r in refs if r not in self._nodes]

    def summary(self) -> dict:
        """High-level graph summary for diagnostic purposes."""
        return {
            "total": len(self._nodes),
            "active": sum(1 for n in self._nodes.values() if n.status == CanonStatus.ACTIVE),
            "deprecated": sum(1 for n in self._nodes.values() if n.status == CanonStatus.DEPRECATED),
            "draft": sum(1 for n in self._nodes.values() if n.status == CanonStatus.DRAFT),
            "edges": self._graph.number_of_edges(),
            "has_cycle": self.has_cycle(),
        }
