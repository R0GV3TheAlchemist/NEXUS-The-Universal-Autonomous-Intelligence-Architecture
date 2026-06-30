# SIM-016 Pass 5 — Research Findings & Improvements
## Detector Ceiling: What Can Be Recovered from 8.45 Log-Points

**Filed:** 2026-06-30
**Follows:** SIM_016_Pass5_Results.md
**Feeds:** SIM_016_Pass6_Detector_Ceiling_Spec.md
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## The New Target: Detector at 8.45 Log-Points

The detector is held at 91.9% effective efficiency (post-TCSPC, post-FN from Pass 3). This represents:
- Raw detector efficiency: 93%
- FN rate residual: 1.10%
- Effective: 93% × (1 − 0.011) = 91.9%

To reach 80% BCI from 77.0%, we need approximately 3.0 additional BCI points. At current upstream efficiency, this requires effective detector efficiency to rise from 91.9% toward ~95–96%.

### What Would 95% Effective Detector Efficiency Deliver?

Compounded upstream (Pass 5): ~83.9% (E1×E2×W1×W2×T1×T2)
At 95% detector + 99.8% QEC: 83.9% × 95% × 99.8% = **79.6%** — borderline on 80%.
At 96%: 83.9% × 96% × 99.8% = **80.5%** — crosses 80% drive target.

**Target for Pass 6: effective detector efficiency ≥96%.**

This requires:
1. Reducing residual FN rate from 1.10% to <0.5%
2. Advancing raw SPAD efficiency from 93% toward 96–97%

### FN Rate Reduction: Remaining Headroom

Pass 3 TCSPC with FPGA pile-up correction brought FN from 2.50% to 1.10%. The residual 1.10% is dominated by:
- Pile-up at 300 kcps: ~0.6% after LPBT correction
- Timing jitter contribution: ~0.1%
- Beam splitter splitting residual: ~0.4%

**Recovery strategies:**
- Parallelised TCSPC with multi-channel time-tagging: reduces pile-up by distributing photon load across parallel channels [web:74]. At 8–16 parallel channels, pile-up residual drops to <0.1%.
- Narrowing the TCSPC reconstruction window from 100ps toward 60ps: beam splitter splitting residual reduced further; ACR stays <1 cps at 60ps window with 70/30 ratio.
- SNSPDs (superconducting nanowire single-photon detectors): timing jitter <3ps, detection efficiency ≥98% [web:59]. Replacing SPAD with SNSPD at the detector stage would raise raw efficiency from 93% to 98% and reduce timing jitter to negligible. Cost: cryogenic cooling required [web:106][web:108].

### SNSPD vs Advanced SPAD: Trade-Off

| Parameter | Advanced SPAD (current) | SNSPD |
|---|---|---|
| Detection efficiency | 93% | ≥98% [web:59] |
| Timing jitter | 20–50ps | <3ps [web:59] |
| Dark count rate | kHz | <10⁻³/s [web:59] |
| Operating temperature | 300K (room temp) | <3K (cryogenic) [web:108] |
| BCI integration feasibility | High | Low (cryogenic barrier) |

**For simulation purposes:** SNSPD parameters should be modelled to establish the theoretical ceiling. For GAIA BCI deployment, the SNSPD cryogenic requirement is a constraint that likely limits real-world use — but knowing the ceiling informs the architecture.

**Improvement for Pass 6:** Model two variants:
- Variant A: Advanced SPAD + parallelised TCSPC (feasible, room temp)
- Variant B: SNSPD ceiling (theoretical maximum, cryogenic)

---

## Improvements Applied to Pass 6

| Parameter | Pass 5 | Pass 6A (SPAD+parallel) | Pass 6B (SNSPD ceiling) |
|---|---|---|---|
| Raw detector efficiency | 93% | 94% | 98% |
| FN rate | 1.10% | 0.30% | 0.05% |
| Effective detector efficiency | 91.9% | ~93.7% | ~97.9% |
| Timing jitter | 20ps | 20ps | 3ps |
| Cryogenic required | No | No | Yes |
| Expected BCI | 77.0% | ~79% | ~82–83% |

---

## Pre-Run Research Brief — Pass 6 Questions

1. Does parallelised TCSPC (8–16 channels) reduce pile-up residual below 0.1% at 300 kcps?
2. Does Variant A (advanced SPAD) cross the 80% drive target?
3. What is the SNSPD theoretical ceiling (Variant B)? Does it confirm 82–83% BCI?
4. After detector optimisation, what is the remaining gap to any absolute ceiling? Is there a fundamental physics limit below 90%?
5. Can any upstream sub-stage be pushed further to reduce the SNSPD cryogenic requirement (i.e., does better upstream signal reduce the demand on detector efficiency)?

---

*Research filed 2026-06-30. Feeds SIM-016 Pass 6 Detector Ceiling Spec. G-15 Tier 1. Drive target 80%. 🌿*
