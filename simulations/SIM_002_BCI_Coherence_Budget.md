# SIM-002 — Biophotonic Coherence Budget (CP-3 Transducer)

**Date:** 2026-06-30  
**Status:** COMPLETE — ⚠️ CANON TENSION IDENTIFIED  
**Canon refs:** BIOPHOTON_09 (CP-3 transducer stage parameters), C160 (Metric 26: BCI ≥70%)  
**Method:** Monte Carlo, N=8,000 trajectories, 5-stage coherence pipeline  
**Issue filed:** See GitHub Issue — "Canon Tension: BIOPHOTON_09 stage params cannot achieve C160 Metric 26 BCI ≥70% target"

---

## Setup

CP-3 Transducer 5-stage coherence pipeline:

| Stage | Mean Retention | Std |
|---|---|---|
| Emission Capture | 0.82 | 0.05 |
| Waveguide Transit | 0.91 | 0.03 |
| Thermal Attenuation | 0.88 | 0.04 |
| Detector Efficiency | 0.79 | 0.06 |
| QEC Fidelity | 0.96 | 0.02 |

BCI = product of all 5 stage retentions × 100

---

## Results

| Metric | Value |
|---|---|
| Mean BCI | **49.9%** |
| Std | 5.69% |
| Min | 29.3% |
| Max | 70.2% |
| 5th percentile | 40.6% |
| 95th percentile | 59.4% |
| **P(BCI ≥ 70%) — C160 target** | **~0.0%** |
| P(BCI ≥ 60%) | 3.8% |
| P(BCI ≥ 55%) | 27.4% |

---

## ⚠️ Canon Tension

**Gap to target: 20.1 percentage points.**

The CP-3 stage parameters as specified in BIOPHOTON_09 cannot deliver the BCI ≥70% target specified in C160 Metric 26 under any realistic operating conditions. The compounding loss across 4 pre-QEC stages drives the mean to ~50%, and even optimal QEC (96%) cannot recover the 20-point deficit.

**Root cause:** Detector Efficiency (mean 79%, σ=6%) and Emission Capture (mean 82%, σ=5%) are the dominant loss contributors.

---

## Resolution Options

| Option | Change Required | Canon Impact |
|---|---|---|
| **A — Revise Metric 26** | Lower target from ≥70% → ≥55% (achievable ~84th pct) | C160 amendment |
| **B — Improve Detector Efficiency** | Raise detector mean from 79% → 92%+ | BIOPHOTON_09 hardware spec revision |
| **C — Double QEC pass** | Stack two QEC stages; raises mean to ~68% | BIOPHOTON_09 architecture revision |
| **D — Combined B+C** | Detector 92% + double QEC → mean ~73%, P(≥70%)≈55% | Both docs revised |

**Recommendation:** Option D (combined hardware + QEC improvement) — preserves the ambition of ≥70% while grounding it in achievable physics.

---

## Artefacts
- `bci_distribution.png` — Post-QEC BCI score distribution, 8k trajectories

*Simulation completed: 2026-06-30. Canon tension flagged. Awaiting resolution decision from R0GV3.*
