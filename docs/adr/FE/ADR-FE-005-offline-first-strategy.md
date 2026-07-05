# ADR-FE-005: Offline-First Architecture for the GAIAN Console

## Status
Accepted

## Date
2026-07-05

## Context

The GAIAN console is a Tauri desktop application with a TypeScript frontend and a Python backend. The Python backend handles AI inference, RAG, and all `core/` computations. If the Python backend is unreachable (process crash, startup failure, dependency missing), the console must not show a blank screen or an unhandled error.

This is especially critical because:
- The console is a personal tool used in sensitive, high-stakes moments
- A blank screen when a person needs grounding or clarity is a failure that matters
- `GAIANProfile` (issue #756) provides a cached state that can serve as a meaningful fallback

## Decision

**The GAIAN console must render a meaningful, stable state even when the Python backend is unreachable. No component in `src/gaian/` may show a blank or broken state.**

### Persistence layer

The persistence layer uses **`@tauri-apps/plugin-store`** (Tauri's built-in key-value store). This was chosen over:
- Raw filesystem: less structured, no atomic writes
- SQLite: heavier dependency for the data volume required
- IndexedDB: browser-only, not available in Tauri WebView context

Maximum acceptable staleness for cached profile data: **the last completed session** (no time limit — the last known good state is always better than no state).

### Fallback rendering strategy

When `GAIANRuntime.ts` cannot reach the Python backend:

1. `GAIANProfileManager.load(architectId)` is called — always offline-capable
2. The last known `GAIANProfile` is injected into `RuntimeContext`
3. Console surfaces render from cached profile:
   - `CrystalView.tsx` renders last known `activeModules`
   - `AlignmentIndicator.ts` renders last known `lciHistory`
   - `GaianOrb.ts` renders with last known `orbParams`
   - `GaianMood.ts` renders with `lciTrend: 'volatile'` to signal degraded mode
4. A non-blocking status indicator shows "Backend unreachable — showing last known state"
5. No component throws, crashes, or shows undefined/null

### Components must never show blank state

Every component in `src/gaian/` must have a defined fallback for every rendered value. There is no acceptable case where a missing backend results in an empty UI.

## Rationale

- A personal console that goes blank when most needed is worse than no console
- `GAIANProfile` provides exactly the cached state needed for meaningful offline rendering
- `@tauri-apps/plugin-store` is the natural persistence layer for Tauri applications

## Consequences

**Easier:** Users always see a stable console. Recovery from backend failure is graceful.

**Harder:** Every new component must implement a fallback rendering path. This is a permanent maintenance requirement.

**New constraint:** PR review for any `src/gaian/` component must verify offline fallback exists. The PR checklist includes this check.

## Related ADRs
- ADR-FE-003 — GAIANRuntime as Central Execution Loop
- ADR-FE-004 — State Management

## Related Issues
- #756 — GAIANProfile (Phase 4: Offline-First Resilience)
- #755 — Error Correction Engine
- #759 — ADR series for src/gaian/
