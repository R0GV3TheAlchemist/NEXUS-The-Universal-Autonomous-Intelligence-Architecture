# Contributing to GAIA

> *"Power without process is just chaos with an audience."*
> — GAIA Canon

Welcome. GAIA is a serious engineering project with a sophisticated multi-language codebase (TypeScript, Python, Rust/Tauri) and an active architectural vision. Contributions are welcome when they follow the protocols below.

These protocols exist not to slow you down — they exist so that every piece of work has a name, a place, and a path to completion.

---

## Before You Begin

1. Read [`docs/adr/README.md`](docs/adr/README.md) — understand why decisions were made
2. Read [`docs/architecture/KNOWLEDGE_TYPE_TAXONOMY.md`](docs/architecture/KNOWLEDGE_TYPE_TAXONOMY.md) — understand the core epistemic model
3. Run the test suite: `pytest tests/` — all tests must pass before opening a PR
4. Run the minimal pipeline: `python examples/minimal_pipeline.py` — confirm your environment works
5. Search open issues before filing a new one — duplicates cost everyone time

---

## 1. The Intake Protocol — How an Idea Becomes an Issue

```
Idea → Is it already an issue? (Search first)
     → YES: Comment on the existing issue
     → NO:  File a new issue using the correct template
```

**Issue templates** (`.github/ISSUE_TEMPLATE/`):

| Template | When to use |
|---|---|
| `feature.md` | New capability or system |
| `research.md` | Exploratory / architecture work requiring investigation before code |
| `bug.md` | Something broken in existing code |
| `process.md` | Workflow, tooling, documentation, or project structure |
| `adr.md` | Architecture Decision Record — when a significant design decision is made |

