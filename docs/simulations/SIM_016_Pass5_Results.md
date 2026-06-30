# SIM-016 Pass 5 Results — Upstream Optimisation

**Pass Classification:** Pass 5 — Optimisation
**Status:** COMPLETE ✅ — **77.0% BCI — G-15 MINIMUM CLEARED ✅** — 3.0 pts from 80% drive target
**Date run:** 2026-06-30 | **Trials:** N=5,000/group (20,000 total)
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Summary

T1 (depth attenuation), E1 (aperture geometry), and W1 (coupling interface) optimised simultaneously with T1–W2 joint path reduction. BCI jumped from 69.4% (Pass 4) to **77.0%** — a +7.6 point gain in a single pass. G-15 minimum target of 70% is cleared. Drive target of 80% is 3.0 points away. The detector is now the dominant constraint at 8.45 log-pts — larger than any remaining upstream sub-stage. The upstream optical path has been optimised to near its ceiling.

---

## Key Results

| Metric | Pass 4 | Pass 5 | Target |
|---|---|---|---|
| Overall Mean BCI | 69.4% | **77.0%** | ≥70% (min) ✅ / ≥80% (drive) |
| Earth | 69.5% ±2.6% | **77.1% ±2.2%** | ≥70% ✅ |
| Water | 69.4% ±3.4% | **77.0% ±2.8%** | ≥70% ✅ |
| Fire | 69.4% ±3.7% | **77.0% ±3.0%** | ≥70% ✅ |
| Air | 69.5% ±3.7% | **77.0% ±2.9%** | ≥70% ✅ |
| Gap to 70% | 0.6 pts | **CLEARED** | ✅ |
| Gap to 80% | 10.6 pts | **3.0 pts** | Closing |

---

## Sub-Stage Bottleneck Ledger — Pass 5 (Definitive)

| Sub-stage | Pass 4 log-loss | Pass 5 log-loss | Recovery | Rank |
|---|---|---|---|---|
| **Detector (held)** | 8.45 pts | **8.45 pts** | 0 | **#1 — New Dominant** |
| T1: Depth attenuation | 8.30 pts | **5.13 pts** | −3.17 | #2 |
| T2: Temp scattering | 3.06 pts | 3.05 pts | −0.01 | #3 |
| E1: Aperture geometry | 6.20 pts | **2.55 pts** | −3.65 | #4 |
| W2: Propagation | 3.04 pts | **2.53 pts** | −0.51 | #5 |
| E2: Adaptive capture | 2.09 pts | 2.15 pts | +0.06 | #6 |
| W1: Coupling interface | 5.13 pts | **2.08 pts** | −3.05 | #7 |

**The detector is now the binding constraint. Pass 6 targets the detector ceiling.**

---

## Pre-Run Research Questions — Answered

1. **Does upstream improvement make detector the dominant constraint?** Yes — detector at 8.45 log-pts, next sub-stage (T1) at 5.13. Confirmed. ✅
2. **T1–W2 joint path reduction: additive or superlinear?** W2 improved by −0.51 log-pts as a secondary effect of T1 path reduction. Additive but meaningful compound. ✅
3. **Upstream ceiling reached?** Effectively yes. E1, W1, W2 all below 3 log-pts. Only T1 (5.13) and T2 (3.05) have remaining headroom, but the detector gap is larger. ✅
4. **Gap to 80% location?** Primarily in the detector (8.45 log-pts). Secondary: T1 and T2. ✅
5. **QEC headroom?** QEC at 99.8% is not a meaningful constraint. No action needed. ✅

---

## Canon Gate Update

BCI ≥70%: **G-15 minimum met as of Pass 5.** Canon amendment process for BIOPHOTON_09 + C160 Metric 26 + CT-001 closure (#707, #713) can now begin, with note that drive target of 80% is ongoing.

**Pass 5 BCI for canon reference: 77.0% ±2.7% overall, all four elemental groups ≥77.0%.**

---

*Run: 2026-06-30. G-15 Tier 1. 70% cleared. Detector is next. Drive target 80% continues. 🌿*
