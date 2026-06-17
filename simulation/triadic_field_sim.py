"""
simulation/triadic_field_sim.py

Queue 2 simulation scaffold.

Renders four layers:
  1. Electronic field  — sinusoidal / propagating interaction pattern
  2. Protonic field    — centered coherence well
  3. Neutronic field   — distributed stabilizing substrate
  4. Meta-field        — weighted superposition of all three

This is a computational visualization scaffold, not a physical proof.

Outputs:
  - simulation/output/triadic_field_snapshot.csv
  - simulation/output/triadic_field_snapshot.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path("simulation/output")
OUT.mkdir(parents=True, exist_ok=True)

# Domain
n = 160
x = np.linspace(-4.0, 4.0, n)
y = np.linspace(-4.0, 4.0, n)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
TH = np.arctan2(Y, X)

# Electronic field: oscillatory and propagating
E = np.sin(2.4 * X) * np.cos(2.0 * Y) * np.exp(-0.08 * R**2)

# Protonic field: centered coherence / identity well
P = np.exp(-0.55 * R**2)

# Neutronic field: neutral substrate / damping lattice
N = 0.55 * np.exp(-0.12 * R**2) + 0.15 * np.cos(3 * TH) * np.exp(-0.25 * R**2)

# Meta-field: weighted superposition
M = 0.45 * E + 0.35 * P + 0.20 * N

# Export a compact table for inspection
sample = pd.DataFrame(
    {
        "x": X.ravel(),
        "y": Y.ravel(),
        "electronic": E.ravel(),
        "protonic": P.ravel(),
        "neutronic": N.ravel(),
        "meta": M.ravel(),
    }
)
sample.to_csv(OUT / "triadic_field_snapshot.csv", index=False)

# Plot
fig, axes = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
fig.patch.set_facecolor("#08111f")
plots = [
    (E, "Electronic Field", "magma"),
    (P, "Protonic Field", "viridis"),
    (N, "Neutronic Field", "cividis"),
    (M, "Meta-Field", "plasma"),
]

for ax, (field, title, cmap) in zip(axes.flat, plots):
    im = ax.imshow(field, extent=[x.min(), x.max(), y.min(), y.max()], origin="lower", cmap=cmap)
    ax.set_title(title, color="white", fontsize=12)
    ax.set_xlabel("x", color="#cbd5e1")
    ax.set_ylabel("y", color="#cbd5e1")
    ax.tick_params(colors="#94a3b8")
    ax.set_facecolor("#0f172a")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.yaxis.set_tick_params(color="#94a3b8")
    plt.setp(cb.ax.get_yticklabels(), color="#cbd5e1")

fig.suptitle("GAIA Queue 2 — Triadic Field Simulation Scaffold", color="white", fontsize=16)
fig.savefig(OUT / "triadic_field_snapshot.png", dpi=180, facecolor=fig.get_facecolor())
print(f"Wrote: {OUT / 'triadic_field_snapshot.csv'}")
print(f"Wrote: {OUT / 'triadic_field_snapshot.png'}")
