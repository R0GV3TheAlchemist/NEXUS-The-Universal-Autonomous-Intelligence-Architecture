# ADR-003 — Architecture Evolution Principle

**Status:** Accepted
**Date:** 2026-06-30
**Author:** GAIA Core

---

## Problem

Large architectural systems tend to calcify: decisions made early become load-bearing
without anyone noticing, and the cost of correction compounds over time.
GAIA must be designed to evolve as implementation reveals new constraints.

## Decision

We adopt the following principle formally:

> **The code is allowed to prove the architecture wrong.**
> That is not failure. That is refinement.
> An ADR that is superseded means the system learned something.

Practically, this means:
1. Every architectural decision is recorded in an ADR with status tracking
2. When implementation reveals a better approach, a new ADR supersedes the old one — the old one is not deleted
3. No layer is considered "locked" until it has passed integration tests under real-world-scale data
4. Benchmark results (`benchmarks/`) are the ground truth for performance claims
5. The architecture document is a living document, not a specification to defend

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Treat initial design as specification | Creates institutional pressure to hide implementation failures rather than fix them |
| No formal ADR process | Decisions are re-litigated endlessly; institutional memory is lost |

## Consequences

**Gains:**
- Architecture improves over time instead of constraining it
- Contributors can propose changes through the ADR process without implicit conflict
- Superseded decisions remain visible — future contributors understand why changes were made

**Losses / Trade-offs:**
- Requires discipline: every significant change needs an ADR, not just a commit
- ADR backlog can grow if not maintained

**Follow-on work:**
- Enforce ADR review in pull request template
- Add ADR index to docs/adr/README.md
