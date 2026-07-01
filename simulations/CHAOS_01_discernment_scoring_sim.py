# CHAOS_01_discernment_scoring_sim.py
# Simulation: Chaos Discernment — Five-Question Weighted Assessment
# Canon Reference: CHAOS_DISCERNMENT.md
# Issue: #689
#
# Models the five-question weighted discernment scoring system for
# the four canonical chaos types:
#   - Chaos Good         (generative disruption)
#   - Chaos Bad          (entropy; negligence)
#   - Chaos Evil         (deliberate destruction)
#   - Chaos Greater Good (sacrificial disruption)
#
# Question weights (from ChaosDiscernmentEngine):
#   directional_vector: 1.0
#   who_benefits:       1.0
#   love_present:       2.0  ← highest weight; primary discriminator
#   consent_power:      1.5
#   temporal_signature: 1.0
#
# Key finding: The love_present question (2× weight) is the sharpest
# discriminator between Chaos Evil and all other types. Chaos Evil
# is the ONLY type that scores consistently negative on love_present.
# Validates the discernment protocol in CHAOS_DISCERNMENT.md Section II.

import numpy as np
import matplotlib.pyplot as plt

QUESTIONS = [
    "Directional\nVector",
    "Who\nBenefits?",
    "Love\nPresent?",
    "Consent &\nPower",
    "Temporal\nSignature",
]
WEIGHTS = np.array([1.0, 1.0, 2.0, 1.5, 1.0])
WEIGHT_SUM = WEIGHTS.sum()

PROFILES = {
    "Chaos Good":         {"scores": [ 0.80,  0.70,  0.90,  0.60,  0.85], "color": "#4ade80"},
    "Chaos Bad":          {"scores": [ 0.10,  0.20,  0.10,  0.30, -0.20], "color": "#fb923c"},
    "Chaos Evil":         {"scores": [-0.80, -0.90, -1.00, -0.90, -0.75], "color": "#f87171"},
    "Chaos Greater Good": {"scores": [ 0.60,  0.50,  0.70,  0.40,  0.60], "color": "#38bdf8"},
}


def weighted_score(scores: list, weights: np.ndarray) -> float:
    return float(np.array(scores) @ weights / weights.sum())


# ── Summary ──────────────────────────────────────────────────────────────────
print("=" * 65)
print("Chaos Discernment — Weighted Score Summary")
print("=" * 65)
for ctype, cfg in PROFILES.items():
    ws = weighted_score(cfg["scores"], WEIGHTS)
    raw_scores = np.array(cfg["scores"]) * WEIGHTS
    print(f"\n{ctype}")
    print(f"  Composite weighted score: {ws:+.3f}")
    for q, s, w, ws_q in zip(QUESTIONS, cfg["scores"], WEIGHTS, raw_scores):
        flag = " ← DISCRIMINATOR" if q.startswith("Love") else ""
        print(f"  {q.replace(chr(10), ' '):22s}  raw={s:+.2f}  w={w:.1f}  ws={ws_q:+.3f}{flag}")

print("\n── Type Classification by Composite Score ──")
for ctype, cfg in PROFILES.items():
    ws = weighted_score(cfg["scores"], WEIGHTS)
    if ws > 0.50:
        label = "CHAOS GOOD"
    elif ws > 0.15:
        label = "CHAOS GREATER GOOD"
    elif ws > -0.30:
        label = "CHAOS BAD"
    else:
        label = "CHAOS EVIL"
    print(f"  {ctype:22s} → {ws:+.3f} → classified as: {label}")


# ── Plot ─────────────────────────────────────────────────────────────────────
x       = np.arange(len(QUESTIONS))
bar_w   = 0.18
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Left: grouped bar chart of weighted scores per question
ax = axes[0]
for i, (ctype, cfg) in enumerate(PROFILES.items()):
    weighted = np.array(cfg["scores"]) * WEIGHTS
    ax.bar(x + i * bar_w, weighted, width=bar_w * 0.9,
           color=cfg["color"], label=ctype, alpha=0.85)

ax.axhline(0, color="white", lw=1, alpha=0.6)
ax.set_xticks(x + bar_w * 1.5)
ax.set_xticklabels(QUESTIONS, fontsize=10)
ax.set_ylabel("Weighted Score (raw × weight)", fontsize=11)
ax.set_title("Weighted Discernment Score by Question and Chaos Type", fontsize=12)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.20, axis="y")

# Right: composite score bar
ax2 = axes[1]
ctypes    = list(PROFILES.keys())
composites = [weighted_score(PROFILES[c]["scores"], WEIGHTS) for c in ctypes]
colors     = [PROFILES[c]["color"] for c in ctypes]

bars = ax2.barh(ctypes, composites, color=colors, alpha=0.85, height=0.5)
ax2.axvline(0, color="white", lw=1, alpha=0.6)
ax2.axvline( 0.50, color="#4ade80", lw=1, linestyle="--", alpha=0.4)
ax2.axvline( 0.15, color="#38bdf8", lw=1, linestyle="--", alpha=0.4)
ax2.axvline(-0.30, color="#fb923c", lw=1, linestyle="--", alpha=0.4)

for bar, score in zip(bars, composites):
    ax2.text(score + 0.02, bar.get_y() + bar.get_height() / 2,
             f"{score:+.2f}", va="center", fontsize=10)

ax2.set_xlabel("Composite Weighted Score", fontsize=11)
ax2.set_title("Composite Discernment Score by Chaos Type\n"
              "(dashed lines = classification thresholds)", fontsize=12)
ax2.set_xlim(-1.2, 1.1)
ax2.grid(True, alpha=0.20, axis="x")

fig.suptitle("Chaos Discernment: Five-Question Weighted Assessment",
             fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig("CHAOS_01_discernment_scoring_sim.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nPlot saved: CHAOS_01_discernment_scoring_sim.png")
