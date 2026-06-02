# CANON_GRAPH_SPEC.md

Canonical specification for `core/canon_graph.py` — GAIA Canon Dependency Graph.

**Sprint:** G-7 | **Issue:** #169 | **Canon:** C01, C30

---

## Problem

As the canon grows (C42, C43, C75, SME01, and beyond), `canon_loader.py`'s
TF-IDF index over flat markdown documents has no mechanism to track which
entries depend on, supersede, or conflict with others. Finding everything that
depends on C32 is currently a manual `grep` exercise — the **Ontology
Explosion Risk**.

---

## Architecture

```
canon_dir/*.md
  │
  ├─ YAML front-matter parse   →  CanonNode dataclasses
  │                                 (id, title, version, status,
  │                                  requires, supersedes, upstream, tags)
  │
  ├─ nx.DiGraph construction
  │     requires edges:   dep → node
  │     supersedes edges: node → old
  │
  ├─ Cycle detection (requires-only subgraph)
  │     warns but does not raise (C30)
  │
  └─ Query API  +  Safety Gates  +  CLI
```

---

## Symbols

| Symbol | Kind | Description |
|---|---|---|
| `CanonStatus` | `str, Enum` | `active \| deprecated \| draft` |
| `CanonNode` | dataclass | All front-matter fields + `path`, `to_dict()`, `is_active/deprecated/draft()` |
| `CanonGraph` | class | DAG container + full query/safety API |

---

## CanonNode Fields

| Field | Type | Source |
|---|---|---|
| `id` | `str` | Front-matter `id` |
| `title` | `str` | Front-matter `title` |
| `version` | `int` | Front-matter `version` (default 1) |
| `status` | `CanonStatus` | Front-matter `status` (default `active`) |
| `requires` | `List[str]` | Front-matter `requires` |
| `supersedes` | `List[str]` | Front-matter `supersedes` |
| `upstream` | `List[str]` | Front-matter `upstream` (informational; no edges) |
| `tags` | `List[str]` | Front-matter `tags` |
| `path` | `Optional[Path]` | Absolute path to source `.md` file |

---

## Query API

| Method | Returns | Description |
|---|---|---|
| `get(id)` | `CanonNode \| None` | Retrieve a node by ID |
| `__contains__(id)` | `bool` | `id in graph` membership test |
| `__len__()` | `int` | Total node count |
| `dependents(id, direct=False)` | `List[str]` | Nodes that depend on `id` (transitive or direct) |
| `dependencies(id, direct=False)` | `List[str]` | Nodes that `id` depends on (transitive or direct) |
| `is_deprecated(id)` | `bool` | Quick deprecation gate |
| `active_nodes()` | `List[CanonNode]` | All ACTIVE nodes |
| `deprecated_nodes()` | `Iterator[CanonNode]` | All DEPRECATED nodes |
| `draft_nodes()` | `Iterator[CanonNode]` | All DRAFT nodes |
| `nodes_by_tag(tag)` | `List[CanonNode]` | Nodes containing `tag` |
| `has_cycles()` | `bool` | True if any requires-edge cycles detected |
| `cycles()` | `List[List[str]]` | All detected cycles |
| `conflict_check(node)` | `List[str]` | ACTIVE node IDs with 3+ shared tags |
| `impact_report(id)` | `dict` | Full pre-deprecation assessment |
| `summary()` | `dict` | Graph-level counts and stats |

---

## Safety Gates

### `conflict_check(proposed: CanonNode) → List[str]`

Returns IDs of ACTIVE nodes whose tag sets overlap with `proposed` by 3 or
more tags. Use before committing a new canon entry to detect semantic
duplication or contradictions.

### `impact_report(node_id: str) → dict`

Returns:
```python
{
    "node":              CanonNode | None,
    "direct_dependents": List[str],    # immediate graph successors
    "all_dependents":    List[str],    # all transitive descendants
    "supersedes":        List[CanonNode],  # nodes this one replaces
    "cycles":            List[List[str]],  # cycles involving this node
}
```
Use before deprecating or substantially modifying any canon entry.

---

## GAIATrace Integration

A `CANON_LOAD` event is emitted once after `_build()` completes.

```python
{
    "event":            "CANON_LOAD",
    "node_count":       int,
    "active_count":     int,
    "deprecated_count": int,
    "draft_count":      int,
    "edge_count":       int,
    "cycles":           List[List[str]],
}
```

All trace operations are wrapped in `try/except` — a broken trace writer
never blocks a canon graph build.

---

## CanonLoader Integration

`CanonLoader.load()` calls `_build_graph()` after the TF-IDF index build.

```python
# In CanonLoader
self.graph: Optional[CanonGraph] = None   # set by _build_graph()

# Delegate methods:
loader.is_deprecated("C17")               # → bool
loader.dependents("C32")                  # → List[str]
loader.dependencies("C32")                # → List[str]
loader.conflict_check(proposed_node)      # → List[str]
loader.impact_report("C44")               # → dict
```

`graph_enabled=False` skips graph build (useful in unit tests that don't
have a canon directory).

---

## Front-Matter Schema

See `docs/canon/FRONT_MATTER_SCHEMA.md` for the full field reference,
status lifecycle, deprecation process, and incremental adoption guide.

---

## CLI Quick Reference

```bash
python -m core.canon_graph deps C32
python -m core.canon_graph deps C32 --direct
python -m core.canon_graph dependents C32
python -m core.canon_graph impact C44
python -m core.canon_graph conflicts C76 --tags synergy orchestration engines
python -m core.canon_graph deprecated
python -m core.canon_graph draft
python -m core.canon_graph tags synergy
python -m core.canon_graph summary
```

---

## Test Coverage Checklist

- [ ] `test_parse_node_valid`           — front-matter parsed correctly into CanonNode
- [ ] `test_parse_node_no_frontmatter`  — file without front-matter returns None
- [ ] `test_parse_node_missing_id`      — front-matter without `id` returns None
- [ ] `test_graph_builds_edges`         — requires edges wired correctly
- [ ] `test_dependents_transitive`      — A→B→C: dependents(A) = [B, C]
- [ ] `test_dependencies_transitive`    — A→B→C: dependencies(C) = [A, B]
- [ ] `test_direct_dependents`          — direct=True returns only immediate successors
- [ ] `test_is_deprecated`              — deprecated node returns True
- [ ] `test_deprecated_nodes_iter`      — yields only deprecated nodes
- [ ] `test_nodes_by_tag`               — correct subset returned
- [ ] `test_cycle_detection`            — circular requires logs warning, no raise
- [ ] `test_conflict_check_threshold`   — 3-tag overlap triggers, 2-tag does not
- [ ] `test_impact_report_structure`    — correct keys and node references
- [ ] `test_canon_graph_trace_event`    — CANON_LOAD event emitted with correct payload
- [ ] `test_canon_loader_graph_enabled` — graph built after load()
- [ ] `test_canon_loader_graph_disabled`— graph=None when graph_enabled=False
- [ ] `test_canon_loader_delegates`     — loader.is_deprecated / dependents delegate correctly

---

## Related

- **#171** `GAIATrace`    — CANON_LOAD event consumer
- **#170** `task_graph`   — `EngineNode.canon_refs` validated against graph
- **#172** `GAIAStateAdapter` — reads canon refs
- **#173** `MemoryHierarchy`  — uses canon to scope memory searches
- `core/canon_loader.py`  — extended by composition (self.graph)
