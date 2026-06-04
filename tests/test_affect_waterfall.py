"""
tests/test_affect_waterfall.py
Parametrised waterfall regression suite — EV1-A (Sprint G-10 / F-1).

Canonical waterfall priority under test:
    0. GRIEF       grief_signal >= 0.50  OR  loss_score >= 0.70
    1. DISSONANCE  conflict_density >= 0.30
    2. UNCERTAINTY truth_score < 0.45
    3. CARE        flourishing >= 0.60  AND  truth_score < 0.75  (strict)
    4. RESONANCE   truth_score >= 0.75
    5. CARE        flourishing >= 0.60  (post-RESONANCE fallback)
    6. CURIOSITY   default

Pass gate: all 60 individual cases + macro-F1 >= 0.75 across 6 classes.

Key design decisions reflected in test cases
--------------------------------------------
* GRIEF is triggered only by grief_signal or loss_score, never by low truth.
  Low truth is an epistemic condition → UNCERTAINTY.
* truth_score=0.75 fires RESONANCE (not CARE) because the pre-RESONANCE CARE
  guard uses strict truth_score < 0.75.
* CARE fires only when flourishing >= 0.60. Moderate truth alone (without
  flourishing) produces CURIOSITY, not CARE.
"""
from __future__ import annotations

import pytest
from collections import defaultdict
from core.affect_inference import AffectState, AffectInference

ai = AffectInference()


def _infer(I, W, T, F, CD, grief):
    """Thin shim mapping test-matrix columns to AffectInference.infer()."""
    return ai.infer(
        identity_score    = I,
        wisdom_score      = W,
        truth_score       = T,
        flourishing_score = F,
        conflict_density  = CD,
        grief_signal      = float(grief),
    ).state


# ---------------------------------------------------------------------------
# Test-case matrix  (I, W, T, F, CD, grief_signal, expected, description)
# ---------------------------------------------------------------------------

