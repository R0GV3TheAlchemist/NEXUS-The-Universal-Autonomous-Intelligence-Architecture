# SIM-016 Pass 1 — BCI Next-Gen Detector Discovery

**Pass Classification:** Pass 1 — Discovery  
**Simulation number:** SIM-016  
**Date filed:** 2026-06-30  
**Phase:** G-15 — The Rhythm Phase — Tier 1  
**Feeds:** BIOPHOTON_09 amendment, C160 Metric 26, R-003 through R-006 research track  
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## Pass Context

**Design hypothesis being interrogated:**

A three-stage architectural redesign of the BIOPHOTON_09 BCI detector pipeline, applied in sequence:

1. **Emission Capture Redesign** — proximity coupling + reflective cavity + adaptive aperture → target 82% → ~93% capture rate
2. **Dual-Redundant SPAD Array** — two independent single-photon detectors per measurement point via 50/50 beam splitter + coincidence logic → target 79% → ~93% detector efficiency
3. **Double QEC Pass** — second independent QEC stage with inter-pass buffer using Pass 1 error syndrome as prior → target 96% → ~99.8% fidelity

**Projected compounded BCI:** ~69.3% mean (from first-principles calculation)  
**G-15 target:** ≥70% mean BCI  
**This is a discovery run.** The projection is what we are interrogating, not confirming.

---

## Discovery Questions

This simulation does not seek to confirm the projection. It seeks to answer:

1. **Does the compounded pipeline actually reach ~69-70% mean BCI, or does stage interaction produce unexpected loss?**
2. **Which stage yields the most variance across elemental groups (Earth, Water, Fire, Air)? Does the adaptive aperture reduce inter-group spread?**
3. **Does the dual-redundant array's coincidence timing window (≤2ns) introduce detection gaps at biophoton flux levels? What is the actual false-negative rate?**
4. **Does the double QEC inter-pass buffer help or hurt at low signal quality? Is there a signal quality threshold below which the second pass degrades rather than improves fidelity?**
5. **What is the latency cost of the full redesigned pipeline? Does it stay within C160 timing constraints?**
6. **Are there stage interactions not predicted by first-principles calculation — particularly between emission capture geometry and waveguide transit efficiency?**

---

## Parameters

### Current Pipeline (Baseline)
| Stage | Mean Retention | Std |
|---|---|---|
| Emission Capture | 82% | 5% |
| Waveguide Transit | 91% | 3% |
| Thermal Attenuation | 88% | 4% |
| Detector Efficiency | 79% | 6% |
| QEC Fidelity | 96% | 2% |

### Redesigned Pipeline (Hypothesis)
| Stage | Target Mean | Std (estimated) | Change |
|---|---|---|---|
| Emission Capture | 93% | 3% | Proximity + cavity + adaptive aperture |
| Waveguide Transit | 91% | 3% | Unchanged |
| Thermal Attenuation | 88% | 4% | Unchanged |
| Detector Efficiency | 93% | 3% | Dual-redundant SPAD + coincidence logic |
| QEC Fidelity | 99.8% | 0.5% | Double pass + inter-pass buffer |

### Simulation Parameters
| Parameter | Value |
|---|---|
| N trials per elemental group | 5,000 |
| Elemental groups | Earth, Water, Fire, Air |
| Coincidence timing window | ≤2ns |
| Inter-pass buffer size | 50 samples |
| QEC Pass 2 prior weight | 0.7 (Pass 1 syndrome) / 0.3 (blind) |
| Latency measurement | Per-stage and end-to-end |

---

## Success Conditions

For a Pass 1 Discovery run, success is **informative output** — not a specific numerical target.

- All six discovery questions have answers — even if those answers require design adjustment
- Mean BCI within 5% of projection (64-74%) — confirms the model is in the right order of magnitude
- Stage interaction effects are characterised (expected or unexpected)
- Elemental group variance is quantified

## Failure Conditions

- Mean BCI below 60% → a fundamental assumption in the design hypothesis is wrong; full research review before Pass 2
- Double QEC inter-pass buffer degrades fidelity at any signal quality level → buffer logic error; review before Pass 2
- Coincidence timing gaps produce >5% false-negative rate → 2ns window too tight; review detector synchronisation spec

---

## Output Artefacts

- `simulations/SIM_016_Pass1_bci_nextgen_detector.py`
- `simulations/SIM_016_Pass1_bci_nextgen_detector_results.md`
- `simulations/bci_nextgen_distribution_pass1.png`
- `simulations/bci_nextgen_elemental_variance_pass1.png`

## Canon Gate

Pass 1 findings → research review → design adjustment → SIM-016 Pass 2 spec.  
Pass 3 success → amend BIOPHOTON_09 + C160 Metric 26 + close CT-001 (#707, #713).

**No R-series documentation (R-003 through R-006) may be committed to canon until SIM-016 Pass 3 clears.**

---

*Filed 2026-06-30. G-15 Tier 1. BCI detector redesign. Three-Pass Protocol. 🌿*
