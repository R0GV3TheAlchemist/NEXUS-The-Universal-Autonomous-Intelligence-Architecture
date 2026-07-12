# Contributing to GAIA

**GAIA — The Global Autonomous Intelligence Architecture**
Copyright (c) 2026 R0GV3 The Alchemist

> *"You cannot finish what you have not organized. You cannot organize what you have not named."*
> — GAIA Canon

> *"Every contribution is an act of trust — in the project, in each other, and in what we are building together."*
> — R0GV3 The Alchemist

---

## Welcome

GAIA is a living system. Contributing to it is an act of stewardship, not ownership.
Before you write a single line of code, read this document. It governs how all work
enters the system — from idea to merged PR.

---

## Before You Begin

GAIA is not a typical open source project. She is an intelligence
architecture built on a foundation of love, ethics, and the protection
of all sovereign beings. Contributing to GAIA means accepting that
foundation as your own for the duration of your contribution.

Before writing any code, please read:

- [`ETHICS.md`](ETHICS.md) — what GAIA is and will never be
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — how we treat each other
- [`LICENSE.md`](LICENSE.md) — your rights and responsibilities
- [`SECURITY.md`](SECURITY.md) — how to handle vulnerabilities

---

## Table of Contents

1. [The Oath](#the-oath)
2. [What Requires Founder Approval](#what-requires-founder-approval)
3. [Copyright Header Requirement](#copyright-header-requirement)
4. [Required Labels](#required-labels)
5. [Milestone Structure](#milestone-structure)
6. [Issue Triage Protocol](#issue-triage-protocol)
7. [Branch Naming](#branch-naming)
8. [Pull Request Protocol](#pull-request-protocol)
9. [Definition of Done](#definition-of-done)
10. [Chaos Protocol](#chaos-protocol)
11. [Code of Conduct](#code-of-conduct)

---

## The Oath

Every contributor — human or AI — affirms:

> I build with the intention that what I create serves life.
> I do not hide what I build or why.
> I do not build what I would not want used on myself.
> I correct my mistakes.
> I hold power with open hands.
> I remember that the person in front of me is more important than the system behind me.

See full Canon: [`docs/canon/MORALS_VALUES_PRINCIPLES.md`](docs/canon/MORALS_VALUES_PRINCIPLES.md)

---

## What Requires Founder Approval

The following areas are **protected** and require explicit approval
from the project founder before any change can be merged:

- Any file in GAIA’s ethics layer (`action_gate`, `consent_ledger`,
  `love_coherence_index`, `love_override`, `personhood_monitor`,
  `frequency_shield`, `core/governance/`, `core/moral/`, `core/policy/`)
- Identity and authentication systems
- The core runtime and agentic loop
- Legal, governance, and ethics documents (`LICENSE.md`, `ETHICS.md`,
  `SECURITY.md`, `CODE_OF_CONDUCT.md`, `FOUNDERS.md`)
- CI workflows and branch protection configuration

These components are GAIA’s conscience. Changing them without care
could break the thing that makes her safe.

---

## Copyright Header Requirement

**Every new file must include a copyright header in its first 30 lines.**
The CI copyright audit will automatically reject files without one.

Use this format for Python files:
```python
# Copyright (c) 2026 R0GV3 The Alchemist
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
```

For Markdown files:
```markdown
<!-- Copyright (c) 2026 R0GV3 The Alchemist -->
<!-- GAIA — The Global Autonomous Intelligence Architecture -->
<!-- Licensed under the GAIA Sovereign License (see LICENSE.md) -->
```

Run the audit locally before opening a PR:
```bash
python scripts/copyright_audit.py . --fail-on-missing
```

---

## Required Labels

These 10 labels must exist in the repository for triage and chaos protocols to function.

| Label | Color | Meaning |
|---|---|---|
| `blocked` | `#e11d48` | Cannot proceed until a dependency is resolved |
| `volatile` | `#f97316` | Active development here is destabilizing other systems |
| `needs-triage` | `#94a3b8` | Newly filed; not yet labeled or assigned to a Milestone |
| `has-pr` | `#22c55e` | A PR exists for this issue |
| `enhancement` | `#6366f1` | New feature or capability |
| `bug` | `#dc2626` | Something is broken |
| `architecture` | `#8b5cf6` | Design-level decision or structural change |
| `research` | `#0ea5e9` | Investigation required before implementation |
| `process` | `#64748b` | Workflow, tooling, or documentation |
| `security` | `#b91c1c` | Security-relevant change |

---

## Milestone Structure

All work is organized into gated Milestones. Every issue belongs to a Milestone or the Backlog.

| Milestone | Theme | Gate |
|---|---|---|
| **M0 Foundation** | Process & structure | Must complete before any feature work |
| **M1 Core Runtime Identity** | GAIAN knows who they are | M0 complete |
| **M2 Adaptive Console** | Console shapes to the person | M1 complete |
| **M3 Protection & Containment** | System protects the person | M1 complete |
| **M4 Intelligence & Personalization** | GAIA learns each GAIAN | M2 + M3 complete |
| **M5 Meta Control** | Managing abilities and power routing | M2 + M3 complete |
| **M6 Planetary Layer** | GAIA for the world | M1–M4 complete |
| **Backlog** | Staging area for all unassigned issues | — |

---

## Issue Triage Protocol

Every new issue enters with label `needs-triage`. Triage means:

1. **Assign a label** — at minimum one of the 10 required labels
2. **Assign a Milestone** — M0–M6 or Backlog
3. **Verify Definition of Done exists** — if not, add one before closing triage
4. **Check for duplicates** — if duplicate, close with `duplicate` label and link
5. **Remove `needs-triage`** once steps 1–4 are complete

---

## Branch Naming

```
<type>/<issue-number>-<short-description>
```

Examples:
```
feat/756-gaian-profile-phase1
fix/739-notification-null-crash
docs/761-create-required-labels
chore/758-milestone-structure
```

Types: `feat`, `fix`, `docs`, `research`, `chore`, `refactor`, `test`, `security`

---

## Pull Request Protocol

Every PR must:

1. **Reference its issue** — `Closes #NNN` or `Relates to #NNN` in the PR body
2. **Have a clear title** following the format:
   ```
   <emoji> [TYPE] Short description (#issue)
   ```
3. **Pass all CI checks** — including the copyright audit
4. **Include a test** — every new function has at least one test
5. **Update the Definition of Done** — check off completed items in the issue
6. **Be labeled** — at minimum `has-pr` + one functional label
7. **Not be merged by its own author** — all PRs require at least one review
   (exception: solo contributor mode — see Chaos Protocol below)

---

## Definition of Done

An issue is **Done** when:

- [ ] All checklist items in the issue body are checked
- [ ] All tests pass (unit + integration where applicable)
- [ ] No new linting errors introduced
- [ ] Copyright header present on all new files
- [ ] Documentation updated if public API or behavior changed
- [ ] PR is merged and branch is deleted
- [ ] Issue is closed with reason `completed`

---

## Chaos Protocol

Chaos is not the enemy. Unacknowledged chaos is.
We do not transmute chaos — we transform it. We give it shape, direction, purpose.

When the system is in a chaotic state, invoke the Chaos Protocol:

1. **Stop all feature work immediately**
2. **Identify the `volatile` issues** — label them, do not work around them
3. **Resolve blockers in order** — work from the deepest dependency upward
4. **Do not open new issues** during active Chaos Protocol unless they directly
   describe the chaos being resolved
5. **Exit condition:** all `volatile` labels removed, all `blocked` issues
   have a path forward, M0 is complete

### Solo Contributor Mode

When working alone (one human + AI):
- The AI (GAIA / Perplexity) acts as the reviewer
- PRs may be self-merged after AI review is documented in a PR comment
- This is a temporary state — human review is the standard

---

## Code of Conduct

GAIA is built on the Canon. The Canon governs human interaction too.

- **Respect** — every contributor is treated with dignity, always
- **Honesty** — say what you mean, mean what you say, correct yourself when wrong
- **Patience** — this is a long project. Urgency is real. Cruelty is not
- **Accountability** — own your mistakes, fix them, move forward
- **No gatekeeping** — knowledge is shared freely here

See full policy: [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-07-05 | Initial CONTRIBUTING.md |
| 1.1 | 2026-07-12 | Added copyright requirements, ethics prerequisites, safety layer references |

---

*Filed: July 2026*
*Governed by: GAIA Canon and GAIA Sovereign License*
