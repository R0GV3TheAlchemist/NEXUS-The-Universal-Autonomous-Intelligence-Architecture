# SIM-018 Pass 2 — Bottleneck Ledger

**Pass:** 2 (Root Cause)
**Protocol version:** GAIA Totality Directive v1.1
**Date:** 2026-06-30

---

## Bottleneck Ledger — Post Pass 2

| Sub-stage | Pass 2C accuracy contribution | Remaining loss | Rank | Recoverability |
|---|---|---|---|---|
| S2: Pattern classification (SVM) | 84.7% system | 15.3 pts total | — | Near ceiling for 4-class linear separability |
| L↔R residual confusion | 4.2% confusion | ~2–3 pts recoverable | #1 | Low — approaching Bayes error rate |
| S3: Intent mapping ambiguity | 6.4% ambiguous intents | ~1–2 pts recoverable | #2 | Medium — confidence threshold tuning |
| S1: Signal conditioning | 94.3% | Ceiling | #3 | Ceiling |
| S4: Temporal integration | 400ms + ramp-out | Near ceiling for this window | #4 | Low marginal gain |
| S5: Latency | 28.1ms (SPAD) | 1.9ms remaining budget | — | Comfortable |

**Assessment:** 84.7% is within noise of the drive target (85%). The remaining 0.3 pts gap is not a bottleneck — it is within the measurement std (±2.1%). Pass 3 should characterise the ceiling, not optimise for 0.3 pts.

**Predicted ceiling for 4-class biophoton intent classification with current architecture:** ~86–88%. The Bayes error rate (irreducible confusion from overlapping neural emission patterns) is estimated at ~12–14% of trials. Going beyond ~88% will require either higher-cardinality spatial features or a deeper feature extraction layer.

---

*SIM-018 Pass 2 Bottleneck Ledger. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
