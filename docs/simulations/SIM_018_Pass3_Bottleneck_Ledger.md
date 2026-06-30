# SIM_018 Pass 3 — Bottleneck Ledger

**Date:** 2026-06-30  
**Pass:** 3 (Verification)  
**Score entering:** 84.7% | **Score exiting:** 86.8%

---

## Ceiling Estimate (Updated)

| Estimate | Value | Basis |
|---|---|---|
| Previous ceiling estimate | 86–88% | Pass 2 bottleneck ledger |
| Updated ceiling estimate | **88–90%** | CNN 3C result exceeded 86%; feature extraction not yet saturated |
| Theoretical Bayes floor | ~12–15% | Biophoton literature (4-class regime) |
| Theoretical ceiling | **85–88%** (conservative) / **90%** (optimistic) | Depends on architecture depth |

**Revised assessment:** The ceiling is not the SVM classifier — it is the feature extractor. Replacing hand-crafted features with even a 1-layer CNN gained 2.1 pts. A deeper architecture has headroom to reach 88–90%.

---

## Binding Constraints (Ranked)

| Rank | Constraint | Impact | Addressable? |
|---|---|---|---|
| 1 | Shallow feature extraction (hand-crafted → CNN) | ~2–4 pts headroom remaining | ✅ Yes — Pass 4 |
| 2 | 4-class Bayes floor (irreducible shot noise) | ~12–15% floor, unavoidable | ❌ Architecture-independent |
| 3 | S3 ambiguous intent threshold | 0.6 pts recovered at threshold 0.55 | ✅ Resolved in Pass 3 |
| 4 | L↔R confusion (resolved in Pass 2) | Was 3.1 pts drag; now ≤0.4 pts | ✅ Resolved |

---

## What Was Tried and the Outcome

| Attempt | Result | Notes |
|---|---|---|
| 5-seed stability test | Mean 84.54%, std 0.49% | Confirmed stable; single-run ±2.1% was noise, not signal |
| Threshold sweep (0.50–0.70) | Optimal at 0.55 (+0.6 pts) | Threshold 0.60 was slightly over-abstaining |
| 1-layer CNN replacement | +2.1 pts to 86.8% | Feature extraction confirmed as primary remaining bottleneck |

---

## What Has NOT Been Tried

| Item | Projected Gain | Priority |
|---|---|---|
| 2–3 layer CNN | +1–3 pts (projected 88–90%) | HIGH — Pass 4 |
| Lightweight transformer on event stream | +2–4 pts (projected 88–91%) | HIGH — Pass 4 alt |
| Data augmentation (synthetic trials) | +0.5–1 pt | MEDIUM — Pass 4 supplementary |
| Cross-subject normalisation | +0.5–1.5 pts | MEDIUM — future |

---

*SIM_018 Pass 3 Bottleneck Ledger. 2026-06-30. 🌿*
