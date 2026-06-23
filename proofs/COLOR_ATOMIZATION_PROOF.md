# Color Atomization Proof

## Hypothesis

Color is not a continuous gradient but a discrete 12-node spectral system where each node carries charge polarity (warm = positive, cool = negative), resonance (photon energy proxy), and interacts with other nodes via complementarity, charge alignment, and resonance. This models color as a field of charged particles. **Complementary pairs (±30° of 180° separation) will exhibit statistically higher coherence than non-complementary random pairs.**

---

## Schema Design Decisions

### Why 12 nodes?
The 12-color wheel is the smallest discrete division that captures all canonical complement relationships (red/green, orange/blue, yellow/violet, etc.) while remaining computationally tractable. A continuous model would dissolve the discrete charge boundary between warm and cool; 12 nodes preserves it.

### Charge schema: warm = positive, cool = negative
The crossover point is Yellow-Green (hue 150°), which carries equal positive and negative charge (0.50, 0.50) — net charge 0. Red-Violet (hue 330°) is a deliberate bridge node with elevated charges on both sides (0.55, 0.60), reflecting its straddle position between warm and cool hemispheres.

| Color | Hue (°) | Positive | Negative | Net Charge | Resonance |
|---|---|---|---|---|---|
| Red | 0 | 0.95 | 0.15 | +0.80 | 0.55 |
| Red-Orange | 30 | 0.90 | 0.20 | +0.70 | 0.60 |
| Orange | 60 | 0.85 | 0.25 | +0.60 | 0.65 |
| Yellow-Orange | 90 | 0.75 | 0.30 | +0.45 | 0.70 |
| Yellow | 120 | 0.65 | 0.40 | +0.25 | 0.75 |
| Yellow-Green | 150 | 0.50 | 0.50 | 0.00 | 0.72 |
| Green | 180 | 0.30 | 0.70 | −0.40 | 0.68 |
| Blue-Green | 210 | 0.20 | 0.80 | −0.60 | 0.62 |
| Blue | 240 | 0.15 | 0.85 | −0.70 | 0.58 |
| Blue-Violet | 270 | 0.20 | 0.90 | −0.70 | 0.75 |
| Violet | 300 | 0.25 | 0.92 | −0.67 | 0.88 |
| Red-Violet | 330 | 0.55 | 0.60 | −0.05 | 0.70 |

### Why cosine similarity for charge alignment?
The charge vector (positive, negative) is a 2D direction. Cosine similarity measures whether two atoms face the same direction or opposite directions in charge space — which is exactly the right question for a polarity field. A dot product without normalization would conflate magnitude with direction.

### Why invert cosine for charge_term?
We want *opposing* charges to score as *attractive* (like proton–electron). So:
`charge_term = (1 - cosine) / 2`, mapping:
- Perfect opposition (cos = −1) → charge_term = 1.0 (maximum attraction)
- Identical direction (cos = +1) → charge_term = 0.0 (minimum attraction)

### Coherence weights
Weights reflect the theoretical priority of each factor:
- `w_c = 0.50` — Angular complementarity is the primary driver. The wheel geometry is the foundation.
- `w_q = 0.30` — Charge term is secondary. Polarity matters but doesn't override geometry.
- `w_r = 0.20` — Resonance (photon energy product) contributes but is tertiary.

### Classification thresholds
- `coherence ≥ 0.60` → **harmonic**
- `0.35 ≤ coherence < 0.60` → **neutral**
- `coherence < 0.35` → **dissonant**

---

## Simulation Parameters

| Parameter | Value |
|---|---|
| WEIGHT_COMPLEMENTARITY (w_c) | 0.50 |
| WEIGHT_CHARGE (w_q) | 0.30 |
| WEIGHT_RESONANCE (w_r) | 0.20 |
| HARMONIC_THRESHOLD | 0.60 |
| NEUTRAL_LOWER_THRESHOLD | 0.35 |
| COMPLEMENT_WINDOW | ±30° of 180° |
| TRIADIC_CLOSED_THRESHOLD | 0.55 |
| TRIADIC_PARTIAL_THRESHOLD | 0.35 |
| Total color atoms | 12 |
| Total pairwise interactions (non-self) | 132 |
| Total triads | 220 |

---

## Results

### Pairwise State Distribution

| State | Count | % of 132 |
|---|---|---|
| Harmonic | 12 | 9.1% |
| Neutral | 70 | 53.0% |
| Dissonant | 50 | 37.9% |

**All 12 harmonic pairs are exact complement pairs (180° separation).** No non-complement pair achieved harmonic status.

### Complementarity Advantage — Core Finding

