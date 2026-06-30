# SIM-016 Pass 2 — Research Findings & Improvements
## TCSPC, Beam Splitter Ratio, and Per-Pixel Gating Physics

**Filed:** 2026-06-30
**Follows:** SIM_016_Pass2_Results.md
**Feeds:** SIM_016_Pass3_BCI_NextGen_Detector_Verification.md (updated)
**80% BCI target established this session**
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Target Revision

The G-15 Tier 1 minimum target is ≥70% BCI. This session establishes a **drive target of ≥80% BCI** — not stopping at spec compliance but driving toward the genuine architectural ceiling. Each pass must track the compounding margin toward 80% explicitly.

Current position: 68.0% (Pass 2). Gap to 80%: 12 points. Identified recovery mechanisms below.

---

## Research Finding 1 — TCSPC Time-Tagged Reconstruction

TCSPC is the established method of choice for ps-resolution photon arrival timing [web:81][web:75]. Key confirmed properties:

- **Timing resolution:** 20–80ps typical with SPAD detectors [web:72][web:64] — far below the 2ns coincidence window that was causing our false-negative problem
- **Time window tuneable:** 10ps to 8 microseconds depending on configuration [web:79] — complete flexibility for per-subject g²(τ) calibration
- **Pile-up at high flux:** At 300 kcps signal rate, pile-up distortion is a known TCSPC limitation at high photon count rates [web:73]. However, FPGA-based pile-up correction (Laser Period Blind Time method) resolves this with low-cost hardware [web:73]
- **Parallelised TCSPC:** Demonstrated in biological tissue imaging with multiple parallel channels [web:74] — directly applicable to multi-pixel SPAD array configuration
- **Per-subject g²(τ) calibration:** Standard practice in photon correlation experiments [web:75] — the coincidence window is set from the second-order coherence function of the specific source, not assumed globally

**Expected FN rate with TCSPC:** <0.5% — genuine coincident pairs reconstructed from time-tags regardless of beam splitter splitting ratio at moment of arrival.

**Recovery:** ~2.0–2.5 BCI points from FN reduction alone.

---

## Research Finding 2 — Beam Splitter Ratio Optimisation

The 50/50 beam splitter was chosen for symmetric redundancy. Pass 2 revealed this is the source of the FN problem at high flux: uneven splitting at the moment of burst arrival causes single-arm events that fail coincidence.

Research on tunable beam splitter ratios [web:80] confirms:
- **Tunable split ratio** is achievable with high fidelity (≥99% overall efficiency in demonstrated systems)
- **Asymmetric splitting (70/30)** would send the majority of photons to the primary detector, reserving the secondary SPAD as a confirmation arm rather than an equal partner
- At 70/30: primary arm at 210 kcps, secondary at 90 kcps — genuine correlated emission still produces coincidences; uncorrelated background less likely to produce accidental coincidences on both arms
- **Combined with TCSPC:** asymmetric splitting + time-tagged reconstruction would virtually eliminate both FN and ACR problems simultaneously

**Estimated additional recovery:** 0.5–1.0 BCI points on top of TCSPC fix.

---

## Research Finding 3 — Per-Pixel Adaptive Gating for Fire Group

Adaptive gating using Thompson sampling is established for SPAD systems [web:61]. The CMU adaptive gating work confirms:
- **Pulse-by-pulse adaptation:** Gate position (and window) updated every SPAD cycle based on prior photon observations
- **Depth distribution prior:** In our context, the equivalent is the emission burst profile prior — updated per pixel per epoch
- Per-pixel adaptation allows each detector element to calibrate to the local emission statistics of the biological tissue it is facing

Fire group's ±6.8% within-group variance arises from heterogeneous biophoton emission across different tissue regions. Per-pixel gating allows each pixel to track its local emission profile rather than applying a system-wide gate.

**Estimated variance reduction:** ±6.8% → ±4.5–5.0% (conservative). Mean BCI contribution: +0.3–0.5 points from variance reduction alone, but more importantly, the lower variance means fewer trials falling below 70% — improving the pass rate.

---

## Research Finding 4 — Pile-Up Correction at 300 kcps

At 300 kcps signal rate, standard TCSPC suffers pile-up distortion [web:73]. The FPGA-based Laser Period Blind Time (LPBT) correction method:
- Corrects pile-up distortions in real time with low-cost FPGA hardware
- Enables reliable TCSPC at high photon count rates without sacrificing timing resolution
- Latency overhead: minimal (FPGA-based, sub-cycle)

This must be included in the Pass 3 detector model. Without pile-up correction, TCSPC at 300 kcps would introduce a new distortion that partially offsets the FN recovery.

**With pile-up correction included:** net TCSPC benefit is preserved at high flux. Without it: partial degradation at peak flux levels.

---

## Compounding Improvements Applied to Pass 3

| Mechanism | Pass 2 | Pass 3 | Expected BCI Recovery |
|---|---|---|---|
| TCSPC time-tagged reconstruction | Not applied | Applied + pile-up correction | +2.0–2.5 pts |
| Beam splitter ratio 70/30 | 50/50 | 70/30 asymmetric | +0.5–1.0 pts |
| Per-pixel adaptive gating (Fire) | Not applied | Applied | +0.3–0.5 pts (variance) |
| Pile-up correction (FPGA) | Not modelled | Modelled | Preserves TCSPC gain |
| **Total projected recovery** | 68.0% | **~71–72%** | **+3–4 pts** |

**Gap to 80% after Pass 3:** ~8–9 points remaining. Further passes will target emission capture ceiling and QEC limits.

---

## Pre-Run Research Brief — Questions for Pass 3

Per the updated simulation protocol (pre-run research brief standard), Pass 3 must answer:

1. Does TCSPC + pile-up correction recover the full 2.50% FN rate, or does residual distortion remain at 300 kcps?
2. Does the 70/30 beam splitter ratio produce meaningful ACR reduction vs 50/50 with TCSPC?
3. Does per-pixel adaptive gating reduce Fire group variance below ±5%?
4. What is the dominant loss mechanism after TCSPC is applied? This determines Pass 4 research direction.
5. Does the compounded pipeline cross 70%? Does it approach 72%?

---

*Research filed 2026-06-30. Feeds SIM-016 Pass 3 spec (updated). 80% drive target established. 🌿*
