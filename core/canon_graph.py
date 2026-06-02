"""
core/canon_graph.py
===================
GAIA Canon Dependency Graph — Sprint G-7

Builds and exposes a directed dependency graph of all GAIA canon entries,
enabling safe ontology navigation, deprecation detection, impact assessment,
and conflict checking as the canon grows.

Architecture
------------
    canon_dir/*.md  →  YAML front-matter parse
                    →  CanonNode dataclasses
                    →  nx.DiGraph  (requires + supersedes edges)
                    →  CanonGraph query API

Canon Refs
----------
  C01 — Sovereignty (no silent spec drift — the graph is the authority)
  C30 — No silent failures (deprecations are explicit, not discovered)

GAIATrace Integration
---------------------
A CANON_LOAD trace event is emitted once at _build() completion if a
live GAIATrace context is available via the `trace` kwarg on CanonGraph().
The event payload includes node_count, deprecated_count, draft_count,
and any cycle warnings. All trace operations are wrapped in try/except.

Front-Matter Schema
-------------------
Every canon .md file should begin with a YAML front-matter block::

    ---
    id: C32
    title: Synergy Doctrine
    version: 2
    status: active          # active | deprecated | draft
    requires: [C01, C14]    # dependencies — this canon assumes these
    supersedes: []          # replaces these older entries
    upstream: [C29, C34]    # thematically upstream context
    tags: [synergy, orchestration, engines]
    ---

Files without a valid front-matter block are silently skipped.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

try:
    import networkx as nx          # type: ignore
except ImportError as _nx_err:   # pragma: no cover
    raise ImportError(
        "CanonGraph requires networkx. Install with: pip install networkx"
    ) from _nx_err

try:
    import yaml                    # type: ignore
except ImportError as _yaml_err:  # pragma: no cover
    raise ImportError(
        "CanonGraph requires PyYAML. Install with: pip install pyyaml"
    ) from _yaml_err


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CanonStatus(str, Enum):
    ACTIVE     = "active"
    DEPRECATED = "deprecated"
    DRAFT      = "draft"


# ---------------------------------------------------------------------------
# CanonNode
# ---------------------------------------------------------------------------

@dataclass
class CanonNode:
    """
    A single node in the GAIA canon dependency graph.

    Attributes
    ----------
    id:          Canonical identifier (e.g. ``"C32"``, ``"SME01"``)
    title:       Human-readable title from front-matter
    version:     Integer version; incremented when the entry is revised
    status:      `CanonStatus.ACTIVE`, `DEPRECATED`, or `DRAFT`
    requires:    IDs of canon entries this node directly depends on
    supersedes:  IDs of older entries this node replaces
    upstream:    IDs of thematically upstream context entries
    tags:        Free-form tags for search and conflict detection
    path:        Absolute path to the source `.md` file (``None`` if synthetic)
    """
    id:         str
    title:      str
    version:    int
    status:     CanonStatus
    requires:   List[str] = field(default_factory=list)
    supersedes: List[str] = field(default_factory=list)
    upstream:   List[str] = field(default_factory=list)
    tags:       List[str] = field(default_factory=list)
    path:       Optional[Path] = field(default=None, repr=False)

    def is_active(self) -> bool:
        return self.status == CanonStatus.ACTIVE

    def is_deprecated(self) -> bool:
        return self.status == CanonStatus.DEPRECATED

    def is_draft(self) -> bool:
        return self.status == CanonStatus.DRAFT

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "title":      self.title,
            "version":    self.version,
            "status":     self.status.value,
            "requires":   self.requires,
            "supersedes": self.supersedes,
            "upstream":   self.upstream,
            "tags":       self.tags,
            "path":       str(self.path) if self.path else None,
        }


# ---------------------------------------------------------------------------
# CanonGraph
# ---------------------------------------------------------------------------

class CanonGraph:
    """
    Directed dependency graph of all GAIA canon entries.

    Construction
    ------------
    Scans ``canon_dir`` recursively for ``*.md`` files, parses the YAML
    front-matter block of each, and adds two kinds of directed edges:

    * ``requires`` edges  — ``dep → node``  (dep must hold for node to hold)
    * ``supersedes`` edges — ``node → old`` (node replaces old)

    Files without valid front-matter are silently skipped.

    Cycle detection
    ---------------
    After the graph is built, ``requires`` edges are checked for cycles.
    A warning is logged for each cycle found (C30 — never silent), but
    construction succeeds so callers are not blocked by a malformed file.

    Parameters
    ----------
    canon_dir:
        Root directory to scan for canon ``.md`` files.
    trace:
        Optional ``GAIATrace`` / ``AsyncGAIATrace`` context.  A
        ``CANON_LOAD`` event is emitted once after ``_build()`` completes.
    """

    def __init__(
        self,
        canon_dir: Path,
        trace: Any = None,
    ) -> None:
        self._graph:  nx.DiGraph          = nx.DiGraph()
        self._nodes:  Dict[str, CanonNode] = {}
        self._cycles: List[List[str]]     = []
        self._build(canon_dir, trace=trace)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self, canon_dir: Path, trace: Any = None) -> None:
        """
        Parse all ``*.md`` files under ``canon_dir`` and construct the
        dependency graph.  Emits a CANON_LOAD trace event on completion.
        """
        import logging
        log = logging.getLogger(__name__)

        for md_file in sorted(canon_dir.glob("**/*.md")):
            node = self._parse_node(md_file)
            if node is not None:
                self._nodes[node.id] = node
                self._graph.add_node(node.id)

        # Wire edges
        for node in self._nodes.values():
            for dep in node.requires:
                if dep in self._nodes:
                    self._graph.add_edge(dep, node.id, relation="requires")
                else:
                    log.debug(
                        "CanonGraph: %s requires unknown node %s — edge skipped",
                        node.id, dep,
                    )
            for sup in node.supersedes:
                if sup in self._nodes:
                    self._graph.add_edge(node.id, sup, relation="supersedes")
                else:
                    log.debug(
                        "CanonGraph: %s supersedes unknown node %s — edge skipped",
                        node.id, sup,
                    )

        # Cycle detection on requires-only subgraph (C30)
        requires_edges = [
            (u, v) for u, v, d in self._graph.edges(data=True)
            if d.get("relation") == "requires"
        ]
        req_graph = nx.DiGraph(requires_edges)
        self._cycles = list(nx.simple_cycles(req_graph))
        if self._cycles:
            log.warning(
                "CanonGraph: %d cycle(s) detected in requires edges: %s",
                len(self._cycles), self._cycles,
            )

        log.info(
            "CanonGraph built: %d nodes (%d active, %d deprecated, %d draft), "
            "%d edges, %d cycles",
            len(self._nodes),
            sum(1 for n in self._nodes.values() if n.is_active()),
            sum(1 for n in self._nodes.values() if n.is_deprecated()),
            sum(1 for n in self._nodes.values() if n.is_draft()),
            self._graph.number_of_edges(),
            len(self._cycles),
        )

        # GAIATrace CANON_LOAD event
        self._emit_canon_load(trace)

    def _emit_canon_load(self, trace: Any) -> None:
        if trace is None:
            return
        try:
            from core.trace import TraceEventType
            trace.record_output(
                output={
                    "event":            "CANON_LOAD",
                    "node_count":       len(self._nodes),
                    "active_count":     sum(1 for n in self._nodes.values() if n.is_active()),
                    "deprecated_count": sum(1 for n in self._nodes.values() if n.is_deprecated()),
                    "draft_count":      sum(1 for n in self._nodes.values() if n.is_draft()),
                    "edge_count":       self._graph.number_of_edges(),
                    "cycles":           self._cycles,
                },
                event_type=TraceEventType.CANON_LOAD,
                canon_refs=["C01", "C30"],
            )
        except Exception:
            pass  # Never suppress a canon graph build result (C30)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_node(path: Path) -> Optional[CanonNode]:
        """
        Parse the YAML front-matter from a canon ``.md`` file.
        Returns ``None`` if the file has no valid front-matter block.
        """
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        match = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
        if not match:
            return None

        try:
            meta = yaml.safe_load(match.group(1))
            if not isinstance(meta, dict) or "id" not in meta:
                return None

            raw_status = str(meta.get("status", "active")).lower()
            try:
                status = CanonStatus(raw_status)
            except ValueError:
                status = CanonStatus.ACTIVE

            return CanonNode(
                id=str(meta["id"]),
                title=str(meta.get("title", "")),
                version=int(meta.get("version", 1)),
                status=status,
                requires=list(meta.get("requires") or []),
                supersedes=list(meta.get("supersedes") or []),
                upstream=list(meta.get("upstream") or []),
                tags=list(meta.get("tags") or []),
                path=path,
            )
        except (KeyError, ValueError, TypeError, yaml.YAMLError):
            return None

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get(self, node_id: str) -> Optional[CanonNode]:
        """Return the ``CanonNode`` for ``node_id``, or ``None``."""
        return self._nodes.get(node_id)

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._nodes

    def __len__(self) -> int:
        return len(self._nodes)

    def dependents(
        self,
        node_id: str,
        direct: bool = False,
    ) -> List[str]:
        """
        Return canon IDs that depend on ``node_id``.

        Parameters
        ----------
        direct:
            When ``True``, return only immediate successors.
            When ``False`` (default), return all transitive descendants.
        """
        if node_id not in self._graph:
            return []
        if direct:
            return list(self._graph.successors(node_id))
        return list(nx.descendants(self._graph, node_id))

    def dependencies(
        self,
        node_id: str,
        direct: bool = False,
    ) -> List[str]:
        """
        Return canon IDs that ``node_id`` depends on.

        Parameters
        ----------
        direct:
            When ``True``, return only immediate predecessors.
            When ``False`` (default), return all transitive ancestors.
        """
        if node_id not in self._graph:
            return []
        if direct:
            return list(self._graph.predecessors(node_id))
        return list(nx.ancestors(self._graph, node_id))

    def is_deprecated(self, node_id: str) -> bool:
        """Return ``True`` if ``node_id`` exists and is DEPRECATED."""
        node = self._nodes.get(node_id)
        return node is not None and node.is_deprecated()

    def active_nodes(self) -> List[CanonNode]:
        """Return all ACTIVE canon nodes."""
        return [n for n in self._nodes.values() if n.is_active()]

    def deprecated_nodes(self) -> Iterator[CanonNode]:
        """Yield all DEPRECATED canon nodes."""
        return (n for n in self._nodes.values() if n.is_deprecated())

    def draft_nodes(self) -> Iterator[CanonNode]:
        """Yield all DRAFT canon nodes."""
        return (n for n in self._nodes.values() if n.is_draft())

    def nodes_by_tag(self, tag: str) -> List[CanonNode]:
        """Return all nodes whose tag list contains ``tag``."""
        return [n for n in self._nodes.values() if tag in n.tags]

    def has_cycles(self) -> bool:
        """Return ``True`` if any cycles were detected in ``requires`` edges."""
        return len(self._cycles) > 0

    def cycles(self) -> List[List[str]]:
        """Return the list of detected cycles (empty list if none)."""
        return list(self._cycles)

    # ------------------------------------------------------------------
    # Safety Gates
    # ------------------------------------------------------------------

    def conflict_check(self, proposed: CanonNode) -> List[str]:
        """
        Return IDs of ACTIVE nodes whose tag sets significantly overlap
        with ``proposed`` (3 or more tags in common).

        Use this before committing a new canon entry to detect potential
        semantic duplication or contradictions.

        Returns
        -------
        list of str
            Canon IDs of conflicting nodes.  Empty list means no conflicts.
        """
        proposed_tags = set(proposed.tags)
        return [
            nid
            for nid, node in self._nodes.items()
            if (
                node.is_active()
                and nid != proposed.id
                and len(proposed_tags & set(node.tags)) >= 3
            )
        ]

    def impact_report(self, node_id: str) -> Dict[str, Any]:
        """
        Full impact assessment before deprecating or modifying a canon node.

        Returns
        -------
        dict with keys:
            node              — the ``CanonNode`` (or ``None`` if not found)
            direct_dependents — immediate successors in the graph
            all_dependents    — all transitive descendants
            supersedes        — CanonNode objects this node replaces
            cycles            — any cycles involving this node
        """
        node = self._nodes.get(node_id)
        superseded_nodes = []
        if node:
            superseded_nodes = [
                self._nodes[s]
                for s in node.supersedes
                if s in self._nodes
            ]
        node_cycles = [
            cycle for cycle in self._cycles
            if node_id in cycle
        ]
        return {
            "node":              node,
            "direct_dependents": self.dependents(node_id, direct=True),
            "all_dependents":    self.dependents(node_id),
            "supersedes":        superseded_nodes,
            "cycles":            node_cycles,
        }

    def summary(self) -> Dict[str, Any]:
        """Return a concise graph-level summary dict."""
        return {
            "total":      len(self._nodes),
            "active":     len(self.active_nodes()),
            "deprecated": sum(1 for _ in self.deprecated_nodes()),
            "draft":      sum(1 for _ in self.draft_nodes()),
            "edges":      self._graph.number_of_edges(),
            "cycles":     len(self._cycles),
        }


# ---------------------------------------------------------------------------
# CLI  (`python -m core.canon_graph`)
# ---------------------------------------------------------------------------

def _cli_main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog="python -m core.canon_graph",
        description="GAIA Canon Graph CLI",
    )
    parser.add_argument(
        "--canon-dir",
        default="docs/canon",
        help="Root directory of canon .md files (default: docs/canon)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # deps
    p_deps = sub.add_parser("deps", help="List what a node depends on")
    p_deps.add_argument("id", help="Canon ID (e.g. C32)")
    p_deps.add_argument("--direct", action="store_true", help="Direct dependencies only")

    # dependents
    p_dep = sub.add_parser("dependents", help="List nodes that depend on a node")
    p_dep.add_argument("id", help="Canon ID")
    p_dep.add_argument("--direct", action="store_true", help="Direct dependents only")

    # impact
    p_imp = sub.add_parser("impact", help="Impact report before modifying a node")
    p_imp.add_argument("id", help="Canon ID")

    # conflicts
    p_con = sub.add_parser("conflicts", help="Conflict-check a proposed node")
    p_con.add_argument("id", help="Proposed canon ID")
    p_con.add_argument("--tags", nargs="+", default=[], help="Tags for proposed node")

    # deprecated
    sub.add_parser("deprecated", help="List all deprecated nodes")

    # draft
    sub.add_parser("draft", help="List all draft nodes")

    # tags
    p_tags = sub.add_parser("tags", help="List nodes by tag")
    p_tags.add_argument("tag", help="Tag to filter by")

    # summary
    sub.add_parser("summary", help="Graph-level summary")

    args = parser.parse_args()
    canon_dir = Path(args.canon_dir)

    if not canon_dir.exists():
        print(f"[ERROR] canon-dir not found: {canon_dir}", file=sys.stderr)
        sys.exit(1)

    graph = CanonGraph(canon_dir)

    if args.cmd == "deps":
        result = graph.dependencies(args.id, direct=args.direct)
        _print_id_list(result, f"Dependencies of {args.id}")

    elif args.cmd == "dependents":
        result = graph.dependents(args.id, direct=args.direct)
        _print_id_list(result, f"Dependents of {args.id}")

    elif args.cmd == "impact":
        report = graph.impact_report(args.id)
        print(f"\n=== Impact Report: {args.id} ===")
        node = report["node"]
        if node:
            print(f"  Title:            {node.title}")
            print(f"  Status:           {node.status.value}")
            print(f"  Version:          {node.version}")
        print(f"  Direct dependents: {report['direct_dependents']}")
        print(f"  All dependents:    {report['all_dependents']}")
        print(f"  Supersedes:        {[n.id for n in report['supersedes']]}")
        print(f"  Cycles involving:  {report['cycles']}")

    elif args.cmd == "conflicts":
        proposed = CanonNode(
            id=args.id,
            title="",
            version=1,
            status=CanonStatus.DRAFT,
            tags=args.tags,
        )
        conflicts = graph.conflict_check(proposed)
        _print_id_list(conflicts, f"Conflicts for proposed {args.id}")

    elif args.cmd == "deprecated":
        nodes = list(graph.deprecated_nodes())
        _print_nodes(nodes, "Deprecated nodes")

    elif args.cmd == "draft":
        nodes = list(graph.draft_nodes())
        _print_nodes(nodes, "Draft nodes")

    elif args.cmd == "tags":
        nodes = graph.nodes_by_tag(args.tag)
        _print_nodes(nodes, f"Nodes tagged '{args.tag}'")

    elif args.cmd == "summary":
        s = graph.summary()
        print("\n=== CanonGraph Summary ===")
        for k, v in s.items():
            print(f"  {k:<12}: {v}")


def _print_id_list(ids: List[str], header: str) -> None:
    print(f"\n{header} ({len(ids)}):")
    for i in sorted(ids):
        print(f"  {i}")


def _print_nodes(nodes: List[CanonNode], header: str) -> None:
    print(f"\n{header} ({len(nodes)}):")
    for n in sorted(nodes, key=lambda x: x.id):
        print(f"  {n.id:<8}  v{n.version}  [{n.status.value}]  {n.title}")


if __name__ == "__main__":  # pragma: no cover
    _cli_main()
