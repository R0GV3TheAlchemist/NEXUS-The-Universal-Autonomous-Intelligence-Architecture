# Trust & Permission Policy Engine — Architecture Spec
> Canon ref: C01 (Gaian Sovereignty), SOVEREIGNTY.md
> Issue: #229

## Overview
The Trust & Permission Policy Engine (TPPE) is the mandatory gate between intent and action in GAIA-OS. No agent, loop, or tool invocation executes without passing through TPPE first. It is not optional and not bypassable.

## Core Principle
> "No action without consent. No power without accountability."
> — SOVEREIGNTY.md

## Trust Tiers

| Tier | Label | Examples | Approval Required |
|------|-------|----------|------------------|
| 0 | Safe | Read memory, query RAG, list files | Auto-approved |
| 1 | Guarded | Write files, call APIs, modify state | Session trust level |
| 2 | Sensitive | External comms, delete ops, financial, identity | Explicit Gaian approval |
| 3 | Critical | OS-level changes, data export, boot config | Biometric + explicit approval |

## Architecture

```
[Agent Intent]
      │
      ▼
[TPPE: Classify Action]
      │
      ├── Tier 0 → Auto-approve → [Execute]
      │
      ├── Tier 1 → Check session trust level → [Execute or Gate]
      │
      ├── Tier 2 → Surface approval prompt to Gaian → [Execute or Deny]
      │
      └── Tier 3 → Biometric + explicit approval → [Execute or Deny]
                                    │
                              [Audit Log]
```

## Policy Schema (JSON)

```json
{
  "tool": "github.create_issue",
  "tier": 1,
  "scope": ["repo:write"],
  "requires_session_trust": "standard",
  "audit": true,
  "description": "Creates a new GitHub issue in the specified repository"
}
```

## Session Trust Levels

- **Minimal**: Tier 0 only. Safe reads and queries.
- **Standard**: Tier 0-1. Normal working session.
- **Elevated**: Tier 0-2. Explicitly unlocked by Gaian for a session.
- **Sovereign**: Tier 0-3. Full access. Requires biometric or passphrase confirmation.

## Audit Log Entry Schema

```json
{
  "timestamp": "ISO8601",
  "tool": "string",
  "tier": 0,
  "decision": "approved | denied | pending",
  "session_trust": "standard",
  "gaian_override": false,
  "context_summary": "string"
}
```

## Implementation Plan

### Phase 1 — Core Engine
- [ ] Define policy schema for all existing GAIA tools.
- [ ] Implement tier classification function.
- [ ] Implement session trust level system.
- [ ] Auto-approve Tier 0 actions with audit log.
- [ ] Surface approval prompt for Tier 2+ actions.

### Phase 2 — Policy Editor
- [ ] UI for Gaian to view, edit, and create policy rules.
- [ ] Version control for policy changes.
- [ ] Export and import policy sets.

### Phase 3 — Advanced
- [ ] Biometric gate for Tier 3 actions.
- [ ] Context-aware trust escalation.
- [ ] Policy inheritance and role-based scopes.

## Files to Create
- `src/trust/policy-engine.ts` — core tier classification and approval logic.
- `src/trust/audit-log.ts` — immutable audit trail.
- `src/trust/session-trust.ts` — session trust level management.
- `config/policies/default.json` — default policy definitions for all tools.
- `tests/trust/policy-engine.test.ts` — unit tests for all tiers.

## Dependencies
- Feeds: Agentic Loop (#228), Observability Layer (#231).
- Required by: every autonomous action in GAIA-OS.
