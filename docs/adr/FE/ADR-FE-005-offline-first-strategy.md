# ADR-FE-005: Offline-First Architecture for the Console

## Status
Accepted

## Date
2026-07-05

## Context

The GAIAN console must render a meaningful, stable state even when the Python backend is unreachable. This is not an edge case — it is a design requirement. The console is a personal intelligence layer. It must be present for the person even when the network is down, the sidecar has crashed, or the AI provider is unreachable.

Without a declared offline strategy, the console will silently fail or render blank screens, which is the opposite of what a stability-oriented system should do.

## Decision

**The console must always render.** Degraded mode is acceptable. Blank screens are not.

The offline-first strategy has three tiers:

### Tier 1: Python Sidecar Unreachable
- `GAIANRuntime.ts` catches the IPC failure
- Console renders from the last known `GAIANProfile` snapshot (held in runtime memory)
- User sees a status indicator: "Core offline — working from last known state"
- All profile-driven adaptation (greeting, module display, LCI color) continues from cached data
- New queries are queued locally and replayed when the sidecar reconnects

### Tier 2: Profile Store Unreadable
- `@tauri-apps/plugin-store` read fails
- Console renders with a safe default profile (`phi: 0.5`, no active modules, neutral LCI)
- User is informed: "Profile unavailable — using defaults"
- No data is written until the store is confirmed writable

### Tier 3: Full Offline (No Sidecar, No Store)
- Console renders the GAIA welcome screen with static content
- No AI features are available
- User sees: "GAIA is offline. Your profile will load when connectivity is restored."
- No error states, no crashes, no blank screens

**Persistence mechanism:** `@tauri-apps/plugin-store` is the single persistence layer for the console. SQLite is not used at the frontend layer. The filesystem is not accessed directly.

**Maximum acceptable staleness for cached profile data:** One session (the profile is refreshed from store on every app launch). Mid-session, the runtime snapshot is authoritative.

## Rationale

A system designed to support human stability cannot itself be unstable. The offline-first requirement is a direct expression of GAIA's Constitutional Layer: the console must not fail the person when they need it most.

The three-tier degradation model ensures that each failure mode has a named, predictable response. Named failure modes are manageable. Unnamed failure modes become chaos.

## Consequences

**Easier:**
- Console is always testable without a running Python sidecar
- Users trust the console because it never goes blank on them
- Failure modes are explicit and can be tested independently

**Harder:**
- `GAIANRuntime.ts` must implement reconnection logic
- Default profile values must be maintained and kept meaningful
- UI must include status indicators for each offline tier

**New constraints:**
- Console must pass a "no sidecar" smoke test before any PR is merged
- Blank screens are a bug, not a feature, in every failure mode

## Related ADRs
- ADR-FE-003 (GAIANRuntime as central execution loop)
- ADR-FE-004 (State management)
- ADR-FE-006 (Meta Control Console integration)
- Related issue: #756 Phase 4 (Offline-First Resilience)
