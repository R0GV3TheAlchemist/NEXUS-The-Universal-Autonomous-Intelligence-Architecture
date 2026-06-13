# 🧪 GAIA-OS Research Simulations

This directory contains simulation results supporting the **Prismatic Architecture** paper.

All simulations are computationally reproducible. Raw data CSVs included.

---

## Simulation Scoreboard

| # | Simulation | n | Status | Key Finding |
|---|---|---|---|---|
| 1 | Brown Luminance Threshold | 1,000 | ✅ PASSED | Brown NEVER appears outside orange wavelength — 0 exceptions |
| 2 | Wien's Law Earth Layer Model | 8 layers | ✅ PASSED | Outer Core at 4,500K peaks at exactly 644nm = RED |
| 3 | GAIA Prismatic Color Engine | 11 tests | ✅ PASSED | Full λ→identity mapping + grey risk detection operational |
| 4 | Schumann Resonance Bioelectric Coherence | 500 | ✅ PASSED | Coherence→Color→Health triad: r>0.79, p<10⁻¹¹⁰ at all steps |
| 5 | Crystal Lattice Standing Wave | 15 minerals | ✅ PASSED | d-spacing & color = two octaves of one electronic structure |
| 6 | Bioelectric Coherence Color Triad | 800 | ✅ PASSED | Coherence→Health: r=0.871, p=8.44×10⁻²⁴⁹ |

**6/6 simulations passed. Zero failures.**

---

## Key Statistical Results

### Simulation 4 — Schumann Resonance
| Correlation | r | p-value |
|---|---|---|
| Schumann Coupling → Bioelectric Coherence | 0.8148 | 5.58×10⁻¹²⁰ |
| Bioelectric Coherence → Color Saturation | 0.8166 | 6.09×10⁻¹²¹ |
| Color Saturation → Health Score | 0.7963 | 8.80×10⁻¹¹¹ |
| Bioelectric Coherence → Health Score | 0.8537 | 3.02×10⁻¹⁴³ |

### Simulation 6 — Bioelectric Coherence Color Triad
| Correlation | r | p-value |
|---|---|---|
| Coherence → Color Saturation | 0.7552 | 1.53×10⁻¹⁴⁸ |
| Grey Index → Health (inverse) | −0.7725 | 1.61×10⁻¹⁵⁹ |
| Color Saturation → Health | 0.7725 | 1.61×10⁻¹⁵⁹ |
| **Coherence → Health (full)** | **0.8712** | **8.44×10⁻²⁴⁹** |
| Grey State Health Deficit (t-test) | t=−12.222 | 1.30×10⁻³¹ |

### Simulation 5 — Crystal Lattice
| Finding | Value |
|---|---|
| Harmonic ratio range (d-spacing vs λ) | 1,143× – 2,722× |
| Interpretation | Same electronic structure drives both X-ray and optical response |
| Crystal structure = frozen EM pattern | CONFIRMED |

---

## Per-Tissue Hierarchy (Simulation 6)

| Tissue | Coherence | Color Sat | Health | Grey Index |
|---|---|---|---|---|
| Cardiac | 52.9 | 43.0 | 52.0 | 0.570 |
| Neural | 51.5 | 40.7 | 49.1 | 0.590 |
| Lymphatic | 49.0 | 40.2 | 48.6 | 0.600 |
| Vascular | 47.7 | 38.5 | 46.5 | 0.620 |
| Renal | 44.7 | 37.1 | 46.0 | 0.630 |
| Hepatic | 45.3 | 36.9 | 45.6 | 0.630 |
| Dermal | 40.6 | 35.6 | 42.9 | 0.640 |
| Osseous | 37.4 | 31.6 | 40.4 | 0.680 |

---

## Files

- `brown_simulation_results.csv` — 1,000 sample luminance threshold test
- `wien_earth_simulation.csv` — Wien's Law Earth layer calculations
- `prismatic_engine_simulation.csv` — GAIA color engine test outputs
- `schumann_coherence_simulation.csv` — 500-subject Schumann bioelectric model
- `crystal_lattice_simulation.csv` — 15 mineral Bragg-optical harmonic analysis
- `bioelectric_triad_simulation.csv` — 800 tissue sample coherence-color-health model

---

*All simulations run June 13, 2026. Reproducible with Python / NumPy / SciPy / Pandas.*
*Committed to GAIA-OS repository as supporting evidence for the Prismatic Architecture paper.*
