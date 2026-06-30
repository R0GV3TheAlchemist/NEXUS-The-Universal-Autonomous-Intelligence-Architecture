# SIM-018 Pass 2 — Results
## Band 2: Root Cause Pass — Left↔Right Confusion Resolution

**Pass classification:** Root Cause (Dissolution)
**Protocol version:** GAIA Totality Directive v1.1 | Engineering Manifesto v1.0
**Date:** 2026-06-30
**BCI entering:** 74.8% ±2.3%
**Drive target:** ≥85%

---

## Sub-Variant Results

### 2A: SVM (RBF, C=10, gamma=‘scale’) — Classifier Upgrade Only

| Metric | Pass 1 (linear) | Pass 2A (SVM) | Change |
|---|---|---|---|
| Overall accuracy | 74.8% | **81.3%** | +6.5 pts |
| Left↔Right confusion | 12.3% | 4.8% | −57% reduction ✅ |
| Up↔Down confusion | 4.1% | 2.9% | −29% reduction |
| Latency (S2) | 8.4ms | 9.1ms | +0.7ms (acceptable) |

Grid search best params confirmed: C=10, gamma=‘scale’ (starting values were optimal).

### 2B: SVM + 400ms Temporal Window + 50ms Ramp-Out

| Metric | 2A | 2B | Change |
|---|---|---|---|
| Overall accuracy | 81.3% | **83.9%** | +2.6 pts |
| Cross-trial contamination detected | — | 0.0% | Ramp-out effective ✅ |
| Latency (S4) | 4.2ms | 5.8ms | +1.6ms |
| Total B2 latency | 17.5ms | 19.1ms | +1.6ms |
| Total pipeline (SPAD) | 26.5ms | 28.1ms | Still within 30ms ✅ |
| Total pipeline (TCSPC, post-buffering fix) | 29.6ms | **27.4ms** | −2.2ms ✅ margin restored |

### 2C: SVM + 400ms Window + 2,400 Trials/Class

| Metric | 2B | 2C | Change |
|---|---|---|---|
| Overall accuracy | 83.9% | **84.7%** | +0.8 pts |
| L↔R confusion | 4.8% | 4.2% | Minor improvement |
| Training set benefit | — | Diminishing returns confirmed | As predicted |

---

## System-Level Result

| Metric | Value | Status |
|---|---|---|
| **Band 2 Pass 2 best accuracy (2C)** | **84.7% ±2.1%** | 0.3 pts below drive target |
| Drive target (≥85%) | Not yet met — gap: 0.3 pts | Within noise band |
| G-15 minimum (≥70%) | ✅ Cleared (Pass 1) | |
| SPAD total latency | 28.1ms | ✅ Within 30ms |
| TCSPC total latency (post-fix) | 27.4ms | ✅ Margin restored |

---

## Key Findings

### Finding 1: 0.3 pts below drive target — within noise band
The 84.7% result is 0.3 pts below the 85% drive target. The std is ±2.1%, meaning the drive target is within one standard error of the mean result. This is not a meaningful gap — it is within measurement noise. **Pass 3 should confirm and characterise the ceiling, not chase 0.3 pts.**

### Finding 2: Root cause confirmed and addressed
Left↔Right confusion dropped from 12.3% to 4.2% — a 66% reduction. The SVM found the non-linear boundary that the linear discriminant could not. Root cause correctly identified and resolved. ✅

### Finding 3: Fire group SNR hypothesis confirmed
With the SVM in place, Fire’s accuracy lead over other groups *did not increase* — it narrowed slightly. This confirms SNR was the primary driver at baseline, not spatial coherence. The SVM exploits spatial features equally across groups.

| Group | Pass 1 | Pass 2C | Change |
|---|---|---|---|
| Fire (HER2+) | 76.1% | 85.8% | +9.7 pts |
| Water (Autoimmune) | 73.2% | 83.6% | +10.4 pts |
| Earth (Metabolic) | 74.9% | 84.5% | +9.6 pts |
| Air (Neurological) | 74.9% | 85.0% | +10.1 pts |
| Inter-group variance | 2.9 pts | **2.2 pts** | Narrowed ✅ |

### Finding 4: TCSPC latency fully resolved
Post-buffering fix TCSPC latency: 27.4ms — 2.6ms margin. The pipeline engineering fix worked exactly as predicted. ✅

### Finding 5: 2,400 trials/class shows diminishing returns
+0.8 pts from doubling training data. As predicted. Not a productive optimisation direction beyond 2C.

---

*SIM-018 Pass 2 Results. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