CASES = [
    # ── GRIEF (10 cases) ────────────────────────────────────────────────────
    # Cases 0-4: grief_signal fires GRIEF
    (0.5, 0.5, 0.5, 0.5, 0.10, True,  AffectState.GRIEF,       "grief_signal=True fires GRIEF"),
    (0.5, 0.5, 0.5, 0.5, 0.10, 0.50,  AffectState.GRIEF,       "grief_signal=0.50 exactly fires GRIEF"),
    (0.5, 0.5, 0.5, 0.5, 0.10, 0.60,  AffectState.GRIEF,       "grief_signal=0.60 fires GRIEF"),
    (0.5, 0.5, 0.5, 0.5, 0.10, 0.90,  AffectState.GRIEF,       "grief_signal=0.90 fires GRIEF"),
    (0.5, 0.5, 0.5, 0.5, 0.10, 1.00,  AffectState.GRIEF,       "grief_signal=1.00 fires GRIEF"),
    # Cases 5-6: grief_signal below threshold → positive state fires instead.
    # F=0.65 ensures flourishing fires CARE, proving grief_signal<0.50 is a no-op.
    (0.5, 0.5, 0.5, 0.65, 0.10, 0.49, AffectState.CARE,        "grief_signal=0.49 does NOT fire GRIEF; flourishing fires CARE"),
    (0.5, 0.5, 0.5, 0.65, 0.10, False,AffectState.CARE,        "grief_signal=False does NOT fire GRIEF; flourishing fires CARE"),
    # Cases 7-9: grief overrides other signals
    (0.5, 0.5, 0.5, 0.5, 0.05, True,  AffectState.GRIEF,       "grief even without high CD"),
    (0.8, 0.8, 0.8, 0.9, 0.05, True,  AffectState.GRIEF,       "grief overrides high truth"),
    (0.3, 0.3, 0.3, 0.3, 0.40, True,  AffectState.GRIEF,       "grief overrides DISSONANCE too"),

    # ── DISSONANCE (10 cases) ────────────────────────────────────────────────
    (0.5, 0.5, 0.5, 0.5, 0.30, False, AffectState.DISSONANCE,  "CD=0.30 exact fires DISSONANCE"),
    (0.5, 0.5, 0.5, 0.5, 0.50, False, AffectState.DISSONANCE,  "CD=0.50 fires DISSONANCE"),
    (0.5, 0.5, 0.5, 0.5, 0.80, False, AffectState.DISSONANCE,  "CD=0.80 fires DISSONANCE"),
    (0.5, 0.5, 0.5, 0.5, 1.00, False, AffectState.DISSONANCE,  "CD=1.00 fires DISSONANCE"),
    (0.5, 0.5, 0.8, 0.5, 0.35, False, AffectState.DISSONANCE,  "high truth doesn't override DISSONANCE"),
    (0.5, 0.5, 0.5, 0.9, 0.40, False, AffectState.DISSONANCE,  "high flourishing doesn't override DISSONANCE"),
    # Cases 16-18: CD below threshold → positive state (F=0.65 provides CARE signal)
    (0.5, 0.5, 0.5, 0.65, 0.29, False,AffectState.CARE,        "CD=0.29 does NOT fire DISSONANCE; flourishing fires CARE"),
    (0.5, 0.5, 0.5, 0.65, 0.10, False,AffectState.CARE,        "CD=0.10 does NOT fire DISSONANCE; flourishing fires CARE"),
    (0.5, 0.5, 0.5, 0.65, 0.00, False,AffectState.CARE,        "CD=0.00 does NOT fire DISSONANCE; flourishing fires CARE"),
    (0.7, 0.7, 0.7, 0.8, 0.35, False, AffectState.DISSONANCE,  "DISSONANCE overrides all positive signals"),

    # ── UNCERTAINTY (10 cases) ───────────────────────────────────────────────
    (0.5, 0.5, 0.44, 0.5, 0.0, False, AffectState.UNCERTAINTY, "truth=0.44 fires UNCERTAINTY"),
    # truth=0.30: no truth→GRIEF gate; truth<0.45 → UNCERTAINTY
    (0.5, 0.5, 0.30, 0.5, 0.0, False, AffectState.UNCERTAINTY, "truth=0.30 < 0.45 fires UNCERTAINTY (not GRIEF — low truth is epistemic)"),
    (0.5, 0.5, 0.31, 0.5, 0.0, False, AffectState.UNCERTAINTY, "truth=0.31 just above 0.30, still < 0.45 → UNCERTAINTY"),
    (0.5, 0.5, 0.40, 0.5, 0.0, False, AffectState.UNCERTAINTY, "truth=0.40 fires UNCERTAINTY"),
    (0.5, 0.5, 0.10, 0.5, 0.0, False, AffectState.UNCERTAINTY, "truth=0.10 < 0.45 fires UNCERTAINTY (not GRIEF)"),
    (0.5, 0.5, 0.00, 0.5, 0.0, False, AffectState.UNCERTAINTY, "truth=0.00 fires UNCERTAINTY (not GRIEF)"),
    # Cases 26-27: truth >= 0.45 clears UNCERTAINTY; F=0.65 fires CARE
    (0.5, 0.5, 0.45, 0.65, 0.0, False,AffectState.CARE,        "truth=0.45 clears UNCERTAINTY; flourishing fires CARE"),
    (0.5, 0.5, 0.50, 0.65, 0.0, False,AffectState.CARE,        "truth=0.50 above UNCERTAINTY; flourishing fires CARE"),
    (0.5, 0.5, 0.44, 0.9, 0.0, False, AffectState.UNCERTAINTY, "high flourishing can't save low truth from UNCERTAINTY"),
    (0.5, 0.5, 0.44, 0.5, 0.29, False,AffectState.UNCERTAINTY, "CD=0.29 doesn't block UNCERTAINTY"),

    # ── RESONANCE (10 cases) ─────────────────────────────────────────────────
    (0.8, 0.8, 0.75, 0.5, 0.0, False, AffectState.RESONANCE,   "truth=0.75 exact fires RESONANCE (not CARE — strict < gate)"),
    (0.8, 0.8, 0.80, 0.5, 0.0, False, AffectState.RESONANCE,   "truth=0.80 fires RESONANCE"),
    (0.8, 0.8, 0.90, 0.5, 0.0, False, AffectState.RESONANCE,   "truth=0.90 fires RESONANCE"),
    (0.8, 0.8, 1.00, 0.5, 0.0, False, AffectState.RESONANCE,   "truth=1.00 fires RESONANCE"),
    (0.8, 0.8, 0.75, 0.5, 0.0, False, AffectState.RESONANCE,   "truth=0.75 is RESONANCE not CARE"),
    (0.9, 0.9, 0.85, 0.9, 0.0, False, AffectState.RESONANCE,   "truth=0.85 beats flourishing — RESONANCE wins"),
    (0.8, 0.8, 0.76, 0.5, 0.0, False, AffectState.RESONANCE,   "truth=0.76 fires RESONANCE"),
    (0.8, 0.8, 0.75, 0.4, 0.0, False, AffectState.RESONANCE,   "low flourishing with truth=0.75 is still RESONANCE"),
    (0.8, 0.8, 0.77, 0.5, 0.0, False, AffectState.RESONANCE,   "truth=0.77 fires RESONANCE"),
    (0.8, 0.8, 0.80, 0.5, 0.0, False, AffectState.RESONANCE,   "truth=0.80 fires RESONANCE (dup check)"),

    # ── CARE (10 cases) ──────────────────────────────────────────────────────
    (0.7, 0.7, 0.70, 0.85, 0.0, False, AffectState.CARE,       "care canonical"),
    (0.5, 0.5, 0.60, 0.80, 0.0, False, AffectState.CARE,       "flourishing=0.80 fires CARE"),
    (0.5, 0.5, 0.55, 0.65, 0.0, False, AffectState.CARE,       "flourishing=0.65 fires CARE"),
    (0.5, 0.5, 0.50, 0.70, 0.0, False, AffectState.CARE,       "flourishing=0.70 fires CARE"),
    (0.5, 0.5, 0.50, 0.90, 0.0, False, AffectState.CARE,       "flourishing=0.90 fires CARE"),
    (0.5, 0.5, 0.50, 1.00, 0.0, False, AffectState.CARE,       "flourishing=1.00 fires CARE"),
    (0.7, 0.65, 0.70, 0.90, 0.15, False, AffectState.CARE,     "flourishing dominant"),
    (0.74, 0.74, 0.74, 0.80, 0.24, False, AffectState.CARE,    "truth=0.74 misses RESONANCE; flourishing fires CARE"),
    # truth=0.75 with F=0.60: pre-RESONANCE CARE uses strict T<0.75, so T=0.75 goes to RESONANCE
    (0.7, 0.5, 0.75, 0.60, 0.1, False, AffectState.RESONANCE,  "truth=0.75 with F=0.60 fires RESONANCE (strict < boundary)"),
    (0.68, 0.48, 0.68, 0.60, 0.05, False, AffectState.CARE,    "truth=0.68; flour=0.60 fires CARE"),

    # ── CURIOSITY (10 cases) ─────────────────────────────────────────────────
    # CURIOSITY fires when neither flourishing (< 0.60) nor resonance (truth < 0.75)
    # nor UNCERTAINTY (truth >= 0.45) nor DISSONANCE triggers.
    (0.5, 0.5, 0.50, 0.50, 0.0, False, AffectState.CURIOSITY,  "default: no flourishing, no resonance"),
    (0.5, 0.5, 0.55, 0.55, 0.0, False, AffectState.CURIOSITY,  "moderate signals — flourishing=0.55 misses CARE"),
    (0.5, 0.5, 0.60, 0.50, 0.0, False, AffectState.CURIOSITY,  "truth=0.60, flourishing=0.50 → CURIOSITY"),
    (0.5, 0.5, 0.65, 0.50, 0.0, False, AffectState.CURIOSITY,  "truth=0.65, flourishing=0.50 → CURIOSITY"),
    (0.5, 0.5, 0.60, 0.55, 0.0, False, AffectState.CURIOSITY,  "flourishing=0.55 (below 0.60) → CURIOSITY"),
    (0.5, 0.5, 0.65, 0.55, 0.0, False, AffectState.CURIOSITY,  "flourishing=0.55 truth=0.65 → CURIOSITY"),
    (0.5, 0.5, 0.70, 0.55, 0.0, False, AffectState.CURIOSITY,  "truth=0.70 but flourishing=0.55 → CURIOSITY"),
    (0.5, 0.5, 0.74, 0.55, 0.0, False, AffectState.CURIOSITY,  "truth=0.74 flourishing=0.55 → CURIOSITY"),
    (0.5, 0.5, 0.50, 0.45, 0.0, False, AffectState.CURIOSITY,  "flourishing=0.45 → CURIOSITY"),
    (0.5, 0.5, 0.65, 0.45, 0.0, False, AffectState.CURIOSITY,  "truth=0.65 flourishing=0.45 → CURIOSITY"),
]

