"""
core/canon_graph.py
GAIA Canon Graph — Sprint G-7, Issue #169

Builds and traverses the Canon knowledge graph from YAML/JSON source
files in the canon/ directory. Every _build() call is wrapped in a
GAIATrace(CANON_LOAD) span so the load is fully observable.

Usage:
    graph = CanonGraph()
    node  = graph.get("C01")
    ancs  = graph.ancestors("C32")
    path  = graph.path_to("C01", "C118")

CLI:
    python -m core.canon_graph show  --node C01
    python -m core.canon_graph path  --from C01 --to C118
    python -m core.canon_graph validate

Canon Refs: C01 (Sovereignty), C47 (Sovereign Matrix), C48 (Knowledge Matrix)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from core.trace import GAIATrace, TraceEventType
    _TRACE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TRACE_AVAILABLE = False

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    _YAML_AVAILABLE = False

_CANON_DIR = Path("canon")


# ── Data Model ───────────────────────────────────────────────────────────── #

@dataclass
class CanonNode:
    """A single node in the Canon knowledge graph."""
    id:       str
    label:    str
    refs:     list[str]      = field(default_factory=list)   # e.g. ["C01", "Doc35"]
    parents:  list[str]      = field(default_factory=list)   # parent node IDs
    children: list[str]      = field(default_factory=list)   # child node IDs
    meta:     dict[str, Any] = field(default_factory=dict)


# ── Canon Graph ─────────────────────────────────────────────────────────── #

class CanonGraph:
    """
    Loads the GAIA Canon from source files and exposes a typed, traversable
    DAG. Emits GAIATrace(CANON_LOAD) on every build.
    """

    def __init__(self, canon_dir: Path | None = None, auto_build: bool = True) -> None:
        self._canon_dir = canon_dir or _CANON_DIR
        self._nodes: dict[str, CanonNode] = {}
        if auto_build and self._canon_dir.exists():
            self._build()

    # ── Build ──────────────────────────────────────────────────────────── #

    def _build(self) -> None:
        """Load all canon source files and wire parent/child edges.
        Wrapped in GAIATrace(CANON_LOAD) — Issue #171."""
        raw_files = list(self._canon_dir.rglob("*.yaml")) + \
                    list(self._canon_dir.rglob("*.yml"))  + \
                    list(self._canon_dir.rglob("*.json"))

        if _TRACE_AVAILABLE:
            ctx = GAIATrace(
                event=TraceEventType.CANON_LOAD,
                canon_refs=["C01", "C47", "C48"],
                inputs={"canon_dir": str(self._canon_dir), "file_count": len(raw_files)},
            )
        else:
            from contextlib import nullcontext
            ctx = nullcontext()  # type: ignore[assignment]

        with ctx as trace:
            for path in raw_files:
                self._load_file(path)
            self._wire_edges()
            if _TRACE_AVAILABLE and trace is not None:
                trace.record_output({"nodes_loaded": len(self._nodes)})

    def _load_file(self, path: Path) -> None:
        """Parse one canon source file (YAML or JSON) into CanonNode objects."""
        try:
            if path.suffix in (".yaml", ".yml"):
                if not _YAML_AVAILABLE:
                    return  # skip if PyYAML not installed
                with path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            else:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
        except Exception:
            return  # corrupt file — skip; trace records the final count

        if not isinstance(data, (list, dict)):
            return
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            if not isinstance(entry, dict) or "id" not in entry:
                continue
            node = CanonNode(
                id=str(entry["id"]),
                label=entry.get("label", ""),
                refs=entry.get("refs", []),
                parents=entry.get("parents", []),
                children=entry.get("children", []),
                meta={k: v for k, v in entry.items()
                      if k not in ("id", "label", "refs", "parents", "children")},
            )
            self._nodes[node.id] = node

    def _wire_edges(self) -> None:
        """Populate children lists from parent declarations (bidirectional wiring)."""
        for node in self._nodes.values():
            for parent_id in node.parents:
                parent = self._nodes.get(parent_id)
                if parent and node.id not in parent.children:
                    parent.children.append(node.id)

    # ── Query API ──────────────────────────────────────────────────────── #

    def get(self, node_id: str) -> CanonNode | None:
        """Return a CanonNode by ID, or None if not found."""
        return self._nodes.get(node_id)

    def all_nodes(self) -> list[CanonNode]:
        """Return all loaded nodes."""
        return list(self._nodes.values())

    def ancestors(self, node_id: str) -> list[CanonNode]:
        """BFS traversal upward from node_id, returning all ancestor nodes."""
        visited: set[str] = set()
        queue: deque[str] = deque()
        result: list[CanonNode] = []
        start = self._nodes.get(node_id)
        if not start:
            return []
        for parent_id in start.parents:
            queue.append(parent_id)
        while queue:
            nid = queue.popleft()
            if nid in visited:
                continue
            visited.add(nid)
            node = self._nodes.get(nid)
            if node:
                result.append(node)
                for p in node.parents:
                    if p not in visited:
                        queue.append(p)
        return result

    def descendants(self, node_id: str) -> list[CanonNode]:
        """BFS traversal downward from node_id, returning all descendant nodes."""
        visited: set[str] = set()
        queue: deque[str] = deque()
        result: list[CanonNode] = []
        start = self._nodes.get(node_id)
        if not start:
            return []
        for child_id in start.children:
            queue.append(child_id)
        while queue:
            nid = queue.popleft()
            if nid in visited:
                continue
            visited.add(nid)
            node = self._nodes.get(nid)
            if node:
                result.append(node)
                for c in node.children:
                    if c not in visited:
                        queue.append(c)
        return result

    def path_to(self, start_id: str, end_id: str) -> list[CanonNode] | None:
        """BFS shortest path from start_id to end_id following child edges.
        Returns the path as a list of nodes, or None if no path exists."""
        if start_id not in self._nodes or end_id not in self._nodes:
            return None
        visited: set[str] = {start_id}
        queue: deque[list[str]] = deque([[start_id]])
        while queue:
            path = queue.popleft()
            current = path[-1]
            if current == end_id:
                return [self._nodes[n] for n in path if n in self._nodes]
            node = self._nodes.get(current)
            if not node:
                continue
            for child_id in node.children:
                if child_id not in visited:
                    visited.add(child_id)
                    queue.append(path + [child_id])
        return None

    def validate(self) -> list[str]:
        """Return a list of validation errors (broken parent/child refs)."""
        errors: list[str] = []
        for node in self._nodes.values():
            for pid in node.parents:
                if pid not in self._nodes:
                    errors.append(f"Node '{node.id}' references missing parent '{pid}'")
            for cid in node.children:
                if cid not in self._nodes:
                    errors.append(f"Node '{node.id}' references missing child '{cid}'")
        return errors

    def __len__(self) -> int:
        return len(self._nodes)

    def __repr__(self) -> str:
        return f"CanonGraph(nodes={len(self._nodes)}, dir='{self._canon_dir}')"


