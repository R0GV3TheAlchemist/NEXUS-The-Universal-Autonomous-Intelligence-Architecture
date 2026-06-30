# SIM_018 Pass 4 — Bottleneck Ledger

**Date:** 2026-06-30  
**Pass:** 4 (Optimisation — Distillation)  
**Score entering:** 86.8% | **Score exiting:** 89.6%

---

## Ceiling Estimate (Final for Current Architecture)

| Estimate | Value | Basis |
|---|---|---|
| Previous ceiling estimate | 88–90% | Pass 3 bottleneck ledger |
| Achieved score | **89.6%** | Pass 4D (transformer + ±5% augment) |
| Remaining headroom | ~0.4–1 pt | Approaching Bayes floor |
| Theoretical Bayes floor | ~10–12% (updated) | 4-class biophoton, transformer regime |
| Hard ceiling estimate | **~90–91%** | Cross-subject normalisation could add +0.5–1.5 pts |

---

## Binding Constraints (Ranked)

| Rank | Constraint | Impact | Addressable? |
|---|---|---|---|
| 1 | Bayes floor — irreducible biophotonic noise | ~10–12% floor | ❌ Architecture-independent |
| 2 | Single-subject data only | ~1–2 pts headroom via cross-subject normalisation | ✅ Future pass |
| 3 | 4-class label granularity | Coarser classes = lower ceiling; finer = lower accuracy | Trade-off |
| 4 | Val/train gap at 3-layer CNN | 2.67% gap — controlled but present | ⚠️ Monitor |

---

## What Was Tried and the Outcome

| Attempt | Result | Notes |
|---|---|---|
| 2-layer CNN (4A) | 87.83% | Just short of gate; confirmed 2 layers insufficient |
| 3-layer CNN (4B) | 88.50% | Gate cleared; val/train gap controlled |
| Lightweight transformer (4C) | 89.37% | Best architecture at current data volume |
| Time-warp ±5% (4D) | +0.23 pts → 89.6% | Validated pre-run Q2; conservative augmentation beneficial |
| Time-warp ±10% | −0.47 pts | Confirmed harmful; pre-run Q2 validated |

---

## What Has NOT Been Tried

| Item | Projected Gain | Priority |
|---|---|---|
| Cross-subject normalisation | +0.5–1.5 pts (projected ~90.5–91%) | MEDIUM — future pass |
| Deeper transformer (4-head attention) | +0.3–0.8 pts | LOW — approaching Bayes floor |
| Larger trial set (3,600+ trials/class) | +0.5–1 pt | LOW — data collection dependency |

**Assessment: The current architecture is near-optimal for this data volume. Further gains require more data or cross-subject approaches, not architectural depth.**

---

*SIM_018 Pass 4 Bottleneck Ledger. 2026-06-30. 🌿*
