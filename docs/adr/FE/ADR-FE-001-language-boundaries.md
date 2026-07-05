# ADR-FE-001: Language Boundaries in src/gaian/

## Status
Accepted

## Date
2026-07-05

## Context

`src/gaian/` contains files in two languages:

- **TypeScript** (`.ts`, `.tsx`): `GAIANRuntime.ts`, `GaianBirth.ts`, `GaianHome.ts`, `GaianChatView.ts`, `CrystalView.tsx`, `GaianMood.ts`, `GaianOrb.ts`, `AlignmentIndicator.ts`, `OrbParams.ts`, `ViriditasTheme.ts`
- **Python** (`.py`): `runtimetypes.py`

No rule existed before this ADR to explain why a Python file lives in the TypeScript frontend directory, which language should own what logic, or what the IPC boundary between the two is.

This creates ambiguity for every developer working in `src/gaian/` and for automated tooling (linters, type checkers, CI) that must handle two language runtimes in one directory.

## Decision

**TypeScript owns the frontend layer. Python owns the backend core.**

The rule is:

| Layer | Language | Location |
|---|---|---|
| UI rendering, console surfaces, Tauri IPC client | TypeScript (`.ts`, `.tsx`) | `src/gaian/` |
| Runtime orchestration (session init, context management) | TypeScript | `src/gaian/GAIANRuntime.ts` |
| AI inference, RAG pipeline, spectral computation, data models | Python | `core/` |
| Shared type definitions used by the Python backend | Python | `core/` or `src/python/` — **NOT** `src/gaian/` |

**`runtimetypes.py` is misplaced.** It lives in `src/gaian/` by accident of early development, not by design. It must be migrated to `core/` or a dedicated `src/python/` directory as part of issue #756 (GAIANProfile).

**The IPC boundary** is the Tauri command layer. TypeScript calls `invoke()` from `@tauri-apps/api`. Python backend receives these via Tauri's Rust command handlers. No Python file should live in `src/gaian/` — that directory is the TypeScript frontend.

## Rationale

- Mixing languages in a single directory breaks tooling assumptions (ESLint, tsc, Ruff all need to know their scope)
- The Tauri architecture naturally enforces a frontend/backend split at the IPC boundary — this ADR makes that split explicit in directory structure
- Future developers must not have to guess which language owns a piece of logic

## Consequences

**Easier:** Linting, type checking, and CI configuration. New developers understand the layer immediately.

**Harder:** `runtimetypes.py` must be migrated (tracked in issue #756). Any existing import paths that reference `src/gaian/runtimetypes.py` must be updated.

**New constraint:** No `.py` file may be created in `src/gaian/`. PR review must catch this.

## Related ADRs
- ADR-0001 — GAIA Kernel Architecture (OS-layer boundary definitions)
- ADR-FE-003 — GAIANRuntime as Central Execution Loop
- ADR-FE-005 — Offline-First Architecture

## Related Issues
- #756 — GAIANProfile (migration of runtimetypes.py)
- #759 — ADR series for src/gaian/