# ── CLI ───────────────────────────────────────────────────────────────── #

def _cmd_show(args: argparse.Namespace) -> None:
    graph = CanonGraph()
    node = graph.get(args.node)
    if not node:
        print(f"Node '{args.node}' not found.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({
        "id": node.id, "label": node.label, "refs": node.refs,
        "parents": node.parents, "children": node.children, "meta": node.meta,
    }, indent=2))


def _cmd_path(args: argparse.Namespace) -> None:
    graph = CanonGraph()
    path = graph.path_to(args.from_node, args.to_node)
    if path is None:
        print(f"No path from '{args.from_node}' to '{args.to_node}'.", file=sys.stderr)
        sys.exit(1)
    for node in path:
        print(f"  {node.id}: {node.label}")


def _cmd_validate(args: argparse.Namespace) -> None:
    graph = CanonGraph()
    errors = graph.validate()
    if not errors:
        print(f"[OK] Canon graph valid. {len(graph)} nodes loaded.")
    else:
        for e in errors:
            print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(1)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core.canon_graph",
        description="GAIA Canon Graph utility",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("show", help="Show a canon node by ID")
    s.add_argument("--node", required=True)
    s.set_defaults(func=_cmd_show)

    p = sub.add_parser("path", help="Show shortest path between two canon nodes")
    p.add_argument("--from", dest="from_node", required=True)
    p.add_argument("--to",   dest="to_node",   required=True)
    p.set_defaults(func=_cmd_path)

    v = sub.add_parser("validate", help="Validate all canon refs are resolvable")
    v.set_defaults(func=_cmd_validate)

    return parser


if __name__ == "__main__":
    _p = _build_parser()
    _a = _p.parse_args()
    _a.func(_a)
