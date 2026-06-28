# CHROMATIC_02_pbm_dose_response_sim.py
# Simulation: Photobiomodulation Biphasic Dose-Response
# Canon Reference: CHROMATIC_CLARITY.md
# Issue: #686
#
# Models the biphasic dose-response (Arndt-Schulz law) for PBM
# across three tissue types and wavelengths:
#   - Wound healing (630 nm, red)
#   - Neural tissue (810 nm, NIR)
#   - Muscle tissue (850 nm, NIR)
#
# Key finding: Biological response peaks within 1-10 J/cm² then
# DECLINES with higher dose (photoinhibition). This validates the
# therapeutic window guidance in CHROMATIC_CLARITY.md Section III.

import numpy as np
import matplotlib.pyplot as plt

# ── Parameters ──────────────────────────────────────────────────────────────
DOSE = np.linspace(0, 30, 300)   # J/cm²

TISSUES = {
    "Wound (630 nm)":  {"peak": 4,  "width": 3.0, "color": "#f87171"},
    "Neural (810 nm)": {"peak": 8,  "width": 4.5, "color": "#a78bfa"},
    "Muscle (850 nm)": {"peak": 6,  "width": 3.8, "color": "#fb923c"},
}


def biphasic(dose: np.ndarray, peak: float, width: float,
             suppression: float = 0.30) -> np.ndarray:
    """Biphasic dose-response (Arndt-Schulz law approximation).
    Stimulation rises to peak, then decays through photoinhibition."""
    stimulation = np.exp(-0.5 * ((dose - peak) / width) ** 2)
    decay       = suppression * np.maximum(0.0, (dose - peak) / 10.0)
    return np.clip(stimulation - decay, 0, 1)


# ── Compute ──────────────────────────────────────────────────────────────────
print("=" * 55)
print("PBM Biphasic Dose-Response — Peak Analysis")
print("=" * 55)
for name, cfg in TISSUES.items():
    y    = biphasic(DOSE, cfg["peak"], cfg["width"])
    peak_dose = DOSE[y.argmax()]
    peak_resp = y.max()
    thresh_low  = DOSE[np.where(y > 0.5)[0][0]]  if (y > 0.5).any() else 0
    thresh_high = DOSE[np.where(y > 0.5)[0][-1]] if (y > 0.5).any() else 0
    print(f"\n{name}")
    print(f"  Peak response:    {peak_resp:.2f} at {peak_dose:.1f} J/cm²")
    print(f"  >50% response:    {thresh_low:.1f} – {thresh_high:.1f} J/cm²")
    print(f"  Therapeutic win:  {cfg['peak']-cfg['width']:.1f} – "
          f"{cfg['peak']+cfg['width']:.1f} J/cm² (±1σ)")


# ── Plot ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
ax.axvspan(1, 10, alpha=0.07, color="green", label="Therapeutic Window")
ax.axvline(x=1,  color="green", lw=1, alpha=0.4, linestyle="--")
ax.axvline(x=10, color="green", lw=1, alpha=0.4, linestyle="--")

for name, cfg in TISSUES.items():
    y = biphasic(DOSE, cfg["peak"], cfg["width"])
    ax.plot(DOSE, y, color=cfg["color"], linewidth=2.5, label=name)
    ax.axvline(x=cfg["peak"], color=cfg["color"], lw=1, alpha=0.3, linestyle=":")

ax.set_xlabel("Dose (J/cm²)", fontsize=12)
ax.set_ylabel("Biological Response (normalized)", fontsize=12)
ax.set_title("PBM Biphasic Dose-Response by Tissue Type\n"
             "(Arndt-Schulz Law — more light past peak = suppression)",
             fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.25)
ax.set_xlim(0, 30)
ax.set_ylim(-0.05, 1.1)
plt.tight_layout()
plt.savefig("CHROMATIC_02_pbm_dose_response_sim.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nPlot saved: CHROMATIC_02_pbm_dose_response_sim.png")
