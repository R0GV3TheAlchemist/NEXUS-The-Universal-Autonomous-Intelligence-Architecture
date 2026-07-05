# ADR-FE-001: Language Boundaries in src/gaian/

## Status
Accepted

## Date
2026-07-05

## Context

`src/gaian/` contains both TypeScript (`.ts`, `.tsx`) and Python (`.py`) files. Without a declared rule, every new contributor faces the same question: which language owns what? The presence of `runtimetypes.py` alongside `GAIANRuntime.ts` in the same directory makes this ambiguity acute.

GAIA's architecture spans three runtimes:
- **Tauri (Rust)** — native shell, window management, OS integration
- **TypeScript** — frontend logic, UI orchestration, session management
- **Python** — AI inference, core reasoning, data pipelines, LCI computation

The IPC boundary between TypeScript and Python is the Tauri `invoke()` channel.

## Decision

**TypeScript owns everything the user sees and interacts with.** Python owns everything that computes, reasons, or persists.

Specific rules:

1. **TypeScript** is the language for: UI components, session orchestration, Tauri IPC calls, profile loading/saving, console adaptation logic, event handling.
2. **Python** is the language for: LCI computation, spectral force resolution, RAG pipeline, Akashic retrieval, AI model calls, data persistence beyond simple key-value storage.
3. **`runtimetypes.py` in `src/gaian/`** is misplaced. It belongs in `src-python/types/` or `core/types/`. It was placed in `src/gaian/` during early prototyping before this boundary was declared. It will be relocated in a follow-up issue.
4. **No Python file should be added to `src/gaian/`** after this ADR is accepted. Python files in the frontend layer indicate a boundary violation.
5. **The IPC contract** (what TypeScript may call on the Python side) must be documented in `docs/api/ipc-contract.md`. Any new IPC command requires that document to be updated.

## Rationale

The TypeScript/Python split mirrors the perceptual/computational split in GAIA's design philosophy: the console is the face, the core is the mind. Keeping them separated by language makes the boundary legible without tooling. A developer looking at a file extension immediately knows which runtime it belongs to.

Alternatives considered:
- **All TypeScript (via node Python bridge):** Rejected. Python's AI/ML ecosystem is non-negotiable for the core.
- **All Python (via server-rendered UI):** Rejected. Tauri's native performance and offline capability require a TypeScript frontend.
- **Mixed freely:** Rejected. This is the current state and it produces exactly the confusion this ADR resolves.

## Consequences

**Easier:**
- New contributors immediately know which language to use for any given task
- Lint, type checking, and testing pipelines can be cleanly separated
- The IPC boundary becomes the single, documented integration point

**Harder:**
- `runtimetypes.py` must be relocated (follow-up issue required)
- Any shared type definitions must be maintained in both languages or generated from a schema

**New constraints:**
- No Python files in `src/gaian/` after this date
- New IPC commands require `docs/api/ipc-contract.md` update before implementation

## Related ADRs
- ADR-0001 (GAIA Kernel Architecture)
- ADR-FE-003 (GAIANRuntime as central execution loop)
- ADR-FE-005 (Offline-first architecture)
