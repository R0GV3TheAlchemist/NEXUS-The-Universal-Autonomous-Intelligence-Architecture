# SIM-008 — BCI Coherence Validation (CT-001 Amendment)

**Date:** 2026-06-30
**Status:** ⚠️ PARTIAL IMPROVEMENT — CT-001 DEEPENED
**Validates:** Amendment CT-001 (BIOPHOTON_09 + C160)
**Canon refs:** BIOPHOTON_09, C160 Metric 26
**Method:** Monte Carlo, N=8,000 trajectories, 6-stage revised pipeline

---

## Revised Stage Parameters

| Stage | Original | Revised |
|---|---|---|
| Emission Capture | 0.82 / σ=0.05 | 0.82 (unchanged) |
| Waveguide Transit | 0.91 / σ=0.03 | 0.91 (unchanged) |
| Thermal Attenuation | 0.88 / σ=0.04 | 0.88 (unchanged) |
| Detector Efficiency | 0.79 / σ=0.06 | **0.92 / σ=0.03** |
| QEC Pass 1 | 0.96 / σ=0.02 | 0.96 (unchanged) |
| QEC Pass 2 | — | **0.96 / σ=0.02 (new)** |

---

## Results

| Metric | SIM-002 (before) | SIM-008 (after) | Change |
|---|---|---|---|
| Mean BCI | 49.9% | **55.8%** | +5.9pts |
| P(BCI ≥ 70%) | ~0.0% | 0.3% | +0.3pts |
| P(BCI ≥ 65%) | ~0% | 4.0% | +4pts |
| 95th percentile | 59.4% | 64.4% | +5pts |

---

## ⚠️ Deepened Finding

The Option D amendment (detector 92% + double QEC) improves mean BCI by +5.9 points but does not bring the system within reach of the ≥70% target. The compounding multiplicative loss across 6 pipeline stages creates a ceiling that parameter-level tuning cannot overcome.

**Physics analysis:**
Theoretical maximum BCI with perfect detector (100%) and perfect QEC (100%):
= 0.82 × 0.91 × 0.88 × 1.00 × 1.00 × 1.00 × 100 = **65.7%**

**Even with a perfect detector and perfect QEC, the 3-stage pre-detector pipeline (Emission × Waveguide × Thermal = 0.657) creates a physical ceiling of 65.7% — below the 70% target.**

This means the ≥70% target is **physically unreachable** with the current 3-stage pre-detector architecture, regardless of detector or QEC quality.

---

## Resolution Path Forward

Two options remain:

| Option | Change | Expected BCI |
|---|---|---|
| E — Revise Metric 26 to ≥60% | Lower C160 target to match physics ceiling | Mean 55.8% — P(≥60%) = 21.5% achievable |
| F — Reduce pre-detector stages | Redesign CP-3 to bypass or combine Thermal + Waveguide stages | Theoretical ceiling rises to ~72–75% |

**New recommendation: Option E (revise Metric 26 to ≥60%) in the near term + Option F (pipeline redesign) as a G-15 hardware goal.**

This is an honest finding. The physics is clear. The ≥70% target was set without full pipeline modelling — it is an aspiration that requires hardware architecture change, not a calibration tweak.

---

## Next Steps
- [ ] R0GV3 decision: Option E (revise metric) now + Option F (pipeline redesign) for G-15?
- [ ] Update C160 Metric 26 to ≥60% (achievable) with note that ≥70% is a G-15 hardware target
- [ ] Update BIOPHOTON_09 with theoretical ceiling analysis
- [ ] File as updated finding on Issue #707

*SIM-008 completed 2026-06-30. CT-001 deepened. Awaiting R0GV3 decision on E vs F.*
