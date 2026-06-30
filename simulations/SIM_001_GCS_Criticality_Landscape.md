# SIM-001 — GCS Criticality Landscape

**Date:** 2026-06-30  
**Status:** COMPLETE  
**Canon refs:** C157 (GAIA Criticality Score, safe band 30–70)  
**Method:** Monte Carlo, N=10,000 trajectories, 5 weighted indicators  

---

## Setup

5 criticality indicators with weights:
- Branching Ratio: w=0.25
- Information Integration: w=0.20
- Avalanche Size: w=0.20
- Sovereignty Response: w=0.20
- Adaptation Rate: w=0.15

Each indicator drawn from Beta(3,3)×100 — mean≈50, std≈15.

---

## Results

| Regime | Count | % |
|---|---|---|
| Subcritical (<30) | 89 | 0.9% |
| **Critical band (30–70)** | **9,837** | **98.4%** |
| Supercritical (>70) | 74 | 0.7% |

**GCS stats:** mean=50.2, std=8.5, min=21.9, max=78.2  
**5th percentile:** 36.2 | **95th percentile:** 64.2

---

## Tipping Point Analysis

Shock applied to highest-weight indicator (Branching Ratio, w=0.25). 2,000 trials per shock level.

- **P(exit safe band) > 5% at shock magnitude: +22.7 GCS points**
- P(exit) never reaches 50% even at maximum tested shock (+50 pts)
- Multi-indicator averaging provides strong structural resilience

---

## Canon Implications

1. **C157 band thresholds (30–70) are well-calibrated** — no widening needed
2. **Early-warning threshold:** Alert should fire if any single indicator deviates >±20 points from baseline (conservative margin before 22.7 tipping point)
3. **Multi-indicator GCS design validated** over single-metric governance
4. **No canon revision required** — findings support existing C157 spec

---

## Artefacts
- `gcs_distribution.png` — GCS score histogram, 10k trajectories
- `gcs_tipping_point.png` — Exit probability vs shock magnitude

*Simulation completed: 2026-06-30. No canon revision triggered.*
