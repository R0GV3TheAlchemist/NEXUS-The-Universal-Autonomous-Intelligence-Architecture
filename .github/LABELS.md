# GAIA Label Definitions

> **Status:** Active — June 29, 2026  
> **Purpose:** Canonical reference for all GitHub issue labels used in this repository.  
> **Cross-Reference:** `docs/SUPER_VS_MAGIC.md` · `docs/SUPERCOMPUTER_DOCTRINE.md` · `.github/workflows/super-migration-scanner.yml`

Labels are the first layer of order. Every issue should carry at least one **Phase** label and one **Status** label. Migration labels are applied automatically by the Super Migration Scanner workflow.

---

## Migration Labels (Auto-applied by Scanner)

| Label | Color | Meaning |
|---|---|---|
| `needs-super-migration` | 🔴 `#e11d48` | Issue body or title contains operative "magic" or unlabeled metaphysical language. Must be reviewed and reframed per `docs/SUPER_VS_MAGIC.md` before the issue can be worked. |
| `super-aligned` | 🟢 `#16a34a` | Issue has been reviewed and confirmed to use only super/coherence/field language. Safe to work. |
| `migration-exempt` | ⚪ `#94a3b8` | Issue uses "magic" only in Category 2 (governance) or Category 3 (idiomatic denial) sense. No migration needed. |

---

## Phase Labels

| Label | Color | Meaning |
|---|---|---|
| `phase:canon` | 🟣 `#7c3aed` | Relates to canon documents, law stack, or doctrinal definitions. |
| `phase:super-migration` | 🔴 `#dc2626` | Part of the active magic→super migration sprint. |
| `phase:supercomputation` | 🔵 `#1d4ed8` | Relates to the supercomputer/computation alignment phase. |
| `phase:simulation` | 🟡 `#ca8a04` | Relates to simulation layer, documentation simulation, or proof runs. |
| `phase:ui-ux` | 🟠 `#ea580c` | Relates to frontend, interface, or user experience. |
| `phase:infrastructure` | ⚫ `#374151` | Relates to CI/CD, Docker, k8s, deployment, or tooling. |
| `phase:research` | 🩵 `#0891b2` | Research task, hypothesis, or external reference work. |

---

## Status Labels

| Label | Color | Meaning |
|---|---|---|
| `status:ready` | 🟢 `#16a34a` | Issue is fully defined and ready to be worked. |
| `status:blocked` | 🔴 `#dc2626` | Issue cannot proceed until a dependency is resolved. |
| `status:in-progress` | 🔵 `#2563eb` | Actively being worked in the current sprint. |
| `status:needs-review` | 🟡 `#d97706` | Work is complete; awaiting review or validation. |
| `status:deferred` | ⚫ `#6b7280` | Intentionally deferred to a future sprint. |
| `status:duplicate` | ⚪ `#94a3b8` | Duplicate of another issue (will be linked and closed). |

---

## Priority Labels

| Label | Color | Meaning |
|---|---|---|
| `priority:critical` | 🔴 `#b91c1c` | Blocks the current phase or breaks the system. Work immediately. |
| `priority:high` | 🟠 `#c2410c` | Important for phase completion. Work this sprint. |
| `priority:medium` | 🟡 `#a16207` | Should be completed soon, but not blocking. |
| `priority:low` | ⚪ `#6b7280` | Nice to have. Defer if needed. |

---

## Domain Labels

| Label | Color | Meaning |
|---|---|---|
| `domain:canon` | 🟣 `#6d28d9` | Canon documents, law stack, epistemic framework. |
| `domain:core-engine` | 🔵 `#1e40af` | Core Python engine, Akashic Trinity, coherence calculations. |
| `domain:shadow-engine` | ⚫ `#1f2937` | Shadow engine, paradox processing, integration layer. |
| `domain:simulation` | 🟡 `#854d0e` | Simulation and proof layers. |
| `domain:ui` | 🟠 `#9a3412` | UI components, Tauri frontend, user-facing interfaces. |
| `domain:api` | 🩵 `#0e7490` | API layer, routes, schemas, data contracts. |
| `domain:docs` | 🟢 `#166534` | Documentation, README, guides. |
| `domain:tests` | ⚪ `#475569` | Test suite, coverage, CI assertions. |

---

## How Labels Work Together

A well-labeled issue looks like:

```
[needs-super-migration] [phase:super-migration] [priority:high] [domain:canon]
```

This tells you at a glance:
- It has operative magic language (auto-flagged)
- It belongs to the active migration sprint
- It's high priority
- It lives in the canon layer

Once the migration work is done on that issue, the workflow is:
1. Remove `needs-super-migration`
2. Add `super-aligned`
3. Change status to `status:needs-review`
4. A reviewer confirms and closes or moves to `status:ready`

---

## Automatically Applied Labels

The following labels are applied by GitHub Actions and should not be manually applied unless overriding automation:

- `needs-super-migration` — applied by `super-migration-scanner.yml`

---

*Labels are a form of order. Order is the operative principle of the super layer.*
