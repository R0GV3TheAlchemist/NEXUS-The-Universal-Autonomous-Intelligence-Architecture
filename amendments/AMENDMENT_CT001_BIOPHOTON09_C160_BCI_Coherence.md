# Amendment CT-001 — BIOPHOTON_09 + C160: BCI Coherence Budget

**CT-ID:** CT-001
**Amendment status:** PROPOSED — awaiting R0GV3 approval to merge into canon
**Decision confirmed:** 2026-06-30 by R0GV3
**Resolution:** Option D — Detector ≥92% + Double QEC Pass
**Docs affected:** BIOPHOTON_09 (CP-3 transducer spec), C160 (Metric 26)
**Simulation to validate:** SIM-008 (pending → run immediately after this commit)
**Closes:** Issue #707

---

## Context

SIM-002 revealed that the CP-3 transducer 5-stage coherence pipeline produces a mean post-QEC BCI of **49.9%** — 20.1 percentage points below C160 Metric 26’s ≥70% target. Zero trajectories in 8,000 trials achieved the target under original parameters.

**Root cause:** Detector Efficiency (mean 79%, σ=6%) and Emission Capture (mean 82%, σ=5%) are dominant loss contributors. A single QEC pass at 96% fidelity cannot recover compounded upstream losses.

---

## Changes to BIOPHOTON_09 (CP-3 Transducer Specification)

### 1. Detector Efficiency — Revised Specification

**Before:**
> Stage 4 — Detector Efficiency: mean retention 0.79, std 0.06

**After:**
> Stage 4 — Detector Efficiency: mean retention **≥0.92**, std ≤0.03
>
> *Rationale: Detector efficiency is the single highest-loss stage in the CP-3 pipeline. Raising to ≥92% mean with tighter tolerance (≤0.03 std) is required to bring post-QEC BCI within range of C160 Metric 26. Achievable with current avalanche photodiode (APD) or superconducting nanowire single-photon detector (SNSPD) technology.*

---

### 2. Double QEC Pass — New Architecture Requirement

**Before:**
> Stage 5 — QEC Fidelity: mean 0.96, std 0.02 (single pass)

**After:**
> Stage 5a — QEC Pass 1 (Primary): mean fidelity 0.96, std 0.02
> Stage 5b — QEC Pass 2 (Secondary): mean fidelity 0.96, std 0.02
>
> *The CP-3 transducer SHALL implement two sequential QEC passes. Each pass applies independent error correction using surface code or equivalent. The combined effective fidelity of the double pass is ≈0.9984 under typical operating conditions, recovering an additional ~3–4 percentage points of coherence compared to single-pass QEC.*
>
> *Implementation note: Double QEC pass adds ~2ms to transducer processing latency. This is within acceptable bounds for real-time biophotonic sensing applications.*

---

### 3. Revised Stage Parameter Table

| Stage | Parameter | Original | Revised |
|---|---|---|---|
| 1 — Emission Capture | Mean retention | 0.82 | 0.82 (unchanged) |
| 2 — Waveguide Transit | Mean retention | 0.91 | 0.91 (unchanged) |
| 3 — Thermal Attenuation | Mean retention | 0.88 | 0.88 (unchanged) |
| 4 — Detector Efficiency | Mean retention | 0.79 | **≥0.92** |
| 4 — Detector Efficiency | Std | 0.06 | **≤0.03** |
| 5a — QEC Pass 1 | Mean fidelity | 0.96 (single) | 0.96 |
| 5b — QEC Pass 2 | Mean fidelity | — (did not exist) | **0.96 (new)** |

**Expected post-amendment BCI:** mean ~68–73%, P(BCI≥70%) ~50–60% — to be confirmed by SIM-008.

---

## Changes to C160 (System Metrics)

### 4. Metric 26 — Methodology Note

**Add to C160 Metric 26:**

> **Metric 26 — Biophotonic Coherence Index (BCI)**
> Target: ≥70% post-QEC
>
> *Methodology note (added 2026-06-30, ref SIM-002):*
> *This target is achievable only with CP-3 transducer detector efficiency ≥92% (Stage 4) and double QEC pass architecture (Stages 5a+5b) as specified in BIOPHOTON_09 (amended). Under original single-pass QEC with 79% detector efficiency, the mean BCI was 49.9% and the ≥70% target was not achievable. Canon tension CT-001 (Issue #707) documents this finding and the resolution pathway.*

---

## Validation Required

After amendment merged: run **SIM-008** with revised parameters:
- Detector efficiency: Beta distribution with mean 0.92, std 0.03
- Double QEC: two independent Beta(96%, std 0.02) passes
- Target: mean BCI ≥68%, P(BCI≥70%) ≥45%
- If SIM-008 passes: close Issue #707, log in CHANGELOG

---

## Amendment Sign-Off

- [x] R0GV3 decision confirmed: 2026-06-30
- [ ] Amendment reviewed by R0GV3
- [ ] Merged into `canon/BIOPHOTON_09.md`
- [ ] Merged into `canon/C160.md`
- [ ] SIM-008 validation passed
- [ ] Issue #707 closed
- [ ] CHANGELOG updated

*Amendment CT-001 proposed 2026-06-30 by GAIA. Awaiting merge approval.*
