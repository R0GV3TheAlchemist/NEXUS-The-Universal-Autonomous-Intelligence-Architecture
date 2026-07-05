# Architecture Decision Records

This directory contains all Architecture Decision Records (ADRs) for the GAIA project.

ADRs document significant architectural decisions — what was decided, why, and what the consequences are.
They are **append-only**: once accepted, an ADR is never deleted. Superseded decisions are marked with a
`Superseded by:` reference.

---

## How to Use

- New decisions: copy `ADR-000-template.md`, fill it in, open a PR
- Number format: `ADR-NNNN-slug.md` for backend/core; `ADR-FE-NNN-slug.md` for frontend (see `FE/`)
- Status values: `Draft` | `Accepted` | `Superseded` | `Deprecated`

---

## Backend / Core ADRs

| # | Title | Status |
|---|---|---|
| [ADR-0001](ADR-0001-gaia-kernel-architecture.md) | GAIA Kernel Architecture | Accepted |
| [ADR-001](ADR-001-knowledge-type-taxonomy.md) | Knowledge Type Taxonomy | Accepted |
| [ADR-002](ADR-002-v0.1-minimal-pipeline.md) | v0.1 Minimal Pipeline | Accepted |
| [ADR-003](ADR-003-architecture-evolution-principle.md) | Architecture Evolution Principle | Accepted |
| [ADR-0009](ADR-0009-langgraph-canonical-orchestrator.md) | LangGraph Canonical Orchestrator | Accepted |
| [ADR-0010](ADR-0010-mcp-canonical-tool-interface.md) | MCP Canonical Tool Interface | Accepted |
| [ADR-0011](ADR-0011-cloud-as-optional-sovereignty.md) | Cloud as Optional Sovereignty | Accepted |

---

## Frontend ADRs

All frontend decisions live in [`FE/`](FE/README.md).

| # | Title | Status |
|---|---|---|
| [ADR-FE-001](FE/ADR-FE-001-language-boundaries.md) | Language Boundaries (TS/Python) | Accepted |
| [ADR-FE-002](FE/ADR-FE-002-tsx-vs-ts-convention.md) | TSX vs TS Convention | Accepted |
| [ADR-FE-003](FE/ADR-FE-003-gaianruntime-orchestration.md) | GAIANRuntime Orchestration | Accepted |
| [ADR-FE-004](FE/ADR-FE-004-state-management.md) | State Management (Tauri Store) | Accepted |
| [ADR-FE-005](FE/ADR-FE-005-offline-first-strategy.md) | Offline-First Strategy | Accepted |
| [ADR-FE-006](FE/ADR-FE-006-meta-control-console-integration.md) | Meta Control Console Integration | Accepted |

---

## Template

See [ADR-000-template.md](ADR-000-template.md) for the canonical ADR format.
