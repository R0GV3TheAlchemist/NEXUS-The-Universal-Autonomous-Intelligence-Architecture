# ADR-FE-003: GAIANRuntime as the Central Execution Loop

## Status
Accepted

## Date
2026-07-05

## Context

`GAIANRuntime.ts` is the single TypeScript file responsible for session initialization, context management, and result processing in the GAIAN console. The question of why this runtime lives in TypeScript (frontend) rather than Python (backend) — and what its exact responsibilities are — was not previously documented.

Without this documentation, contributors risk either duplicating runtime logic in Python or moving responsibilities into the wrong layer.

## Decision

**`GAIANRuntime.ts` is the TypeScript-side session orchestrator.** It owns the lifecycle of a single GAIAN session from the user's perspective. It does not own inference, computation, or reasoning — those belong to the Python core.

Responsibilities of `GAIANRuntime.ts`:
1. Session initialization — load `GAIANProfile`, establish IPC connection to Python sidecar
2. Context assembly — collect current session context (profile state, LCI snapshot, active modules) before each query
3. IPC dispatch — send assembled context + query to Python via Tauri `invoke()`
4. Result processing — receive Python response, apply console adaptation rules, route to correct view
5. Error surfacing — catch IPC failures, apply offline fallback strategy (see ADR-FE-005)
6. Session teardown — persist profile state on session end

**`GAIANRuntime.ts` is a singleton.** One instance per application lifetime. It is instantiated once in the Tauri app entry point and passed via context or accessed via module-level export.

**`GAIANRuntime.ts` is TypeScript (not Python) because** the session lifecycle is a frontend concern. The user opens the app, interacts with the console, closes the app — this arc is owned by the UI layer. Python is stateless across IPC calls; state continuity is the runtime's job.

## Rationale

The alternative — a Python-side session manager — would require the Python sidecar to maintain state between Tauri IPC calls. This creates a tight coupling between the frontend and the sidecar's internal state, making offline resilience (ADR-FE-005) significantly harder. A TypeScript-side runtime that holds session state locally and calls Python only for computation is cleaner, more testable, and more resilient.

## Consequences

**Easier:**
- Session state is always local to the frontend — offline resilience is achievable
- Python sidecar can be restarted without losing session context
- TypeScript unit tests can mock the IPC layer cleanly

**Harder:**
- Any state that Python needs to "remember" across calls must be passed explicitly in each IPC payload
- The IPC contract must be comprehensive (see ADR-FE-001)

**New constraints:**
- `GAIANRuntime.ts` must remain a singleton
- No session state may be stored exclusively in the Python sidecar
- All IPC calls go through `GAIANRuntime.ts` — no component calls `invoke()` directly

## Related ADRs
- ADR-FE-001 (Language boundaries)
- ADR-FE-004 (State management)
- ADR-FE-005 (Offline-first architecture)
- Related issue: #439 (Full system prompt injection)
