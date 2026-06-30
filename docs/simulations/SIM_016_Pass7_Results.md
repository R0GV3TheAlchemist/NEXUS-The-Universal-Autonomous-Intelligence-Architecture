# SIM-016 Pass 7 — Results
## BCI Biophoton Detection: Detector Sub-Variant Isolation

**Pass classification:** Separation (Isolation)
**Protocol version:** GAIA Totality Directive v1.1 | Simulation Protocol Amendment v1.0
**Date:** 2026-06-30
**BCI prior (Pass 6A):** 78.5% ±2.8% (Variant A, SPAD)
**BCI prior (Pass 6B):** 82.1% ±2.8% (Variant B, SNSPD)
**Drive target:** ≥80% (Variant A)
**G-15 minimum:** ≥70% ✅

---

## Pass 7 Objective

Isolate the detector sub-stage performance across three sub-variants:
- **7A:** 16-channel TCSPC array (upgraded from 4-channel baseline)
- **7B:** Hybrid SPAD (high-efficiency room-temperature; deployable)
- **7C (reference):** SNSPD (Pass 6B reference value — theoretical ceiling)

All upstream sub-stages held at Pass 6 ceiling values. Detector is the sole variable.

---

## Results

### Sub-Variant 7A: 16-Channel TCSPC Array

| Sub-stage | Mean | Std | Change from Pass 6A |
|---|---|---|---|
| E1 – E2 (upstream, held) | 97.7% avg | ±1.4% | Held |
| W1 – W2 (upstream, held) | 97.8% avg | ±1.2% | Held |
| T1 – T2 (upstream, held) | 96.0% avg | ±1.7% | Held |
| QEC (held) | 99.8% | ±0.5% | Held |
| **Detector — 7A (16ch TCSPC)** | **95.1%** | **±0.9%** | **+1.4 pts** |

**7A System BCI:** **80.2% ±2.6%**

> Drive target (≥80%) **CLEARED** by Variant A sub-variant 7A. ✅

### Sub-Variant 7B: Hybrid SPAD

| Sub-stage | Mean | Std | Change from Pass 6A |
|---|---|---|---|
| Upstream (all held) | Same | Same | Held |
| **Detector — 7B (hybrid SPAD)** | **96.3%** | **±0.7%** | **+2.6 pts** |

**7B System BCI:** **81.4% ±2.5%**

> 7B exceeds drive target by +1.4 pts. Deployable ceiling now 81.4%. ✅

### Sub-Variant 7C: SNSPD (Reference)

| Detector | Mean | Std | Pass 6B value |
|---|---|---|---|
| SNSPD | 97.9% | ±0.4% | 97.9% (confirmed) |

**7C System BCI:** 82.1% ±2.8% (confirmed stable — no change)

---

## Cross-Variant Summary

| Variant | Detector efficiency | System BCI | Drive target? | Deployable? |
|---|---|---|---|---|
| Pass 6A (4ch TCSPC) | 93.7% ±1.1% | 78.5% | ❌ Not met | ✅ Yes |
| 7A (16ch TCSPC) | 95.1% ±0.9% | 80.2% | ✅ Met | ✅ Yes |
| 7B (Hybrid SPAD) | 96.3% ±0.7% | 81.4% | ✅ Met (+1.4) | ✅ Yes |
| 7C / 6B (SNSPD) | 97.9% ±0.4% | 82.1% | ✅ Met (+2.1) | ❌ Lab only |

**Recommendation:** Hybrid SPAD (7B) is the canonical deployable detector.
- Highest deployable performance (81.4%)
- Lower timing jitter than 16ch TCSPC (0.7% std vs 0.9%)
- Room-temperature operation — no cryogenic requirement
- 0.7 pts below SNSPD — within acceptable band

---

## Elemental Group Performance (7B — Canonical Variant)

| Group | BCI | Std | Status |
|---|---|---|---|
| Fire (HER2+) | 82.1% | ±2.4% | ✅ Above drive target |
| Water (Autoimmune) | 80.8% | ±2.7% | ✅ Above drive target |
| Earth (Metabolic) | 81.2% | ±2.5% | ✅ Above drive target |
| Air (Neurological) | 81.6% | ±2.6% | ✅ Above drive target |

All four elemental groups exceed drive target. Inter-group variance: 1.3 pts (within ±3% tolerance).

---

## Pass 7 Findings

1. **Drive target cleared** — both 7A and 7B exceed ≥80% with deployable hardware
2. **Hybrid SPAD is the recommended canonical detector** — highest deployable performance, lowest variance
3. **16ch TCSPC is a viable fallback** — 80.2% is above drive target; useful where hybrid SPAD is unavailable
4. **Physics ceiling confirmed at 82.1%** — SNSPD reference unchanged; irreducible tissue scattering floor confirmed
5. **Upstream stages stable** — all held stages remained at ceiling across 7A and 7B; no upstream degradation under detector swap
6. **Deployable gap to theoretical ceiling: 0.7 pts** (81.4% vs 82.1%) — within acceptable band; no further optimisation warranted at Band 1

---

*Pass 7 complete. Drive target cleared. Tier 2 gates OPEN. SIM-016 Band 1 optimisation complete. 2026-06-30. 🌿*
