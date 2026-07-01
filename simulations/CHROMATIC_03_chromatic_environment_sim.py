# CHROMATIC_03_chromatic_environment_sim.py
# Simulation: Chromatic Clarity Score Across 24 Hours (4 Scenarios)
# Canon Reference: CHROMATIC_CLARITY.md
# Issue: #686
#
# Models the chromatic clarity score (0–1) across a full 24-hour day
# for four lifestyle scenarios:
#   (a) Full Optical Hygiene
#   (b) Office Worker (minimal outdoor exposure)
#   (c) Shift Worker (inverted light cycle)
#   (d) Balanced Mixed Practice
#
# Key finding: The clarity gap between optimal hygiene and office/shift
# patterns exceeds 0.40 at peak hours, quantifying the cost of
# light environment neglect.

import numpy as np
import matplotlib.pyplot as plt

HOURS = np.linspace(0, 24, 289)

SCENARIOS = {
    "Full Optical Hygiene": {"color": "#38bdf8"},
    "Office Worker":        {"color": "#fb923c"},
    "Shift Worker":         {"color": "#f87171"},
    "Balanced Mixed":       {"color": "#4ade80"},
}


def chromatic_clarity(h: np.ndarray, scenario: str) -> np.ndarray:
    if scenario == "Full Optical Hygiene":
        morning   = np.exp(-0.5 * ((h - 8.0)  / 1.5) ** 2) * 0.95
        midday    = np.exp(-0.5 * ((h - 12.0) / 2.5) ** 2) * 1.00
        afternoon = np.exp(-0.5 * ((h - 15.5) / 2.0) ** 2) * 0.85
        evening   = np.exp(-0.5 * ((h - 19.0) / 1.5) ** 2) * 0.75
        night     = np.where(h > 22, 0.80, 0.0)
        return np.clip(morning + midday + afternoon + evening + night, 0, 1)
    elif scenario == "Office Worker":
        base    = np.where((h >= 9) & (h <= 18), 0.45, 0.20)
        penalty = np.where(h > 20, -0.25 * (h - 20) / 4, 0.0)
        return np.clip(base + penalty, 0, 1)
    elif scenario == "Shift Worker":
        return np.clip(np.where((h >= 22) | (h <= 6), 0.30, 0.15), 0, 1)
    else:  # Balanced Mixed
        base    = np.where((h >= 7) & (h <= 20), 0.60, 0.35)
        penalty = np.where(h > 21, -0.10 * (h - 21), 0.0)
        return np.clip(base + penalty, 0, 1)


# ── Compute & summarize ──────────────────────────────────────────────────────
print("=" * 55)
print("Chromatic Clarity — Daily Score Summary")
print("=" * 55)
for sc in SCENARIOS:
    y = chromatic_clarity(HOURS, sc)
    print(f"\n{sc}")
    print(f"  Mean score:    {y.mean():.3f}")
    print(f"  Peak score:    {y.max():.3f} at {HOURS[y.argmax()]:.1f}h")
    print(f"  Low score:     {y.min():.3f}")
    print(f"  Time >0.60:    {(y > 0.60).mean() * 24:.1f}h/day")


# ── Plot ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))

for sc, cfg in SCENARIOS.items():
    y = chromatic_clarity(HOURS, sc)
    ax.plot(HOURS, y, color=cfg["color"], linewidth=2.5, label=sc)

# Time-of-day background shading
ax.axvspan(0,   6,  alpha=0.04, color="navy")
ax.axvspan(6,  10,  alpha=0.04, color="yellow")
ax.axvspan(10, 14,  alpha=0.04, color="orange")
ax.axvspan(14, 18,  alpha=0.04, color="lightgreen")
ax.axvspan(18, 21,  alpha=0.04, color="salmon")
ax.axvspan(21, 24,  alpha=0.04, color="navy")

ax.set_xticks(range(0, 25, 3))
ax.set_xticklabels(["12am","3am","6am","9am","12pm","3pm","6pm","9pm","12am"])
ax.set_xlabel("Hour of Day", fontsize=12)
ax.set_ylabel("Chromatic Clarity Score (0–1)", fontsize=12)
ax.set_title("Chromatic Clarity Score Across 24 Hours\n"
             "GAIA-OS optical hygiene protocol vs real-world scenarios",
             fontsize=13)
ax.legend(fontsize=10, loc="upper left")
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.20)
plt.tight_layout()
plt.savefig("CHROMATIC_03_chromatic_environment_sim.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nPlot saved: CHROMATIC_03_chromatic_environment_sim.png")
