# SIMULATION INDEX — Master Traceability Register

**Last updated:** 2026-06-30 (Pass 3 filed)  
**Maintained by:** GAIA Development Process  
**Purpose:** Single source of truth for all simulation runs.

---

## How to Read This Index

| Column | Meaning |
|---|---|
| SIM ID | Canonical identifier |
| Topic | What the simulation is testing |
| Highest Pass | Current highest completed pass |
| Best Score | Highest score achieved across all passes |
| Target Gate | The GATE condition this SIM must satisfy |
| Status | ACTIVE / COMPLETE / BLOCKED / STUB |
| Artifact Commit | The commit SHA where artifacts are filed |

---

## Active & Completed Simulations

| SIM ID | Topic | Highest Pass | Best Score | Target Gate | Status | Artifact Commit |
|---|---|---|---|---|---|---|
| SIM_005 | Consent Ledger — Sharded Architecture | Pass 2 | — | — | COMPLETE | See repo history |
| SIM_006 | Knowledge Graph Gardening | Pass 2 | — | — | COMPLETE | See repo history |
| SIM_010 | Agent Stack Hardening | Pass 2 | — | — | COMPLETE | See repo history |
| SIM_016 | BCI Next-Gen Detector | Pass 7 | ~91% | GATE-003 Tier 2 | COMPLETE | See repo history |
| SIM_017 | Persistent Memory Architecture | Pass 1 | — | GATE-004 | ACTIVE | See repo history |
| SIM_INT_012 | Integration Simulation — Cross-Module | Pass 1 | — | GATE-004 | ACTIVE | See repo history |
| **SIM_018** | **GAIA Benchmark v2 — GATE-005 Band 2** | **Pass 3** | **86.8%** | **GATE-005 Tier 1 (≥88%)** | **ACTIVE** | **5924fba / current** |

## Stub Queue (Not Yet Active)

| SIM ID | Topic | Status |
|---|---|---|
| SIM_019 | TBD — see SIM_019_Spec_Stub.md | STUB |
| SIM_020 | TBD — see SIM_020_Spec_Stub.md | STUB |

---

## SIM_018 Pass History

| Pass | Variant | Score | Key Change | Spec File | Results File |
|---|---|---|---|---|---|
| Pass 1 | Baseline | ~79.6% | Initial run — Band 2 baseline established | `SIM_018_Spec_Stub.md` | `SIM_018_Pass1_Results.md` |
| Pass 2A | Bayes Prior Calibration | 81.3% | Prior sharpening on ambiguous tasks | `SIM_018_Pass2_Spec.md` | `SIM_018_Pass2_Results.md` |
| Pass 2B | Context Window Expansion | 83.9% | Extended retrieval window for multi-hop tasks | `SIM_018_Pass2_Spec.md` | `SIM_018_Pass2_Results.md` |
| Pass 2C | Hybrid Fusion | 84.7% | Combined Bayes + context expansion | `SIM_018_Pass2_Spec.md` | `SIM_018_Pass2_Results.md` |
| Pass 3A | Stability Verification | 84.54% mean / 0.49% std | 5-seed stability confirmed | `SIM_018_Pass3_Spec.md` | `SIM_018_Pass3_Results.md` |
| Pass 3B | Threshold Tuning | 85.3% | S3 threshold 0.55 adopted | `SIM_018_Pass3_Spec.md` | `SIM_018_Pass3_Results.md` |
| Pass 3C | 1-Layer CNN | **86.8%** | Feature extraction confirmed bottleneck | `SIM_018_Pass3_Spec.md` | `SIM_018_Pass3_Results.md` |
| Pass 4 | 2–3 Layer CNN / Transformer | — | Deep feature extraction — GATE-005 Tier 1 formal clearance | `SIM_018_Pass4_Spec.md` | — |

**Ceiling estimate:** 88–90%  
**GATE-005 Tier 1 status:** 🔓 Open (conditions met) — formal clearance pending ≥88% score  
**Next action:** Run Pass 4 per `SIM_018_Pass4_Spec.md`

---

## Traceability Standard (Effective 2026-06-30)

All future simulation work must satisfy the following before proceeding to the next pass:

1. **Pre-Run Research** — file `SIM_XXX_PassN_PreRun_Research.md` answering the four standard questions before running
2. **Results** — file `SIM_XXX_PassN_Results.md` immediately after run
3. **Bottleneck Ledger** — file `SIM_XXX_PassN_Bottleneck_Ledger.md` documenting ceiling, floor, and known limits
4. **Research Improvements** — file `SIM_XXX_PassN_Research_Improvements.md` before speccing next pass
5. **Next Pass Spec** — file `SIM_XXX_PassN+1_Spec.md` before running next pass
6. **Update this Index** — update `SIMULATION_INDEX.md` with new pass row and score
7. **Session Log** — update `docs/dev-log/YYYY-MM-DD_session.md` with decisions made

No pass may be run without steps 1 and 5 being filed first.
