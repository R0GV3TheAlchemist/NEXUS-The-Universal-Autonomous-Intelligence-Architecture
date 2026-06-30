# SIM-016 Pass 4 Results — Upstream Optical Path Decoupling

**Pass Classification:** Pass 4 — Isolation & Decoupling
**Status:** COMPLETE ✅ — 69.4% — 0.6 pts below 70% minimum — DOMINANT SUB-STAGES IDENTIFIED
**Date run:** 2026-06-30 | **Trials:** N=5,000/group (20,000 total)
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Summary

Upstream stages split into 6 sub-stages. BCI improved from 68.4% (Pass 3) to 69.4% — an increase driven entirely by more accurate sub-stage modelling revealing higher baseline efficiencies when coupling-interface and propagation losses are measured independently. The system is now 0.6 points below the 70% G-15 minimum. Two sub-stages dominate: T1 (depth attenuation, 8.30 log-pts) and E1 (aperture geometry, 6.20 log-pts). W1 (coupling interface, 5.13 log-pts) is third. T1–W2 correlation rho=0.35 confirmed — joint optimisation required for these two.

---

## Key Results

| Metric | Pass 3 | Pass 4 | Target |
|---|---|---|---|
| Overall Mean BCI | 68.4% | **69.4%** | ≥70% (min) / ≥80% (drive) |
| Earth | 68.4% ±3.6% | 69.5% ±2.6% | ≥70% |
| Water | 68.4% ±4.7% | 69.4% ±3.4% | ≥70% |
| Fire | 68.5% ±5.1% | 69.4% ±3.7% | ≥70% |
| Air | 68.3% ±5.0% | 69.5% ±3.7% | ≥70% |
| Gap to 70% | 1.6 pts | **0.6 pts** | 0 |
| Gap to 80% | 11.6 pts | **10.6 pts** | 0 |

---

## Sub-Stage Bottleneck Ledger — Pass 4 (Definitive)

| Sub-stage | Physical mechanism | Mean | Std | Log-loss (pts) | Rank |
|---|---|---|---|---|---|
| T1: Depth attenuation | Path-length μs/μa in neural tissue | 0.920 | ±0.027 | **8.30** | #1 — Dominant |
| E1: Aperture geometry | Solid angle, electrode proximity | 0.940 | ±0.018 | **6.20** | #2 |
| W1: Coupling interface | Fresnel, taper, index mismatch | 0.950 | ±0.018 | **5.13** | #3 |
| W2: Propagation | In-guide scatter, sidewall | 0.970 | ±0.009 | 3.04 | #4 |
| T2: Temp scattering | State-dependent μs drift | 0.970 | ±0.013 | 3.06 | #5 |
| E2: Adaptive capture | Per-subject aperture optimisation | 0.979 | ±0.013 | 2.09 | #6 |
| **Detector (held)** | TCSPC post-FN | 0.919 | held | 8.45 | Reference |

**Top 3 recovery targets for Pass 5: T1, E1, W1**

---

## Pre-Run Research Questions — Answered

1. **Waveguide: coupling interface vs propagation split?** Confirmed separable. W1 (coupling) contributes 5.13 log-pts; W2 (propagation) 3.04 log-pts. Interface is the dominant waveguide loss. ✅
2. **Depth-dependent attenuation profile?** T1 is the dominant upstream sub-stage at 8.30 log-pts. Subject-specific and placement-depth dependent (std ±0.027 — highest variance of all sub-stages). ✅
3. **Adaptive aperture effect?** E2 at 97.9% mean and only 2.09 log-pts — already near ceiling for its mechanism. Pass 5 focus is E1 (geometry/proximity), not E2. ✅
4. **T1–W2 correlation?** rho=0.35 confirmed. Longer path in tissue increases both depth attenuation and propagation scatter. Joint optimisation required. ✅
5. **Dominant loss after decoupling?** T1 depth attenuation (8.30 log-pts). Determines Pass 5 primary target. ✅

---

## Pass 4 Success Criteria — Assessment

| Criterion | Target | Result | Status |
|---|---|---|---|
| All sub-stages characterised independently | Yes | Yes | ✅ |
| Dominant loss sub-stage identified | Yes | T1 depth (8.30 pts) | ✅ |
| T1–W2 correlation tested | Yes | rho=0.35 confirmed | ✅ |
| Mean BCI ≥70% | ≥70% | 69.4% | ❌ 0.6 pts short |
| Variance reduced across groups | Yes | ±3.4% overall (vs ±4.6% P3) | ✅ |

**Pass 4 status: HIGHLY INFORMATIVE ✅ — optimisation targets locked. Pass 5 is now a precision strike.**

---

*Run: 2026-06-30. G-15 Tier 1. Upstream decoupling complete. T1+E1+W1 are the targets. 🌿*
