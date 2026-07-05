# ADR-FE-004: State Management in src/gaian/ (No Redux/Zustand)

## Status
Accepted

## Date
2026-07-05

## Context

The `src/gaian/` layer manages state without a centralized state management library (no Redux, Zustand, Jotai, MobX, or equivalent). This is not an oversight — it is a deliberate architectural choice that must be documented so future contributors do not introduce a state library assuming one is missing.

The introduction of `GAIANProfile` (issue #756) adds a significant new state object: the persistent identity of the GAIAN across sessions. Its placement in the state hierarchy must be declared.

## Decision

**State in `src/gaian/` is managed through three and only three mechanisms:**

1. **`GAIANRuntime.ts` module-level singleton** — holds session-scoped state (current profile snapshot, active LCI, session context). This is the source of truth for the running session.
2. **`@tauri-apps/plugin-store`** — holds persistent state (GAIANProfile, user preferences, calibration history). This is the source of truth across sessions.
3. **Local component state** — holds ephemeral UI state (input field content, scroll position, animation state) that does not need to survive a component unmount.

**`GAIANProfile` lives in `@tauri-apps/plugin-store`** as the persistent record, and is loaded into `GAIANRuntime.ts` as a session snapshot at startup. Components read profile data from the runtime, not directly from the store.

**Why no Redux/Zustand/Jotai:**
- GAIA's frontend state is not complex enough to require a reactive global store. There is one primary state object (`GAIANProfile`) and one session orchestrator (`GAIANRuntime.ts`). A state library would add indirection without adding capability.
- Tauri's plugin-store already provides the persistence layer. Adding a separate state management library would create two sources of truth for the same data.
- The offline-first requirement (ADR-FE-005) is simpler to implement when persistence is handled directly by the Tauri store rather than mediated through a reactive state library.

## Rationale

The three-mechanism model (runtime singleton + Tauri store + local state) maps directly onto the three scopes of state in GAIA: session, persistent, and ephemeral. Each scope has exactly one owner. This makes state predictable and auditable without tooling.

Alternatives considered:
- **Zustand:** Rejected. Adds a dependency and a reactive graph for a problem that a singleton solves directly.
- **Redux Toolkit:** Rejected. Significant overhead for a single primary state object.
- **Jotai / Recoil:** Rejected. Atom-based state is appropriate for complex UI trees with many independent state slices. GAIA's console is not that.

## Consequences

**Easier:**
- State flow is traceable without DevTools or middleware
- Persistence is always explicit — no hidden reactive writes to disk
- New contributors can read state management from the code without learning a library

**Harder:**
- Cross-component state sharing requires going through `GAIANRuntime.ts` rather than a hook
- If the console grows significantly in complexity, this decision should be revisited (file a new ADR)

**New constraints:**
- No state management library may be added to `src/gaian/` without a superseding ADR
- `GAIANProfile` must not be accessed directly from `@tauri-apps/plugin-store` in components — always go through the runtime

## Related ADRs
- ADR-FE-003 (GAIANRuntime as central execution loop)
- ADR-FE-005 (Offline-first architecture)
- Related issue: #756 (GAIANProfile)
