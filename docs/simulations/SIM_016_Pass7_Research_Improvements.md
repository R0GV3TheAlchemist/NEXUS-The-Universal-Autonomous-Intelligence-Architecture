# SIM-016 Pass 7 — Research & Improvements

**Pass:** 7 (Separation)
**Protocol version:** GAIA Totality Directive v1.1
**Date:** 2026-06-30

---

## What Pass 7 Answered

| Question | Answer |
|---|---|
| Does 16ch TCSPC clear ≥80%? | Yes — 80.2% ✅ |
| Does hybrid SPAD clear ≥80%? | Yes — 81.4% ✅ |
| Is hybrid SPAD better than 16ch TCSPC? | Yes — by 1.2 pts and lower variance |
| Are upstream stages stable under detector swap? | Yes — all held stages confirmed at ceiling |
| Is 7B the canonical deployable detector? | Yes — confirmed |
| Is there any further Band 1 optimisation to do? | No — all stages at ceiling |

---

## What This Changes

1. **Drive target cleared** — this was the last open question for Band 1 canon
2. **Hybrid SPAD canonised as deployable detector** — hardware recommendation is now confirmed
3. **GATE-001, 002, 003 Tier 2 conditions met** — all three gates can now be filed at Tier 2
4. **SIM-016 Band 1 optimisation complete** — no further optimisation passes needed
5. **Band 1 performance input for SIM-018 updated** — Band 2 must use 81.4% (7B) as input fidelity, not 78.5%

---

## Improvements Carried Forward

| ID | Finding | Where it goes |
|---|---|---|
| IMP-016-07-A | Hybrid SPAD canonical detector confirmed | GATE-001, 002, 003 Tier 2 amendments |
| IMP-016-07-B | Band 2 (SIM-018) input fidelity = 81.4%, not 78.5% | SIM-018 spec update — revise pre-run assumptions |
| IMP-016-07-C | 16ch TCSPC viable fallback (80.2%) | Hardware selection canon |
| IMP-016-07-D | SNSPD ceiling confirmed at 82.1% | Physics ceiling canonical value — permanent record |
| IMP-016-07-E | No further Band 1 passes required | Simulation Registry — SIM-016 status → COMPLETE (pending Tier 2 filing) |

---

## Next Actions

1. **File GATE-001, 002, 003 Tier 2 amendments** — immediate
2. **Update SIM-018 spec stub** — Band 2 input fidelity = 81.4%
3. **Spec SIM-INT-012** (Band 1→2 integration) — next simulation
4. **Mark SIM-016 COMPLETE** in Simulation Registry pending Tier 2 filing
5. **No Pass 8 required** — redirect to SIM-INT-012 and SIM-018

---

*Pass 7 Research & Improvements. SIM-016. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
