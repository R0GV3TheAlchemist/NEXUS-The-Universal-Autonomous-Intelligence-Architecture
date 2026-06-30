# SIM-016 Pass 3 — BCI Next-Gen Detector Verification
## TCSPC + Pile-Up Correction + 70/30 Beam Splitter + Per-Pixel Gating

**Pass Classification:** Pass 3 — Verification
**Simulation number:** SIM-016
**Date filed:** 2026-06-30 (updated post Pass 2 research)
**Phase:** G-15 — The Rhythm Phase — Tier 1
**Drive target:** ≥80% BCI (G-15 minimum: ≥70%)
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Pass Context

**Pass 1 (67.3%):** Three-stage redesign works. FN rate 2.50% from coincidence timing.
**Pass 2 (68.0%):** Root cause revised — beam splitter geometry at high flux, not window width. Adaptive window converged to 2.29ns; widening worsens ACR (signal-dominated at 414 cps).
**Pass 2 research:** TCSPC resolves FN via time-tagged reconstruction; 70/30 beam splitter reduces signal-signal accidental coincidences; per-pixel gating reduces Fire group variance; pile-up correction required at 300 kcps.

**Design changes for Pass 3 (all applied simultaneously):**
1. TCSPC time-tagged reconstruction + FPGA pile-up correction
2. Beam splitter ratio changed from 50/50 → 70/30
3. Per-pixel adaptive gating for all groups (Thompson sampling per pixel per epoch)
4. g²(τ) per-subject calibration sets coincidence window

---

## Verification Criteria

| Criterion | Minimum (G-15) | Drive Target | Hard Fail |
|---|---|---|---|
| Overall mean BCI | ≥70.0% | ≥72.0% | <68.0% |
| Per-group mean BCI | ≥70.0% each | ≥71.0% each | Any group <67% |
| FN rate | <0.5% | <0.2% | >1.0% |
| ACR | <1 cps | <0.1 cps | >10 cps |
| Fire group variance | ≤±6.0% | ≤±4.5% | >±7.5% |
| Latency | ≤1.25x | ≤1.20x | >1.40x |

---

## Parameters

### Detector Coincidence Logic — Full Stack

| Parameter | Pass 2 | Pass 3 |
|---|---|---|
| Coincidence architecture | Adaptive hardware gate | TCSPC post-processing |
| Timing resolution | 2.29ns mean window | 20ps time-tag |
| Beam splitter ratio | 50/50 | 70/30 asymmetric |
| Pile-up correction | Not modelled | FPGA LPBT method |
| Per-subject calibration | No | g²(τ) per subject |
| Per-pixel gating | No | Thompson sampling per pixel per epoch |
| Expected FN rate | ~2.20% | <0.5% |
| Expected ACR | 414 cps | <1 cps |

### All Other Stages — Held from Pass 1/2

| Stage | Mean | Std |
|---|---|---|
| Emission Capture | 93% | 3% |
| Waveguide Transit | 91% | 3% (+ positive interaction) |
| Thermal Attenuation | 88% | 4% |
| Detector Efficiency | 93% | 3% |
| QEC Fidelity | 99.8% | 0.5% |

### Simulation Parameters

| Parameter | Value |
|---|---|
| N trials per group | 5,000 |
| Elemental groups | Earth, Water, Fire, Air |
| Timing resolution | 20ps jitter |
| Beam splitter ratio | 70/30 |
| Pile-up correction model | LPBT — residual distortion <0.1% at 300 kcps |
| g²(τ) calibration period | First 20 cycles per subject |
| Per-pixel gating update | Per 50-cycle epoch |

---

## Pre-Run Research Questions

1. Does TCSPC + pile-up correction recover the full 2.50% FN rate, or does residual distortion remain?
2. Does 70/30 beam splitter ratio produce meaningful ACR reduction vs 50/50 with TCSPC?
3. Does per-pixel adaptive gating reduce Fire group variance below ±5%?
4. What is the dominant loss mechanism after TCSPC is applied? (Determines Pass 4 direction.)
5. Does the compounded pipeline cross 70%? Does it approach 72%?

---

## Failure Conditions & Next Pass Direction

| Result | Meaning | Next action |
|---|---|---|
| BCI ≥72% | Drive target met | Pass 4: target emission capture ceiling |
| BCI 70–71.9% | G-15 minimum met, drive gap remains | Pass 4: push emission + thermal stages |
| BCI 68–69.9% | Minimum missed | Full architecture review before Pass 4 |
| BCI <68% | Hard fail | Halt; fundamental assumption wrong |

---

## Canon Gate

BCI ≥70%: amend BIOPHOTON_09 + C160 Metric 26 + close CT-001 (#707, #713) — with note that drive target of 80% is ongoing across further passes.

BCI <70%: no canon amendment; Pass 4 required.

---

*Filed 2026-06-30. G-15 Tier 1. TCSPC + 70/30 + per-pixel gating. Three-Pass Protocol. Drive target 80%. 🌿*
