# GAIA Traceability Standard

**Effective:** 2026-06-30  
**Scope:** All simulation work, canon development, and architectural decisions  
**Canonical simulation register:** `docs/simulations/SIMULATION_INDEX.md`

---

## Why Traceability Matters

GAIA is a long-running, multi-session project. Without traceability, decisions made in one session become invisible to future sessions. The cost is:

- Repeated work (re-running analyses already done)
- Lost rationale (knowing *what* was decided but not *why*)
- Broken gate logic (inability to prove a gate condition was satisfied)
- Invisible bottlenecks (not knowing what was already tried and why it failed)

Traceability means every artifact can be followed forward (what came next) and backward (what produced it).

---

## Simulation Traceability Checklist

Applies to every simulation pass. All steps must be completed in order.

### Before Running a Pass
- [ ] **Pre-Run Research filed** — `SIM_XXX_PassN_PreRun_Research.md` answers the four standard questions:
  1. What is the specific hypothesis this pass tests?
  2. What change is being made vs. the prior pass, and why?
  3. What score or result would confirm the hypothesis?
  4. What score or result would falsify it?
- [ ] **Pass Spec filed** — `SIM_XXX_PassN_Spec.md` defines methodology, parameters, and acceptance criteria
- [ ] **SIMULATION_INDEX.md** has a planned row for this pass

### After Running a Pass
- [ ] **Results filed** — `SIM_XXX_PassN_Results.md` within the same session
- [ ] **Bottleneck Ledger filed** — `SIM_XXX_PassN_Bottleneck_Ledger.md` documenting ceiling, floor, and binding constraints
- [ ] **Research Improvements filed** — `SIM_XXX_PassN_Research_Improvements.md` before speccing next pass
- [ ] **SIMULATION_INDEX.md updated** — new row added with score, commit SHA
- [ ] **Session Log updated** — `docs/dev-log/YYYY-MM-DD_session.md` records what was done and decided

---

## Architectural Decision Traceability

For any architectural decision that changes a spec, doctrine, or canon document:

- File an ADR (Architecture Decision Record) in `docs/adr/`
- Format: `ADR-NNN_short-title.md`
- Required fields: **Context**, **Decision**, **Rationale**, **Consequences**, **Alternatives Considered**

---

## Document Ownership

| Document Type | Location | Update Trigger |
|---|---|---|
| Simulation Index | `docs/simulations/SIMULATION_INDEX.md` | Every pass completion |
| Session Logs | `docs/dev-log/YYYY-MM-DD_session.md` | Every session |
| ADRs | `docs/adr/ADR-NNN_*.md` | Any architectural decision |
| Gate Conditions | `docs/simulations/SIMULATION_VALIDATION_PROTOCOL.md` | Gate definition changes only |
| This Standard | `docs/TRACEABILITY_STANDARD.md` | Process changes only |

---

## Commit SHA Policy

Every document filed must be traceable to a commit SHA. The convention is:

- File artifacts **in the same commit** whenever possible (use `push_files` for batch commits)
- Record the SHA in `SIMULATION_INDEX.md` and in the session log
- Never reference work as "done" in a session log unless the commit SHA is known
