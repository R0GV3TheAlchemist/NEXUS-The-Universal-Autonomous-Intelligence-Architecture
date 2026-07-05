# ADR-FE-004: State Management in src/gaian/

## Status
Accepted

## Date
2026-07-05

## Context

`src/gaian/` contains no Redux, Zustand, Jotai, MobX, or any other centralized state management library. State appears to be managed through:
- `RuntimeContext` — a typed object passed through `GAIANRuntime.ts`
- File-level module state in individual `.ts` files
- Tauri store (for persistence)
- Direct Tauri IPC for cross-boundary communication

This raised the question: is this a deliberate architectural decision, or an oversight that will cause problems as the codebase grows?

With `GAIANProfile` (issue #756) introducing persistent per-user state, and the Meta Control Console (ADR-FE-006) introducing power state, the state management question becomes urgent.

## Decision

**`src/gaian/` uses `RuntimeContext` as its primary state carrier, extended by `GAIANProfile` for persistent state. No third-party state management library is introduced.**

The rationale for avoiding Redux/Zustand/Jotai:
1. The console is not a traditional React SPA with deeply nested component trees — it is a Tauri desktop application with a focused set of surfaces
2. `RuntimeContext` already provides a typed, session-scoped state object
3. Adding a state library introduces a dependency and a new mental model that the existing architecture does not need
4. Tauri's `@tauri-apps/plugin-store` handles cross-session persistence — this is the "store" layer

### State hierarchy (after issue #756)

```
Tauri Store (persistent, across sessions)
  └── GAIANProfile (loaded at sessionInit, saved at session end)
        └── RuntimeContext (ephemeral, per-session)
              └── Individual component state (ephemeral, per-render)
```

### Shared state passing

Shared state (current `phi`, active `spectral_force`, `GAIANProfile`) is passed explicitly through `RuntimeContext` — not through global singletons or event buses. Components read from `RuntimeContext`, not from each other.

### When to revisit this decision

This decision should be revisited if:
- Component count in `src/gaian/` exceeds 20 files with shared state dependencies
- A new surface requires state that spans multiple sessions without going through `GAIANProfile`
- Performance profiling shows prop-drilling overhead becoming significant

## Rationale

- Keeps the architecture simple and consistent with existing patterns
- Avoids unnecessary dependencies in a desktop application context
- `GAIANProfile` + `RuntimeContext` provides a typed, auditable state chain

## Consequences

**Easier:** No new library to learn. State flow is explicit and traceable.

**Harder:** As the console grows, `RuntimeContext` may become large. Must be actively pruned.

**New constraint:** No state management library may be added to `src/gaian/` without a new ADR that supersedes this one.

## Related ADRs
- ADR-FE-003 — GAIANRuntime as Central Execution Loop
- ADR-FE-005 — Offline-First Architecture
- ADR-FE-006 — Meta Control Console Integration

## Related Issues
- #756 — GAIANProfile (the persistent state layer)
- #759 — ADR series for src/gaian/
