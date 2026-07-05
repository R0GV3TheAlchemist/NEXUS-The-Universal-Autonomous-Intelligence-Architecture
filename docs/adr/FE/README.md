# Frontend Architecture Decision Records

All ADRs governing the GAIA-OS Tauri / TypeScript frontend layer.

Parent index: [`docs/adr/README.md`](../README.md)

---

## Numbering Convention

`ADR-FE-NNN-slug.md` — FE prefix distinguishes frontend decisions from backend/core ADRs.

---

## ADR Index

| # | Title | Status | Implemented |
|---|---|---|---|
| [ADR-FE-001](ADR-FE-001-language-boundaries.md) | Language Boundaries — TypeScript owns the UI layer; Python owns the kernel | Accepted | ✅ |
| [ADR-FE-002](ADR-FE-002-tsx-vs-ts-convention.md) | TSX vs TS — `.tsx` only when JSX is present; `.ts` otherwise | Accepted | ✅ |
| [ADR-FE-003](ADR-FE-003-gaianruntime-orchestration.md) | GAIANRuntime Orchestration — 7-step sessionInit sequence | Accepted | ✅ M1 |
| [ADR-FE-004](ADR-FE-004-state-management.md) | State Management — GAIANProfile via Tauri Store; ephemeral state in RuntimeContext | Accepted | ✅ M1 |
| [ADR-FE-005](ADR-FE-005-offline-first-strategy.md) | Offline-First Strategy — profile load always runs regardless of network | Accepted | ✅ M1 |
| [ADR-FE-006](ADR-FE-006-meta-control-console-integration.md) | Meta Control Console Integration — MCC power commands, LCI gates, ConstitutionalLayer | Accepted | ⬜ M2–M5 |

---

## M1 — Core Runtime Identity (Issue #756) — ✅ Complete

**Completed: 2026-07-05**

Three files written / updated:

| File | Change |
|---|---|
| `src/gaian/GAIANProfile.ts` | New — persistent identity layer (GAIANProfile, GAIANProfileManager, ConstitutionalLayer, computeLCITrend) |
| `src/gaian/GaianBirth.ts` | Updated — 3-step birth wizard fully wired; saves GAIANProfile on successful birth |
| `src/gaian/GAIANRuntime.ts` | Updated — RuntimeContext extended with `profile?`; sessionInit wired with 7-step sequence; `[GAIAN IDENTITY]` context block added to SystemPromptBuilder |

ADRs satisfied by M1: **ADR-FE-003, ADR-FE-004, ADR-FE-005**

---

## M2–M5 — Roadmap

| Milestone | Scope | ADR |
|---|---|---|
| M2 | LCI Live Computation — phi updated from real session data; `lciBaseline` written back to profile | ADR-FE-003, ADR-FE-004 |
| M3 | Crystal System — crystal selection UI; `preferredCrystal` persisted; SpectralForceEngine reads crystal | ADR-FE-006 |
| M4 | Constitutional Layer UI — Sigil Lock, Service Mode, Human/Superhuman toggle wired to profile | ADR-FE-006 |
| M5 | MCC Power Commands — 12 command implementations (ACTIVATE, DEACTIVATE, MODIFY, ENHANCE, COMBINE, SPLIT, STORE, TRANSFER, MONITOR, SEARCH, CUSTOMIZE, DELETE) | ADR-FE-006 |

---

## Adding a New FE ADR

1. Copy `../ADR-000-template.md`
2. Name it `ADR-FE-NNN-slug.md` (next available number)
3. Fill in all sections — Status must be `Draft` until PR is merged
4. Add a row to the index table above
5. Add a row to the parent `docs/adr/README.md` table
6. Open a PR referencing the relevant issue
