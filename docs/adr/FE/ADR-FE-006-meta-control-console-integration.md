# ADR-FE-006: The Meta Control Console — Integration Architecture

## Status
Accepted

## Date
2026-07-05

## Context

The Meta Control Console is an existing interface (HTML + mobile app) with eight functional domains: Powers, Containment Chamber, Sigil Activation, Crystal Routing, Protection, Recovery, Action Log, and World Service Mode. It must be formally integrated into GAIA's architecture rather than remaining a standalone prototype.

None of the eight domains have a declared mapping to GAIA's existing systems. Without this mapping, integration work will be inconsistent, duplicative, or structurally incorrect.

## Decision

**The Meta Control Console becomes a dedicated view inside `src/gaian/`**, implemented as `MetaControlConsole.tsx`. It is not a separate Tauri window. It shares session state with `GAIANRuntime.ts` and adapts based on `GAIANProfile`.

### Domain Mappings

| Meta Control Domain | GAIA System Mapping |
|---|---|
| **Power Containment Chamber** | `core/sentinel/` — safety checks that run before any power activation. A power cannot activate if `core/sentinel/` returns a block. |
| **Sigil Activation** (requires Magic ≥ 30) | Constitutional Layer — LCI threshold enforcement. `sigil.activate()` calls the Constitutional Layer gate before execution. Magic ≥ 30 maps to `lci ≥ 0.30` in `GAIANProfile`. |
| **Crystal Routing** (Amethyst, Clear Quartz, Obsidian, etc.) | `SpectralForceEngine` crystal resonance. Each crystal maps to a named spectral force. Routing a crystal activates the corresponding spectral configuration in the engine. |
| **Recovery Mode** (Order Map, Stability Meter, Trust Process) | `lciTrend: 'volatile'` in `GAIANProfile`. Recovery Mode is surfaced automatically when the LCI trend crosses the volatile threshold. The Stability Meter reads from `stabilityIndex` in the profile. |
| **Action Log** ("Every action writes a visible result here") | Provenance Layer (issue #753). Every action dispatched through `GAIANRuntime.ts` writes a provenance record. The Action Log is a read view of the provenance stream. |
| **World Service Mode** (Healing, Protection, Clarity, Balance) | Constitutional Layer ethical guardrails. World Service Mode activates only when the Constitutional Layer confirms the action is within ethical bounds. The four modes map to named ethical operation profiles. |
| **Ability Selection** (Core, Mission, Emergency, Experimental) | `GAIANModule` types in `GAIANProfile`. Each ability category corresponds to a module type. Ability activation loads the corresponding module configuration. |
| **Human Mode / Superhuman Mode toggle** | Constitutional Layer consent enforcement. Mode toggle is a consent event. The Constitutional Layer records it with timestamp and LCI snapshot. It cannot be toggled without explicit user action — no automatic escalation. |

### Implementation Path

1. `MetaControlConsole.tsx` is created as a new view in `src/gaian/`
2. It reads `GAIANProfile` from `GAIANRuntime.ts` — no direct store access
3. Each domain panel calls through `GAIANRuntime.ts` via typed action dispatchers
4. The runtime routes each action through the appropriate GAIA system (sentinel, Constitutional Layer, SpectralForceEngine, provenance)
5. Results are written to the Action Log (provenance stream) before being displayed

### What the Meta Control Console Is Not
- It is not a superuser bypass. Every action goes through the same Constitutional Layer gates as any other action.
- It is not a separate application. It shares the runtime, the profile, and the provenance layer.
- It is not always visible. It surfaces based on `GAIANProfile.activeModules` and the current LCI state.

## Rationale

Integrating the Meta Control Console as a view rather than a separate window keeps the session context unified. The person is always one identity, in one session, with one provenance record. Splitting into separate windows would fragment this.

The domain mappings ensure that the Meta Control Console's powerful capabilities are constrained by the same Constitutional Layer that governs all of GAIA. Power without constraint is the opposite of what this system is designed to provide.

## Consequences

**Easier:**
- Every Meta Control action is audited via the provenance layer automatically
- Recovery Mode surfaces without manual invocation — it responds to the LCI
- The Constitutional Layer is the single enforcement point for all ability activation

**Harder:**
- `MetaControlConsole.tsx` is a significant implementation effort — it should be built in phases aligned with Milestone 5
- Crystal Routing requires `SpectralForceEngine` to be fully implemented first
- The Action Log requires the Provenance Layer (issue #753) to be implemented first

**New constraints:**
- No Meta Control action may bypass `core/sentinel/` or the Constitutional Layer
- Human Mode / Superhuman Mode toggle requires explicit user consent — no programmatic escalation
- The Action Log is read-only from the console — provenance records are immutable

## Related ADRs
- ADR-FE-003 (GAIANRuntime as central execution loop)
- ADR-FE-004 (State management)
- ADR-FE-005 (Offline-first architecture)
- Related issues: #753 (Provenance Layer), #742 (Security Model), #754 (Human Coherence), #756 (GAIANProfile)
- Milestone: M5 Meta Control
