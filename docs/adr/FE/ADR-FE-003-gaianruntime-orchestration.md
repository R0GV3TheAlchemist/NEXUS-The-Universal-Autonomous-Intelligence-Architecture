# ADR-FE-003: GAIANRuntime as the Central Execution Loop

## Status
Accepted

## Date
2026-07-05

## Context

`GAIANRuntime.ts` is the central orchestration point for the GAIAN console. It manages:
- Session initialization (`sessionInit()`)
- Query processing and context management (`process()`)
- Connection to the Python backend via Tauri IPC
- `RuntimeContext` — the typed state object passed through the execution cycle

Questions that existed before this ADR:
1. Why is the runtime in TypeScript (frontend) rather than Python (backend)?
2. What is the exact boundary between `GAIANRuntime.ts` and the Python core?
3. How are Python errors surfaced in the TypeScript runtime?
4. Is `GAIANRuntime.ts` a singleton or instantiated per session?

## Decision

**`GAIANRuntime.ts` is the TypeScript session orchestrator. It owns the lifecycle of one GAIAN session from init to teardown. The Python core owns all intelligence computation.**

### Why TypeScript for the runtime?

The runtime lives in TypeScript because its primary job is **session lifecycle management and IPC coordination** — both of which are inherently frontend concerns in a Tauri application. The alternative (a Python runtime that drives the session) would require an additional IPC layer and would make the console non-functional when the Python backend is unreachable (violating ADR-FE-005).

### The boundary

| `GAIANRuntime.ts` owns | Python core owns |
|---|---|
| Session start / end | AI inference (RAG, LLM) |
| `RuntimeContext` construction | SpectralForceEngine computation |
| Tauri `invoke()` calls | MagnumOpusStageEngine |
| Error surface (catch + format) | AkashicEngine |
| Profile load/save coordination | All `core/` modules |
| Console state updates | Claim validation, provenance |

### Error handling

Errors from the Python core arrive as rejected Tauri `invoke()` promises. `GAIANRuntime.ts` catches these, formats them into a typed `GAIARuntimeError`, and surfaces them to the console. No raw Python tracebacks reach the UI. The Error Correction Engine (issue #755) hooks into this error surface point.

### Singleton vs. per-session

`GAIANRuntime.ts` is a **per-session singleton** — one instance per active GAIAN session, created at `sessionInit()` and released at session end. It is not a global singleton across the application lifetime.

## Rationale

- Tauri architecture naturally places session management in the frontend
- Offline-first requirement (ADR-FE-005) demands a TypeScript runtime that can operate without the Python backend
- Per-session (not global) singleton keeps state clean across sessions and prevents cross-session contamination

## Consequences

**Easier:** The console can render and operate in degraded mode when Python is unreachable. Error boundaries are well-defined.

**Harder:** Python errors must be explicitly mapped to typed `GAIARuntimeError` objects — this requires maintenance as the Python core evolves.

**New constraint:** No Python computation logic may be added to `GAIANRuntime.ts`. If logic belongs in the backend, it goes in `core/` and is called via `invoke()`.

## Related ADRs
- ADR-FE-001 — Language Boundaries
- ADR-FE-004 — State Management
- ADR-FE-005 — Offline-First Architecture

## Related Issues
- #756 — GAIANProfile (extends RuntimeContext)
- #755 — Error Correction Engine (hooks into GAIANRuntime error surface)
- #439 — Full system prompt injection (GAIANRuntime foundation)
