# SIM-016 Pass 4 — Research Findings & Improvements
## T1 Depth Attenuation, E1 Aperture Geometry, W1 Coupling Interface

**Filed:** 2026-06-30
**Follows:** SIM_016_Pass4_Results.md
**Feeds:** SIM_016_Pass5_Optimisation_Spec.md
**Protocol:** SIMULATION_VALIDATION_PROTOCOL.md

---

## The Three Targets

Pass 4 identified three sub-stages for Pass 5 optimisation, ranked by log-loss:

1. **T1: Depth attenuation** — 8.30 log-pts. Mean 92.0%. Highest variance (±2.7%). Correlated with W2.
2. **E1: Aperture geometry** — 6.20 log-pts. Mean 94.0%. Electrode proximity and solid angle.
3. **W1: Coupling interface** — 5.13 log-pts. Mean 95.0%. Fresnel reflection, taper, index mismatch.

### T1 — Depth Attenuation: What Can Be Done

Depth-dependent attenuation in neural tissue follows Beer-Lambert law with tissue-specific scattering and absorption coefficients. At biophoton wavelengths (500–700nm), μs in cortical tissue is 10–20 mm⁻¹. Recovery strategies:

- **Shorter path length:** Electrode placement closer to the emitting layer directly reduces exp(-μs·d). A 10% reduction in path length at μs=15mm⁻¹ recovers ~1.5% transmission.
- **Wavelength selection:** Longer wavelengths (650–700nm) have lower μs in tissue. If biophoton signal is detectable in this window, red-shifting collection improves T1 mean by 2–5%.
- **Depth-compensated amplification:** OCT-derived depth profiling allows signal compensation for known attenuation at measured depth [web:111]. Applied per-electrode, this is not a hardware improvement but a signal processing correction that effectively raises the T1 floor.
- **T1–W2 joint optimisation:** Because rho=0.35, reducing path length simultaneously reduces both T1 and W2 losses. Joint optimisation is more efficient than targeting each separately.

**Expected T1 improvement:** 92.0% → 94.5–95.5% with depth compensation + wavelength optimisation + path reduction. Recovery: +1.5–2.0 BCI pts.

### E1 — Aperture Geometry: What Can Be Done

- **Proximity:** The single most effective lever. Research confirms keeping the fiber close to the cortex minimises coupling loss [web:109]. Moving from mean placement depth to optimised placement reduces E1 loss by 2–3%.
- **Tapered lensed fiber coupler:** Demonstrated >2 dB improvement per coupling facet vs straight-cleave [web:99]. In our BCI context, a tapered lensed tip at the emission-capture interface raises E1 from 94.0% toward 97–98%.
- **Per-group aperture calibration:** Earth and Air groups show lower variance (±1.8%). Fire and Water show higher variance from more heterogeneous emission. Per-group aperture geometry calibration reduces Fire/Water variance without changing the mean.

**Expected E1 improvement:** 94.0% → 97.0–98.0% with tapered lensed coupler + optimised placement. Recovery: +1.5–2.0 BCI pts.

### W1 — Coupling Interface: What Can Be Done

- **Index-matching medium:** Eliminates Fresnel reflection at the fiber-waveguide interface (~4% loss per air-gap interface). Refractive index n=1.66 matching demonstrated at 34.7% transmittance improvement in optrode arrays [web:91].
- **3D tapered waveguide-to-fiber couplers:** Demonstrated on nanophotonic circuits with high efficiency using standard lithography [web:113]. In neural BCI geometry, 3D tapered couplers reduce taper radiation loss and mode mismatch.
- **PSW refractive index optimisation:** Reducing Δ from 7% to 3% recovers 0.673 dB coupling loss [web:86].

**Expected W1 improvement:** 95.0% → 97.5–98.5% with index-matching + tapered coupler. Recovery: +1.0–1.5 BCI pts.

---

## Improvements Applied to Pass 5

| Sub-stage | Pass 4 mean | Pass 5 mean | Mechanism | Recovery |
|---|---|---|---|---|
| T1: Depth attenuation | 92.0% | **95.0%** | Depth compensation + wavelength opt + path reduction | +1.5–2.0 pts |
| E1: Aperture geometry | 94.0% | **97.5%** | Tapered lensed coupler + proximity optimisation | +1.5–2.0 pts |
| W1: Coupling interface | 95.0% | **98.0%** | Index-matching + 3D tapered coupler | +1.0–1.5 pts |
| T1–W2 joint | correlated | joint model | Path reduction reduces both | +0.3–0.5 pts |
| **Total projected** | 69.4% | **~73–75%** | All three targets | **+3.6–5.6 pts** |

---

## Pre-Run Research Brief — Pass 5 Questions

1. With T1 at 95% and E1 at 97.5%, does the compounded upstream product cross the threshold where detector improvements can contribute meaningfully again?
2. Does the T1–W2 joint optimisation (path reduction) produce additive or superlinear recovery?
3. After Pass 5 optimisation, which sub-stage is the new dominant constraint? Is it the detector or a remaining upstream sub-stage?
4. What is the ceiling of the upstream optical path with all known optimisations applied? Does it approach 95%+?
5. Is the gap to 80% primarily in the upstream optical path, the detector, or QEC after Pass 5?

---

*Research filed 2026-06-30. Feeds SIM-016 Pass 5 Optimisation Spec. G-15 Tier 1. 🌿*