**Every issue must include:**
- [ ] A one-sentence **problem statement** (what is wrong or missing right now)
- [ ] A **Definition of Done** (exact, checkable, no ambiguity)
- [ ] **Related issues** (what this blocks, what blocks this)
- [ ] **Milestone assignment** (which phase this belongs to — see [Milestone Structure](#milestone-structure))

---

## 2. The Triage Protocol — What Happens After Filing

Within 48 hours of filing, every issue must be:

- **Labeled** correctly (`enhancement`, `bug`, `architecture`, `research`, `process`)
- **Assigned to a Milestone** (see Milestone Structure below)
- **Assessed for prerequisites** — are there blocking issues that must be resolved first?
- If blocked: labeled `blocked` and the blocking issue number added to the body

If an issue has no Milestone assignment after 48 hours, it goes into `Milestone: Backlog` by default. **Nothing lives in limbo.**

---

## 3. Milestone Structure

GAIA's work is organized into 8 milestones. Issues must not begin implementation until their milestone's gate condition is met.

| Milestone | Focus | Gate |
|---|---|---|
| **M0 — Foundation & Process** | Process, ADRs, error-detection foundation | Must complete before all other milestones |
| **M1 — Core Runtime Identity** | GAIANProfile, architectId, session persistence | M0 complete |
| **M2 — Adaptive Console** | CrystalView, Orb, AlignmentIndicator adapt per profile | M1 complete |
| **M3 — Protection & Containment** | Security, shielding, stability interfaces | M1 complete |
| **M4 — Intelligence & Personalization** | Supercomputation Alignment, Provenance, RAG | M2 + M3 complete |
| **M5 — Meta Control System** | Meta Control Console, Power Containment, Sigil, Crystal Routing | M2 + M3 complete |
| **M6 — Planetary & Civilization Layer** | Governance, ecology, economy, eBPF, HAL | M1–M4 complete |
| **Backlog** | All unassigned issues — staging only | Graduate into a milestone after triage |

**Gate rules:**
1. A milestone is not "in-progress" until its gate is cleared.
2. A milestone is complete when **all** issues in it are closed and all Definitions of Done are satisfied.
3. An issue may not move forward until its Definition of Done has no unchecked items.
4. Gate blockers are named explicitly with the `blocked` label.

---

## 4. The Branch Protocol — How Code Gets Written

```
Branch naming convention:
  feature/issue-{number}-{short-description}
  fix/issue-{number}-{short-description}
  research/issue-{number}-{short-description}
  process/issue-{number}-{short-description}

Examples:
  feature/issue-756-gaian-profile-types
  fix/issue-723-runtime-context-null-crash
  process/issue-757-contributing-md
```

**Rules:**
- One branch per issue. Never combine unrelated work into a single branch.
- Branch off `main` unless the issue specifies a different base.
- Never commit directly to `main`.
- Branch names must include the issue number. No exceptions.

---

## 5. The PR Protocol — How Code Gets Reviewed

**Before opening a PR:**
- [ ] All Phase 1 prerequisites from the issue are complete
- [ ] Tests written and passing locally (`pytest tests/` for Python, ESLint + type check for TypeScript)
- [ ] No new lint errors introduced (Ruff for Python, ESLint for TypeScript)
- [ ] `tools/claim_validator.py` passes on any new claim schemas
- [ ] `knowledge_type` set on all new claims (per ADR-001)
- [ ] No simulation results written directly to real-world state
- [ ] This CONTRIBUTING.md read and followed

**PR body must include:**
- `Closes #` (links the PR to the issue — required)
- Summary of what changed and why
- Any known limitations or follow-up issues
- Screenshots/recordings for any UI changes in `src/gaian/`

**Review requirements:**
- Self-review using the PR checklist before requesting review
- For changes to `core/`, `src/gaian/`, or `docs/adr/`: explicit acknowledgment required before merge
- If architectural: ADR written, accepted, and linked in the PR description

---

## 6. The Merge Protocol — What "Done" Actually Means

A PR may be merged when:
- [ ] All checklist items in the PR body are checked
- [ ] All automated checks pass (lint, type check, tests)
- [ ] The Definition of Done from the linked issue is fully satisfied
- [ ] No `blocked` label remains on the issue
- [ ] For architectural PRs: linked ADR has status `Accepted`

**After merge:**
- Close the linked issue
- Update any parent/child issues that were waiting on this work
- If this resolves a Milestone gate blocker, note it in the Milestone description

---

## 7. The Chaos Protocol — What to Do When Work Is Uncertain

This is the section most projects omit. GAIA names it explicitly.

**When work is uncertain** (you don't know how to implement it yet):
→ File a `research` issue. Do not write code until the research issue produces an implementation plan.

**When work is blocked** (something else must happen first):
→ Label the issue `blocked`. Add the blocking issue number. Do not start the work.

**When work is volatile** (active development is destabilizing other things):
→ Apply the `volatile` label. Note what is being destabilized and why in the issue body.
→ This is not failure. This is named, tracked, and manageable.

**When work is abandoned** (it no longer makes sense):
→ Close the issue with `wont-fix` or `duplicate`. Never leave issues open that are no longer real work.

**The rule: every state of work has a name. Unnamed states become chaos.**

---

## 8. The ADR Protocol — When Architecture Must Be Documented

Every significant architectural decision needs an ADR before code is written.

**File an ADR when:**
- You are choosing between two or more viable technical approaches
- A decision will be difficult or expensive to reverse
- A decision affects more than one file, module, or language boundary
- A new pattern is being established that future code will follow

**ADR location:** `docs/adr/` for OS-layer decisions, `docs/adr/FE/` for `src/gaian/` frontend decisions.

**ADR template:** [`docs/adr/ADR-000-template.md`](docs/adr/ADR-000-template.md)

The code is allowed to prove the architecture wrong. That is not failure. That is refinement. (ADR-003)

---

## Contribution Type Reference

| Type | Protocol |
|---|---|
| Bug fix | Issue (bug template) → branch → PR with test that reproduces + fixes |
| New feature | Issue (feature template) → milestone assignment → branch → PR |
| Architecture change | Issue (research template) → ADR written + accepted → branch → PR |
| Documentation | PR directly for typos/clarity; issue first for structural changes |
| Process change | Issue (process template) → discussion → PR |
| ADR | Issue (adr template) → write ADR file → PR to `docs/adr/` |

---

## Questions

Open an issue with the `question` label. Every question is a signal that documentation is missing somewhere.

---

*Last updated: July 5, 2026*
*Governed by: Issue #757 — CONTRIBUTING.md & PR Protocol*
*Related: Issue #758 (Milestone Structure), Issue #759 (ADR for src/gaian/)*
