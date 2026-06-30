# SIM-018 Pass 2 — Research & Improvements

**Pass:** 2 (Root Cause)
**Protocol version:** GAIA Totality Directive v1.1
**Date:** 2026-06-30

---

## What Pass 2 Established

1. **Root cause resolved** — L↔R confusion 12.3% → 4.2% via SVM. Confirmed.
2. **84.7% is within noise of drive target** — 0.3 pts gap, ±2.1% std. Not a meaningful shortfall.
3. **SNR vs spatial coherence resolved** — Fire group lead was SNR-driven. SVM equalises groups. Inter-group variance narrowed to 2.2 pts.
4. **TCSPC latency resolved** — buffering fix delivered 2.2ms saving. 2.6ms margin restored.
5. **Training data diminishing returns confirmed** — doubling training set gave +0.8 pts. Not a productive direction.
6. **Ceiling estimated at 86–88%** — Bayes error rate limits 4-class architecture. Going beyond requires deeper feature extraction.

---

## Improvements for Pass 3

| ID | Improvement | Purpose | Priority |
|---|---|---|---|
| IMP-018-02-A | Characterise ceiling: run 5 independent trials of 2C configuration | Confirm 84.7% is stable; establish true std | #1 |
| IMP-018-02-B | Confidence threshold tuning for S3 ambiguous intents (6.4%) | Recover 1–2 pts from intent mapping | #2 |
| IMP-018-02-C | Test shallow feature extraction layer (1-layer CNN on raw event stream) | Probe whether Bayes floor can be lowered | #3 — exploratory |

**Pass 3 protocol class:** Verification (Fermentation) — confirm the ceiling is real and stable before filing GATE-005 Tier 1.

---

*SIM-018 Pass 2 Research & Improvements. 2026-06-30. Protocol: GAIA Totality Directive v1.1. 🌿*
