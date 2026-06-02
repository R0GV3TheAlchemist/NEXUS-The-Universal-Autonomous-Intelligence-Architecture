# Canon Front-Matter Schema

Every GAIA canon `.md` file **must** begin with a YAML front-matter block
so that `CanonGraph` can parse it into a `CanonNode`.

```yaml
---
id: C32                          # Required. Canonical ID (C-series, SME-series, etc.)
title: Synergy Doctrine          # Required. Human-readable title.
version: 2                       # Required. Integer; increment on revision.
status: active                   # Required. One of: active | deprecated | draft
requires: [C01, C14]             # Optional. IDs this entry depends on.
supersedes: []                   # Optional. IDs this entry replaces.
upstream: [C29, C34]             # Optional. Thematically upstream context.
tags: [synergy, orchestration, engines]  # Optional. Free-form tags.
---
```

## Field Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | Unique canonical ID. Must be stable — once published, never change. |
| `title` | string | ✅ | Human-readable title. |
| `version` | integer | ✅ | Increment when the entry content changes significantly. |
| `status` | enum | ✅ | `active` (default), `deprecated`, or `draft`. |
| `requires` | list\[string\] | ☐ | IDs of canon entries this one assumes. Creates `requires` edges in the graph. |
| `supersedes` | list\[string\] | ☐ | IDs of older entries this one replaces. Creates `supersedes` edges. |
| `upstream` | list\[string\] | ☐ | Thematically upstream context (informational; no graph edges). |
| `tags` | list\[string\] | ☐ | Free-form tags. Used by `conflict_check()` (3+ shared tags = potential conflict). |

## Status Lifecycle

```
draft  ──→  active  ──→  deprecated
```

- **draft**: Work in progress. Not referenced by GAIA runtime yet.
- **active**: Canonical and in force. Referenced by engines and traces.
- **deprecated**: Superseded or retired. Kept for history. `is_deprecated()` returns True.

## Deprecation Process

Before setting `status: deprecated`:

1. Run `python -m core.canon_graph impact <ID>` to see all dependents.
2. Update or re-point all dependent entries.
3. Set `status: deprecated` and add a `supersedes` pointer in the replacement entry.
4. Commit with a message referencing the Canon ID.

## Incremental Adoption

Files **without** a valid front-matter block are silently skipped by
`CanonGraph._parse_node()`. Front-matter can be added incrementally to
existing canon files — the graph simply grows as files are annotated.

Priority order for adoption:
1. C01, C30, C32 (most referenced in traces and engine nodes)
2. All C-series files in `docs/canon/`
3. Legacy `canon/` directory files
4. SME-series and proposed entries

## Example: C32

```markdown
---
id: C32
title: Synergy Doctrine
version: 2
status: active
requires: [C01, C14]
supersedes: []
upstream: [C29, C34]
tags: [synergy, orchestration, engines, coherence]
---

# Synergy Doctrine

...(body content)...
```

## CLI Quick Reference

```bash
# What does C32 depend on?
python -m core.canon_graph deps C32

# What breaks if I change C32?
python -m core.canon_graph dependents C32

# Full impact report before deprecating C32
python -m core.canon_graph impact C32

# Conflict-check a proposed new entry
python -m core.canon_graph conflicts C76 --tags synergy orchestration engines

# List all deprecated entries
python -m core.canon_graph deprecated

# Graph-level summary
python -m core.canon_graph summary
```
