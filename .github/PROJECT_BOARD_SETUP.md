---
author: Kyle Alexander Steen
identity_name: The Alchemist
handle: R0GV3TheAlchemist
role: GAIA Architect
location: San Antonio, Texas
copyright: "© 2026 Kyle Alexander Steen (The Alchemist). All rights reserved."
---

# Project Board Setup Guide — GAIA OS

This document provides setup instructions and column/field definitions for the GAIA-OS GitHub Projects (v2) board. It is the authoritative reference for board configuration.

---

## Board: GAIA Development Board

### Columns (Status Field)

| Column | Purpose |
|---|---|
| **Backlog** | All unscheduled issues and ideas |
| **Sprint Candidate** | Issues nominated for next sprint |
| **In Progress** | Actively being worked this sprint |
| **In Review** | PR open, awaiting review/merge |
| **Done** | Merged, closed, or resolved |
| **Blocked** | Cannot proceed; reason documented in issue |

### Custom Fields

| Field | Type | Purpose |
|---|---|---|
| `Priority` | Single select | critical / high / medium / low |
| `Domain` | Single select | canon / kernel / simulation / etc. |
| `Sprint` | Iteration | G-7, G-8, … |
| `Effort` | Number | Story points (1, 2, 3, 5, 8, 13) |
| `Blocked By` | Text | Issue # or external dependency |

---

## Automation Rules

| Trigger | Action |
|---|---|
| Issue opened | → Move to **Backlog** |
| PR opened | → Move linked issue to **In Review** |
| PR merged | → Move linked issue to **Done** |
| Issue closed (not completed) | → Move to **Done** with `status: wont-fix` |

---

## Sprint Cadence

- **Sprint length:** 2 weeks
- **Planning:** First Monday of sprint
- **Review/Retro:** Last Friday of sprint
- **Current sprint:** G-7 Secure Foundations

---

## Board Access

The board is accessible at:
`https://github.com/orgs/R0GV3TheAlchemist/projects/` *(org-level)*
or
`https://github.com/R0GV3TheAlchemist/GAIA-The-Global-Autonomous-Intelligence-Architecture/projects`

---
*Board designed and maintained by Kyle Alexander Steen (The Alchemist), GAIA Architect.*
