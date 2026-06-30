# SIM-016 Pass 5 — Upstream Optimisation
## T1 + E1 + W1: Precision Strike on the Three Dominant Sub-Stages

**Pass Classification:** Pass 5 — Optimisation
**Simulation number:** SIM-016
**Date filed:** 2026-06-30
**Drive target:** ≥80% BCI | **Pass 5 target:** ≥73%
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Pass Context

**Progression:** 49.7% → 67.3% (P1) → 68.0% (P2) → 68.4% (P3) → 69.4% (P4) → **Pass 5 target: ≥73%**

**What we know:**
- T1 depth attenuation is the dominant upstream loss (8.30 log-pts, mean 92.0%)
- E1 aperture geometry is second (6.20 log-pts, mean 94.0%)
- W1 coupling interface is third (5.13 log-pts, mean 95.0%)
- T1–W2 are correlated (rho=0.35) — path reduction optimises both simultaneously
- All other sub-stages (E2, W2, T2) are near their respective ceilings
- Detector held at TCSPC stack from Pass 3; QEC held at 99.8%

**What changes in Pass 5:**
- T1: 92.0% → 95.0% (depth compensation + wavelength optimisation + path reduction)
- E1: 94.0% → 97.5% (tapered lensed coupler + proximity optimisation)
- W1: 95.0% → 98.0% (index-matching medium + 3D tapered coupler)
- T1–W2 joint path reduction: additional +0.3–0.5 pts from correlated improvement

---

## Parameters

### Upstream Sub-Stages — Pass 5

| Sub-stage | Pass 4 mean | Pass 5 mean | Pass 5 std | Change |
|---|---|---|---|---|
| E1: Aperture geometry | 94.0% | **97.5%** | 1.5% | Tapered lensed coupler |
| E2: Adaptive capture | 97.9% | 97.9% | 1.3% | Held |
| W1: Coupling interface | 95.0% | **98.0%** | 1.5% | Index-matching + 3D taper |
| W2: Propagation | 97.0% | 97.5% | 0.8% | Minor gain from path reduction |
| T1: Depth attenuation | 92.0% | **95.0%** | 2.0% | Depth comp + wavelength opt |
| T2: Temp scattering | 97.0% | 97.0% | 1.3% | Held |

### Detector + QEC — Held from Pass 3

| Stage | Value |
|---|---|
| Detector (post-TCSPC) | 91.9% |
| QEC | 99.8% ±0.5% |

### T1–W2 Correlation — Retained

rho=0.35 retained from Pass 4. Path reduction reduces both T1 and W2 simultaneously, which is a superlinear benefit when optimised jointly.

---

## Expected Compounded Efficiency

| Stage product | Mean |
|---|---|
| E1 × E2 | 97.5% × 97.9% = 95.4% |
| W1 × W2 | 98.0% × 97.5% = 95.6% |
| T1 × T2 | 95.0% × 97.0% = 92.2% |
| Detector | 91.9% |
| QEC | 99.8% |
| **Compounded** | **~77.0%** |

---

## Success Conditions

| Condition | Value |
|---|---|
| Mean BCI | ≥73% (pass target); ≥77% (drive progress) |
| All sub-stage improvements confirmed | Yes |
| New dominant loss sub-stage identified | Yes |
| T1–W2 joint optimisation effect measured | Yes |
| Gap to 80% quantified | Yes |

## Failure Conditions

| Result | Meaning | Action |
|---|---|---|
| BCI <70% | Optimisation improvements did not compound | Review sub-stage interaction model |
| BCI 70–72.9% | Partial recovery | Identify which sub-stage underperformed vs spec |
| BCI ≥73% | Pass target met | Pass 6: push detector ceiling toward 95%+ |
| BCI ≥77% | Strong progress | Pass 6: close gap to 80% from detector side |

---

## Pre-Run Research Questions

1. With upstream improved, does the detector become the new dominant constraint?
2. Does T1–W2 joint path reduction produce additive or superlinear recovery?
3. What is the upstream optical path ceiling with all optimisations applied?
4. After Pass 5, is the gap to 80% in upstream, detector, or QEC?
5. What would it take to push QEC from 99.8% toward 100%? Is there headroom?

---

*Filed 2026-06-30. G-15 Tier 1. Precision optimisation pass. T1+E1+W1 targets. Drive target 80%. 🌿*