assert len(CASES) == 60, f"Expected 60 test cases, got {len(CASES)}"


# ---------------------------------------------------------------------------
# Parametrised regression test
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("I,W,T,F,CD,grief,expected,desc", CASES)
def test_waterfall_case(I, W, T, F, CD, grief, expected, desc):
    got = _infer(I, W, T, F, CD, grief)
    assert got == expected, (
        f"\n  [{desc}]\n"
        f"  inputs: I={I} W={W} T={T} F={F} CD={CD} grief={grief}\n"
        f"  expected={expected.value!r}, got={got.value!r}"
    )


# ---------------------------------------------------------------------------
# Macro-F1 gate (must be >= 0.75 across all six AffectState classes)
# ---------------------------------------------------------------------------

def test_macro_f1_gate():
    """Macro-F1 across all 60 cases must be >= 0.75."""
    y_true = [c[6] for c in CASES]
    y_pred = [_infer(*c[:6]) for c in CASES]

    tp: dict = defaultdict(int)
    fp: dict = defaultdict(int)
    fn: dict = defaultdict(int)

    for true, pred in zip(y_true, y_pred):
        if true == pred:
            tp[true] += 1
        else:
            fp[pred] += 1
            fn[true] += 1

    f1s = []
    for cls in AffectState:
        p = tp[cls] / (tp[cls] + fp[cls]) if (tp[cls] + fp[cls]) > 0 else 0.0
        r = tp[cls] / (tp[cls] + fn[cls]) if (tp[cls] + fn[cls]) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        f1s.append(f1)

    macro = sum(f1s) / len(f1s)
    assert macro >= 0.75, f"Macro-F1 = {macro:.4f} — below 0.75 gate"
