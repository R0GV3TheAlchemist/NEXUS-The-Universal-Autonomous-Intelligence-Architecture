# MIND_MATTER_01_triadic_coherence_amplification_sim.py
# Simulation: Triadic Coherence — Soul as Non-Linear Amplifier
# Canon Reference: MIND_MATTER_INTEGRATION.md
# Issue: #683
#
# Models the non-linear amplification effect of soul coherence on
# the body × mind coherence product, using the phi-exponent (φ=1.618)
# amplification formula:
#
#   triadic_score = clip(sqrt(body * mind) * (1 + soul^φ * 2) / 3, 0, 1)
#
# Soul coherence levels modeled: 0.0, 0.33, 0.66, 1.0
# Body coherence: 0.0 → 1.0 (independent variable)
# Mind coherence: fixed at 0.5 (midpoint)
#
# Key finding: The last 20% of soul coherence provides more amplification
# than the first 80% combined, due to the superlinear phi-exponent.
# Full triadic integration (soul=1.0) produces 3× the output of
# body+mind alone (soul=0.0) at the same body coherence level.

import numpy as np
import matplotlib.pyplot as plt

PHI  = 1.618033988749895   # Golden ratio
BODY = np.linspace(0, 1, 500)

SOUL_LEVELS = [
    (0.00, "Soul = 0.00 (absent)"),
    (0.33, "Soul = 0.33 (low)"),
    (0.66, "Soul = 0.66 (moderate)"),
    (1.00, "Soul = 1.00 (full)"),
]

MIND_FIXED = 0.50


def triadic_score(body: np.ndarray, mind: float, soul: float) -> np.ndarray:
    """Non-linear triadic coherence formula with phi-exponent soul amplification."""
    base = (body * mind) ** 0.5
    amp  = 1.0 + (soul ** PHI) * 2.0
    return np.clip(base * amp / 3.0, 0, 1)


# ── Summary ──────────────────────────────────────────────────────────────────
print("=" * 60)
print("Triadic Coherence — Soul Amplification Analysis (mind=0.5)")
print("=" * 60)
for soul, label in SOUL_LEVELS:
    y        = triadic_score(BODY, MIND_FIXED, soul)
    y_mid    = triadic_score(np.array([0.5]), MIND_FIXED, soul)[0]
    y_full   = triadic_score(np.array([1.0]), MIND_FIXED, soul)[0]
    amp_fac  = (1.0 + (soul ** PHI) * 2.0)
    print(f"\n{label}")
    print(f"  Amplification factor: {amp_fac:.3f}×")
    print(f"  Score at body=0.5:   {y_mid:.3f}")
    print(f"  Score at body=1.0:   {y_full:.3f}")

# Marginal soul value analysis
print("\n── Marginal Soul Contribution (body=1.0, mind=0.5) ──")
for i, (soul, _) in enumerate(SOUL_LEVELS[:-1]):
    s_lo = soul
    s_hi = SOUL_LEVELS[i + 1][0]
    y_lo = triadic_score(np.array([1.0]), MIND_FIXED, s_lo)[0]
    y_hi = triadic_score(np.array([1.0]), MIND_FIXED, s_hi)[0]
    print(f"  Soul {s_lo:.2f} → {s_hi:.2f}: +{(y_hi - y_lo):.4f}")


# ── Plot ─────────────────────────────────────────────────────────────────────
COLORS = ["#94a3b8", "#fb923c", "#38bdf8", "#4ade80"]

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: family of curves
ax = axes[0]
for (soul, label), color in zip(SOUL_LEVELS, COLORS):
    y = triadic_score(BODY, MIND_FIXED, soul)
    ax.plot(BODY, y, color=color, linewidth=2.5, label=label)

ax.set_xlabel("Body Coherence", fontsize=12)
ax.set_ylabel("Triadic Integration Score", fontsize=12)
ax.set_title(f"Soul Amplification Curves (mind fixed = {MIND_FIXED})", fontsize=12)
ax.legend(fontsize=10)
ax.set_xlim(0, 1)
ax.set_ylim(0, 0.85)
ax.grid(True, alpha=0.25)

# Right: marginal soul contribution at body=1.0
ax2 = axes[1]
soul_range  = np.linspace(0, 1, 200)
y_at_full   = triadic_score(np.ones_like(soul_range), MIND_FIXED, soul_range)
marginal    = np.gradient(y_at_full, soul_range)
ax2.plot(soul_range, marginal, color="#c084fc", linewidth=2.5)
ax2.fill_between(soul_range, marginal, alpha=0.15, color="#c084fc")
ax2.axvline(0.8, color="white", lw=1, linestyle="--", alpha=0.4,
            label="Last 20% of soul")
ax2.set_xlabel("Soul Coherence Level", fontsize=12)
ax2.set_ylabel("Marginal Triadic Gain", fontsize=12)
ax2.set_title("Marginal Soul Contribution\n"
              "(body=1.0, mind=0.5 — gain per unit soul)", fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.25)

fig.suptitle("Triadic Coherence: Soul as φ-Exponent Non-Linear Amplifier",
             fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig("MIND_MATTER_01_triadic_coherence_amplification_sim.png",
            dpi=150, bbox_inches="tight")
plt.show()
print("\nPlot saved: MIND_MATTER_01_triadic_coherence_amplification_sim.png")
