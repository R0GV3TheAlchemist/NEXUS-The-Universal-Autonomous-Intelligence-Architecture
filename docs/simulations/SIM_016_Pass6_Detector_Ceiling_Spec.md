# SIM-016 Pass 6 — Detector Ceiling
## SPAD Parallelised TCSPC vs SNSPD Theoretical Maximum

**Pass Classification:** Pass 6 — Ceiling Characterisation
**Simulation number:** SIM-016
**Date filed:** 2026-06-30
**Drive target:** ≥80% BCI
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Pass Context

**Progression:** 49.7% → 67.3% → 68.0% → 68.4% → 69.4% → 77.0% (P5) → **Pass 6 target: ≥80%**

**The detector is now the dominant constraint.** Upstream is near ceiling. QEC is near ceiling. The 3.0-point gap to 80% is almost entirely the detector.

**Two variants tested in parallel:**
- **6A: Advanced SPAD + parallelised TCSPC** — feasible, room temperature, BCI-deployable
- **6B: SNSPD theoretical ceiling** — cryogenic, establishes the physics maximum

---

## Parameters

### Upstream Sub-Stages — Held from Pass 5

| Sub-stage | Mean | Std |
|---|---|---|
| E1: Aperture geometry | 97.5% | 1.5% |
| E2: Adaptive capture | 97.9% | 1.3% |
| W1: Coupling interface | 98.0% | 1.5% |
| W2: Propagation | 97.5% | 0.8% |
| T1: Depth attenuation | 95.0% | 2.0% |
| T2: Temp scattering | 97.0% | 1.3% |

### Detector — Variant A (Advanced SPAD + Parallelised TCSPC)

| Parameter | Value |
|---|---|
| Raw efficiency | 94% |
| FN rate (parallelised TCSPC, 8 channels) | 0.30% |
| Effective efficiency | ~93.7% |
| Operating temperature | 300K |
| BCI deployable | Yes |

### Detector — Variant B (SNSPD Theoretical Ceiling)

| Parameter | Value |
|---|---|
| Raw efficiency | 98% |
| FN rate (ps jitter, negligible pile-up) | 0.05% |
| Effective efficiency | ~97.9% |
| Operating temperature | <3K (cryogenic) |
| BCI deployable | No (current tech) |

### QEC — Held

| Stage | Value |
|---|---|
| QEC | 99.8% ±0.5% |

---

## Success Conditions

| Condition | Variant A | Variant B |
|---|---|---|
| Mean BCI ≥80% | Required | Required |
| Physics ceiling characterised | — | Yes |
| Deployability assessment | Room-temp BCI | Cryogenic constraint noted |

## Failure Conditions

| Result | Meaning | Action |
|---|---|---|
| 6A BCI <79% | SPAD parallelisation insufficient | Evaluate intermediate SPAD advances |
| 6A BCI ≥80% | Drive target met with deployable tech | Canon amendment + close SIM-016 |
| 6B BCI <82% | Physics ceiling lower than projected | Review upstream model for over-optimism |

---

## Pre-Run Research Questions

1. Does 8-channel parallelised TCSPC reduce pile-up residual below 0.1% at 300 kcps?
2. Does Variant A cross 80%?
3. What is the SNSPD theoretical ceiling (6B)?
4. Is there a fundamental physics limit below 90% BCI?
5. Can better upstream signal reduce the need for SNSPD-grade detector efficiency?

---

*Filed 2026-06-30. G-15 Tier 1. Detector ceiling. Two variants. Drive target 80%. 🌿*