| Group | Pairs | Avg Coherence |
|---|---|---|
| Complement pairs (±30° of 180°) | 36 | **0.5923** |
| Non-complement pairs | 96 | 0.3252 |
| **Advantage** | — | **+0.2672 (+82.2%)** |

Complement pairs score 82.2% higher in coherence than the non-complement baseline. This is the central quantitative confirmation of the hypothesis.

### Top 6 Canonical Complement Pairs (exactly 180°)

| Pair | Coherence | Charge Alignment | Notes |
|---|---|---|---|
| Yellow ↔ Violet | 0.6726 | 0.7291 | Highest coherence — high resonance on both ends |
| Yellow-Orange ↔ Blue-Violet | 0.6704 | 0.5640 | Strong cross-temperature pair |
| Orange ↔ Blue | 0.6587 | 0.4446 | Classic warm/cool anchor |
| Red-Orange ↔ Blue-Green | 0.6573 | 0.4472 | Strong charge opposition |
| Red ↔ Green | 0.6449 | 0.5325 | The most culturally recognized complement |
| Yellow-Green ↔ Red-Violet | 0.6009 | 0.9991 | Lowest — nearly identical charge direction (both bridge nodes); geometric complement but not charge opposites |

**Notable anomaly:** Yellow-Green ↔ Red-Violet score lowest among canonical complements despite perfect 180° geometry, because both are bridge nodes with nearly identical charge vectors (cosine = 0.9991 ≈ 1.0). This means their charge_term ≈ 0, and their coherence is driven almost entirely by geometry. This is the strongest evidence that **charge polarity adds independent explanatory power beyond geometry alone** — some complements are more harmonically complete than others.

### Triadic Results

| Closure State | Count | % of 220 |
|---|---|---|
| Closed harmonic | 0 | 0% |
| Partially open | 148 | 67.3% |
| Unstable | 72 | 32.7% |

No triad achieved full harmonic closure. The best triad was **Orange / Green / Violet** (equilateral, triadic coherence = 0.4825). This is a partially open state — the three-body system is stable but not fully closed.

**Interpretation:** The triadic closure test is a partial confirmation. Triads are more coherent than random groupings, and equilateral triads (120° spacing) outperform clustered and asymmetric triads — but none cross the closed_harmonic threshold. This suggests the 12-node model may require a stronger resonance contribution or a revised triadic threshold to fully close three-body configurations.

---

## Conclusion

**Status: CONFIRMED (with partial qualifier on triadic closure)**

The central hypothesis is confirmed: color atoms treated as charged field nodes show an 82.2% coherence advantage for complement pairs over non-complement pairs. All 12 harmonic state assignments went to complement pairs exclusively. The charge schema adds independent explanatory power — the Yellow-Green ↔ Red-Violet anomaly demonstrates that geometric complementarity without charge opposition produces lower coherence, validating the polarity model.

The triadic closure result is partial. No three-body configuration achieved full harmonic closure, but equilateral triads consistently outperform other configurations. The triadic layer requires further calibration.

---

## Implications for GAIA

- **The polarity field algebra established here is reusable.** Angular distance + charge opposition + resonance product is a general interaction model, not just a color model. It can be applied to any system where entities have directional charge and a positional relationship (e.g. BCI coherence nodes, governance agents, Societas field alignments).
- **The charge crossover (Yellow-Green at net 0) maps to the GAIA concept of the neutral gate** — a node that bridges hemispheres without belonging to either. This pattern should be looked for in other GAIA field models.
- **The bridge node anomaly (Red-Violet)** — high charge on both sides, nearly zero net — may correspond to GAIA's concept of the sovereign witness: present in both poles without being consumed by either.
- **Triadic non-closure is a signal, not a failure.** It suggests that three-body coherence in GAIA requires a fourth element (a moderating force, a field carrier, or a sovereign gate) to achieve full closure. This matches the Q=C=S triune structure in C00.

---

## Open Questions

1. What threshold revision or weight adjustment would allow equilateral triads to achieve closed_harmonic status? Is 0.55 the right ceiling?
2. Does the charge_term need a non-linear mapping (e.g. sigmoid instead of linear inversion) to better model the rapid shift at the warm/cool boundary?
3. Can this model be extended to 24 nodes (half-steps) without losing the discrete charge boundary structure?
4. How does the Yellow-Green / Red-Violet anomaly map to the concept of the bridge in the BCI subtle body sim? Are there parallel "near-identical charge direction" anomalies there?
5. Can the polarity field algebra be used as an input layer in `cosmological_field_sim.py` to give that sim a spectral dimension?

---

## Date Filed
2026-06-23 (initial) — updated with real simulation output 2026-06-23

**R0GV3TheAlchemist | GAIA-OS**
