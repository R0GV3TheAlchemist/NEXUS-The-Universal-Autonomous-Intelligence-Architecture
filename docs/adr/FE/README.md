# ADR — Frontend Layer (src/gaian/)

This directory contains Architecture Decision Records for `src/gaian/` — the GAIAN console frontend layer.

For OS-layer decisions, see `../` (the parent `docs/adr/` directory).

---

## ADR Index

| ADR | Title | Status | Date |
|---|---|---|---|
| [ADR-FE-001](ADR-FE-001-language-boundaries.md) | Language Boundaries in src/gaian/ | Accepted | 2026-07-05 |
| [ADR-FE-002](ADR-FE-002-tsx-vs-ts-convention.md) | .tsx vs .ts File Extension Convention | Accepted | 2026-07-05 |
| [ADR-FE-003](ADR-FE-003-gaianruntime-orchestration.md) | GAIANRuntime as Central Execution Loop | Accepted | 2026-07-05 |
| [ADR-FE-004](ADR-FE-004-state-management.md) | State Management in src/gaian/ | Accepted | 2026-07-05 |
| [ADR-FE-005](ADR-FE-005-offline-first-strategy.md) | Offline-First Architecture for the Console | Accepted | 2026-07-05 |
| [ADR-FE-006](ADR-FE-006-meta-control-console-integration.md) | Meta Control Console — GAIA Integration Architecture | Accepted | 2026-07-05 |

---

## When to Write an ADR

Write an ADR for `src/gaian/` when:
- You are choosing between two or more viable approaches for a frontend decision
- A decision affects more than one file in `src/gaian/`
- A new pattern is being established that future files will follow
- The decision involves a language, tooling, or architectural boundary

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for the full ADR protocol.

---

*Governed by: Issue #759 — ADR series for src/gaian/*
*Last updated: 2026-07-05*
