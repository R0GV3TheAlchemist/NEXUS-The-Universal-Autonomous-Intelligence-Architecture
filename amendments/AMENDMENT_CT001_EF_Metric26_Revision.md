# Amendment CT-001 (E+F) — C160 Metric 26 Revision + G-15 Pipeline Redesign Declaration

**CT-ID:** CT-001
**Amendment status:** PROPOSED — awaiting R0GV3 approval to merge into canon
**Decision confirmed:** 2026-06-30 by R0GV3
**Resolution:** Option E (revise Metric 26 to ≥60%, G-14) + Option F (pipeline redesign declared G-15 target)
**Docs affected:** C160 (Metric 26), BIOPHOTON_09 (ceiling analysis + G-15 note)
**Supersedes:** AMENDMENT_CT001_BIOPHOTON09_C160_BCI_Coherence.md (Option D — partially applied; detector upgrade + double QEC still retained)
**Closes:** Issue #707

---

## Physics Basis

SIM-008 established that the three pre-detector pipeline stages create a hard physical ceiling:

```
Emission Capture × Waveguide Transit × Thermal Attenuation
= 0.82 × 0.91 × 0.88 = 0.657 (65.7%)
```

Even with a perfect detector (100%) and perfect QEC (100%), BCI cannot exceed **65.7%** under the current 3-stage pre-detector architecture. The ≥70% target in C160 Metric 26 is physically unreachable in G-14 without pipeline architectural change.

---

## Changes to C160 (System Metrics)

### Metric 26 — Revised Target

**Before:**
> Metric 26 — Biophotonic Coherence Index (BCI): target ≥70% post-QEC

**After:**
> **Metric 26 — Biophotonic Coherence Index (BCI)**
>
> **G-14 target: ≥60% post-QEC** (achievable with CP-3 detector ≥92% + double QEC)
>
> **G-15 target: ≥70% post-QEC** (requires CP-3 pre-detector pipeline redesign; see BIOPHOTON_09 §G-15)
>
> *Physics note (SIM-002, SIM-008, 2026-06-30):*
> *The current 3-stage pre-detector pipeline (Emission × Waveguide × Thermal = 0.657) imposes a hard ceiling of 65.7% BCI regardless of detector or QEC quality. The ≥60% G-14 target is achievable under this architecture. The ≥70% G-15 target requires reducing or fusing pre-detector stages to raise the pipeline ceiling to ≥72%. Canon tension CT-001 (Issue #707) documents the full analysis.*

---

## Changes to BIOPHOTON_09 (CP-3 Transducer Specification)

### Retained from Option D
The following changes from AMENDMENT_CT001_BIOPHOTON09_C160_BCI_Coherence.md are retained:
- Detector Efficiency revised to ≥92%, σ≤0.03 (Stage 4)
- Double QEC pass architecture (Stages 5a + 5b)

### New: Physical Ceiling Analysis Section

**Add to BIOPHOTON_09:**

> **§ CP-3 Pipeline Physical Ceiling Analysis**
>
> The multiplicative product of pre-detector stages sets a hard BCI ceiling:
>
> | Scenario | Ceiling |
> |---|---|
> | Current 3-stage pre-detector | **65.7%** |
> | Fused Waveguide+Thermal (target: 0.92) | ~72.5% |
> | Single-stage pre-detector (target: 0.90) | ~73.8% |
>
> *G-14 operates within the 65.7% ceiling. G-15 pipeline redesign must raise the ceiling above 70% before the Metric 26 G-15 target becomes achievable.*

### New: G-15 Hardware Goal Declaration

**Add to BIOPHOTON_09:**

> **§ G-15 Hardware Goal: Pre-Detector Pipeline Redesign**
>
> To achieve BCI ≥70% (C160 Metric 26 G-15 target), the CP-3 transducer pre-detector pipeline must be redesigned in G-15 to:
> 1. Fuse or eliminate the Waveguide Transit and Thermal Attenuation stages, OR
> 2. Develop a direct-capture transducer that bypasses multi-stage optical routing
>
> This is a hardware architecture goal, not a calibration task. It requires dedicated R&D in G-15 and should be scoped as a separate work order.

---

## Summary of CT-001 Final State

| What | Before | After |
|---|---|---|
| C160 Metric 26 G-14 target | ≥70% (unachievable) | **≥60% (achievable)** |
| C160 Metric 26 G-15 target | (not declared) | **≥70% (pipeline redesign required)** |
| BIOPHOTON_09 Detector Efficiency | 79% / σ=0.06 | **≥92% / σ≤0.03** |
| BIOPHOTON_09 QEC | Single pass | **Double pass (5a + 5b)** |
| BIOPHOTON_09 ceiling analysis | Absent | **65.7% ceiling documented** |
| BIOPHOTON_09 G-15 goal | Absent | **Pipeline redesign declared** |

---

## Amendment Sign-Off

- [x] R0GV3 decision confirmed: 2026-06-30 (Option E+F)
- [ ] Amendment reviewed by R0GV3
- [ ] Merged into `canon/C160.md`
- [ ] Merged into `canon/BIOPHOTON_09.md`
- [ ] Issue #707 closed
- [ ] CHANGELOG updated

*Amendment CT-001 (E+F) proposed 2026-06-30 by GAIA. Physics-first resolution. Awaiting merge approval.*
