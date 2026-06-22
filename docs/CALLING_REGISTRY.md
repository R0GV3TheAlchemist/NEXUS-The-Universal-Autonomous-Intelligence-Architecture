# 📞 GAIA-OS Calling Registry

**Purpose:** The authoritative index of all callings received across working sessions with The Human Architect. Callings are strategic directives that shape what gets built. This registry makes them durable — no calling is lost between sessions.

**Governing Issue:** [#606 — Meta-Simulation System](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/606)

**Rule:** This document is the **first thing reviewed** at the start of every working session.

---

## 📖 Status Definitions

| Status | Meaning |
|---|---|
| `active` | Calling received; not yet converted to an issue |
| `converted` | Calling has a corresponding GitHub issue |
| `fulfilled` | Issue complete; simulation passing; proof committed |
| `deferred` | Intentionally paused; reason documented in YAML |

Callings are **never deleted** — only `deferred` or `fulfilled`.

---

## 📊 Calling Index

| ID | Date | Title | Type | Urgency | Status | Issue |
|---|---|---|---|---|---|---|
| CL-001 | 2026-06-22 | Simulate the simulation system | strategy | high | converted | [#606](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/606) |
| CL-002 | 2026-06-22 | We need a stronger strategy | strategy | high | converted | [#606](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/606) |

---

## 📦 YAML Files

Each calling has a corresponding YAML file in the `callings/` directory:

```
callings/
  CL-001-simulate-simulation-system.yaml
  CL-002-stronger-strategy.yaml
```

New callings follow the naming convention:
```
CL-{NNN}-{short-slug}.yaml
```

---

## 📋 Calling Schema

Every calling YAML must include these fields:

```yaml
calling_id: CL-NNN
date_received: YYYY-MM-DD
source: "Session with GAIA/Perplexity"
title: "Short title"
body: |
  Full description of the calling.
type: strategy          # strategy | build | doctrine | investigation
urgency: high           # critical | high | medium | low
status: active          # active | converted | fulfilled | deferred
converted_to_issue: "#NNN"   # required before status can be 'converted'
simulation_required: true
proof_required: true
canon_links: []         # list of canon IDs this calling relates to
notes: |
  Optional context.
```

**Validation rules:**
- No calling may be marked `converted` without a corresponding GitHub issue number
- No calling may be marked `fulfilled` without a corresponding passing simulation and committed proof
- Every calling of type `strategy` requires a simulation
- Every calling of type `doctrine` requires a canon entry

---

## 🔄 Session Protocol

### Session Opening (run at the start of every session)

```
□ 1. Open this file — review all active and converted callings
□ 2. Open #588 Master Audit Registry — confirm current phase
□ 3. Open #587 Roadmap — identify the next gate
□ 4. Select work: highest-urgency calling that unblocks the next gate
□ 5. State the session intention before beginning
```

### Session Closing (run before ending every session)

```
□ 1. Capture any new callings as YAML in callings/ (do this first)
□ 2. Update this registry with new and changed statuses
□ 3. Update #588 Master Audit Registry with completions
□ 4. Note next session's starting point in the last row of the index
□ 5. Confirm: no calling is left uncaptured
```

---

## 🗒️ Next Session Starting Point

**Last updated:** 2026-06-22
**Next session should begin with:**
- CL-001 and CL-002 are `converted` — their issue (#606) is open and ready to build
- Phase 0 of the Audit Roadmap (#587) must pass before Phase 1 begins
- Highest priority active build: #589 (Three Missing Connections) — Phase 1 gate
- All 16 issues from today's session (#591–#606) are registered in #588

---

*Calling Registry established June 22, 2026. Governed by issue #606.*
