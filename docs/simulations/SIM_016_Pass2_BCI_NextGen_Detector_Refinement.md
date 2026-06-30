# SIM-016 Pass 2 — BCI Next-Gen Detector Refinement
## Coincidence Timing Fix Applied

**Pass Classification:** Pass 2 — Refinement
**Simulation number:** SIM-016
**Date filed:** 2026-06-30
**Phase:** G-15 — The Rhythm Phase — Tier 1
**Feeds:** BIOPHOTON_09 amendment, C160 Metric 26
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md
**Follows:** SIM_016_Pass1_Results.md + SIM_016_Pass1_Research_Improvements.md

---

## Pass Context

**What Pass 1 revealed:**
- Three-stage redesign delivers +17.6 point lift (49.7% → 67.3%) but misses 70% G-15 target by 2.7 points
- Root cause: 2ns coincidence timing window produces 2.50% false-negative rate at 93% detector efficiency
- At higher efficiency, biophoton coincident pairs arrive with temporal spread exceeding the 2ns discrimination window
- QEC double pass: sound (0.03% degradation rate). Emission capture: sound. Stage interaction: positive. Latency: within C160.
- Inter-group spread reduced from 0.4% to 0.1% — architecture is equitable

**How the design is adjusted (from research findings):**
- Replace fixed 2ns coincidence window with **adaptive flux-responsive window (2–4ns)**
- Thompson sampling per 50-cycle measurement window adjusts window width to measured flux density
- ACR penalty at 3–4ns is negligible at biophoton flux levels (ACR ≤ 0.36 cps accidental vs ~300 kcps signal)
- All other stages held constant — they performed as designed in Pass 1

---

## Refinement Hypotheses

1. **Adaptive coincidence window (2–4ns) recovers the 2.50% false-negative rate**, bringing effective detector efficiency from ~90.5% back toward 93% — adding ~2.0–2.5 BCI points
2. **Mean BCI crosses the 70% G-15 target** across all elemental groups
3. **ACR penalty is negligible** — accidental coincidence rate stays below 1 cps at all flux levels tested
4. **Adaptive window stabilises inter-group spread** — Fire group variance reduces from ±6.8% as window adapts to per-subject emission profile
5. **No new latency cost** — Thompson sampling window update overhead stays within C160 timing constraints

---

## Parameters

### Pipeline — All Stages (Pass 1 values held constant except detector coincidence logic)

| Stage | Mean | Std | Change from Pass 1 |
|---|---|---|---|
| Emission Capture | 93% | 3% | Unchanged |
| Waveguide Transit | 91% | 3% | Unchanged (positive interaction retained) |
| Thermal Attenuation | 88% | 4% | Unchanged |
| Detector Efficiency | 93% | 3% | Unchanged — coincidence logic updated |
| QEC Fidelity | 99.8% | 0.5% | Unchanged |

### Coincidence Logic — Updated

| Parameter | Pass 1 | Pass 2 |
|---|---|---|
| Window type | Fixed | Adaptive flux-responsive |
| Minimum window | 2ns | 2ns |
| Maximum window | 2ns | 4ns |
| Adaptation mechanism | None | Thompson sampling per 50-cycle window |
| Dark count rate model | Not modelled | kHz range — ACR explicitly tracked |
| Per-pixel adaptation | No | Optional test (Fire group) |

### Simulation Parameters

| Parameter | Value |
|---|---|
| N trials per elemental group | 5,000 |
| Elemental groups | Earth, Water, Fire, Air |
| Window adaptation period | 50 measurement cycles |
| Window range | 2.0–4.0ns |
| Dark count rate | 1 kHz per SPAD |
| Signal flux rate | ~300 kcps |
| ACR tracking | Per trial |

---

## Success Conditions

- Mean BCI ≥70.0% overall
- Mean BCI ≥70.0% for each elemental group individually
- ACR < 1 cps at all flux levels
- Fire group variance ≤±6.5% (modest improvement expected)
- Latency cost ≤1.20x baseline (adaptive logic overhead ≤0.05x)

## Failure Conditions

- Mean BCI <68% → adaptive window is not recovering the false-negative loss; review Thompson sampling implementation
- ACR >5 cps → window widening too aggressive at high flux; cap maximum window at 3ns and re-test
- Latency >1.25x baseline → Thompson sampling overhead too high; review update frequency (reduce to per-100-cycle)

---

## Output Artefacts

- `simulations/SIM_016_Pass2_bci_nextgen_detector.py`
- `simulations/SIM_016_Pass2_bci_nextgen_detector_results.md`
- `simulations/bci_nextgen_distribution_pass2.png`
- `simulations/bci_nextgen_adaptive_window_pass2.png`

## Canon Gate

Pass 2 success → research review → SIM-016 Pass 3 spec.  
Pass 3 success → amend BIOPHOTON_09 + C160 Metric 26 + close CT-001 (#707, #713).

**No BIOPHOTON_09 or C160 Metric 26 documentation may be committed to canon until Pass 3 clears.**

---

*Filed 2026-06-30. G-15 Tier 1. Coincidence timing fix. Three-Pass Protocol. 🌿*
