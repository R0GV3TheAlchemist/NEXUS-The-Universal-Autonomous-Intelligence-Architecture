# SIM-016 Pass 7 — Bottleneck Ledger

**Pass:** 7 (Separation — Isolation)
**Protocol version:** GAIA Totality Directive v1.1
**Date:** 2026-06-30

---

## Bottleneck Ledger — Post Pass 7 (Canonical Variant 7B, Hybrid SPAD)

| Sub-stage | Mean | Std | Log-loss (pts) | Rank | Recoverability |
|---|---|---|---|---|---|
| T1_depth | 95.0% | ±2.0% | 2.23 | #1 | Low — tissue physics ceiling |
| T2_temp_scatter | 97.0% | ±1.3% | 1.31 | #2 | Low — tissue physics ceiling |
| E1_aperture | 97.5% | ±1.5% | 1.10 | #3 | Low — geometry ceiling |
| W2_propagation | 97.5% | ±0.8% | 1.10 | #4 | Low — waveguide ceiling |
| Detector (7B hybrid SPAD) | 96.3% | ±0.7% | 1.61 | #5 | **Near-ceiling — 0.7 pts below SNSPD** |
| E2_adaptive | 97.9% | ±1.3% | 0.92 | #6 | Ceiling |
| W1_coupling | 97.9% | ±1.5% | 0.90 | #7 | Ceiling |
| QEC | 99.8% | ±0.5% | 0.09 | #8 | Ceiling |

**Status: All sub-stages at ceiling or near-ceiling. Band 1 optimisation COMPLETE.**

**Residual loss (0.7 pts detector gap to SNSPD):** Not recoverable within deployable hardware constraints. Accepted as the deployable physics floor.

**Total compounded loss from theoretical maximum (82.1% SNSPD → 81.4% hybrid SPAD):** 0.7 pts. This is irreducible for deployable hardware.

---

## No Further Band 1 Optimisation Passes Required

All eight sub-stages are at ceiling or within 0.7 pts of absolute ceiling. The correct next action is:
1. File Tier 2 canon amendments (GATE-001, 002, 003)
2. Run SIM-INT-012 (Band 1→2 integration)
3. Begin SIM-018 (Band 2 baseline)

No Band 1 optimisation pass is warranted until SIM-INT-012 reveals a Band 1-side integration bottleneck.

---

*Pass 7 Bottleneck Ledger. SIM-016. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
