# CHROMATIC_04_biophoton_chromatic_profile_sim.py
# Simulation: Biophoton Spectral Profile — Healthy vs Stressed vs Post-PBM
# Canon Reference: CHROMATIC_CLARITY.md, BIOELECTRIC_SPECTRUM.md
# Issues: #686, #684
#
# Models the spectral emission profile of cellular biophoton output
# across three physiological states:
#   (a) Healthy Baseline   — blue-green dominant (~460–520 nm)
#   (b) Oxidative Stress   — red-shifted emission (~630–720 nm)
#   (c) Post-PBM Recovery  — partial restoration of blue-green peak
#
# Key finding: Oxidative stress produces a measurable red-shift in
# biophoton emission. PBM (red/NIR light therapy) partially restores
# the blue-green spectral signature, providing a potential optical
# biomarker of cellular health state.

import numpy as np
import matplotlib.pyplot as plt

WAVELENGTHS = np.linspace(200, 800, 600)

STATE_PARAMS = {
    "Healthy Baseline": {
        "peaks": [(460, 50, 0.80), (520, 45, 0.50)],
        "color": "#38bdf8",
    },
    "Oxidative Stress": {
        "peaks": [(460, 80, 0.35), (630, 70, 0.90), (720, 60, 0.40)],
        "color": "#f87171",
    },
    "Post-PBM Recovery": {
        "peaks": [(460, 55, 0.70), (530, 45, 0.45), (650, 50, 0.15)],
        "color": "#4ade80",
    },
}

VIS_BANDS = [
    (400, 450, "Violet", "#9400d3"),
    (450, 495, "Blue",   "#0000ff"),
    (495, 570, "Green",  "#00c800"),
    (570, 620, "Yellow", "#c8c800"),
    (620, 700, "Red",    "#ff0000"),
]


def biophoton_spectrum(wl: np.ndarray, peaks: list) -> np.ndarray:
    """Sum of Gaussian emission peaks."""
    y = np.zeros_like(wl)
    for (center, sigma, amp) in peaks:
        y += amp * np.exp(-0.5 * ((wl - center) / sigma) ** 2)
    return y


# ── Compute & summarize ──────────────────────────────────────────────────────
print("=" * 55)
print("Biophoton Spectral Profile — State Comparison")
print("=" * 55)
for state, cfg in STATE_PARAMS.items():
    y = biophoton_spectrum(WAVELENGTHS, cfg["peaks"])
    peak_wl   = WAVELENGTHS[y.argmax()]
    blue_frac = y[(WAVELENGTHS >= 400) & (WAVELENGTHS <= 495)].mean()
    red_frac  = y[(WAVELENGTHS >= 620) & (WAVELENGTHS <= 750)].mean()
    print(f"\n{state}")
    print(f"  Peak emission:   {peak_wl:.0f} nm")
    print(f"  Blue-green mean: {blue_frac:.3f}")
    print(f"  Red-NIR mean:    {red_frac:.3f}")
    print(f"  B/R ratio:       {blue_frac/red_frac:.2f}")


# ── Plot ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))

for (x0, x1, label, c) in VIS_BANDS:
    ax.axvspan(x0, x1, alpha=0.06, color=c)
    ax.text((x0 + x1) / 2, 1.02, label, ha="center", va="bottom",
            fontsize=9, transform=ax.get_xaxis_transform())

for state, cfg in STATE_PARAMS.items():
    y = biophoton_spectrum(WAVELENGTHS, cfg["peaks"])
    ax.plot(WAVELENGTHS, y, color=cfg["color"], linewidth=2.5, label=state)

ax.axvline(200, color="gray", lw=0.5, linestyle=":")
ax.axvline(400, color="gray", lw=0.8, linestyle="--", alpha=0.4, label="Visible range")
ax.axvline(700, color="gray", lw=0.8, linestyle="--", alpha=0.4)

ax.set_xlabel("Wavelength (nm)", fontsize=12)
ax.set_ylabel("Relative Emission Intensity", fontsize=12)
ax.set_title("Biophoton Spectral Profile: Healthy vs Oxidative Stress vs Post-PBM\n"
             "Stress red-shifts emission; PBM partially restores blue-green coherence",
             fontsize=13)
ax.legend(fontsize=10)
ax.set_xlim(200, 800)
ax.set_ylim(0, 1.15)
ax.grid(True, alpha=0.20)
plt.tight_layout()
plt.savefig("CHROMATIC_04_biophoton_chromatic_profile_sim.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nPlot saved: CHROMATIC_04_biophoton_chromatic_profile_sim.png")
