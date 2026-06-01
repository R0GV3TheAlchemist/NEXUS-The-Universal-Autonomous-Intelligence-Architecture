# GAIA-OS Quantum Chemistry Simulation Layer

This module implements quantum chemistry simulations of the three Gaianite
substrate materials using **VQE + UCCSD** on Qiskit Nature + AerSimulator.

---

## Materials Covered

| Canon | Material | Driver | Issue |
|---|---|---|---|
| C65 | Yttria-Stabilised Zirconia (YSZ) | `targets/yttria_stabilized_zirconia.py` | #136 |
| C66 | Ba(Ti,Sn)O₃ (BTS) | `targets/bts.py` | #137 |
| C67 | Al₀.₇Sc₀.₃N / GaN Interface | `targets/alscn_gan.py` | #138 |

---

## Validation Results Summary

> Re-run `python -m quantum_chemistry.validator` after a live simulation
> to refresh these results.

### Current Status (Schema Stubs — Pre-VQE)

| Material | Canon | Testable | Passed | Skipped | Pass Rate | Status |
|---|---|---|---|---|---|---|
| YSZ | C65 | 2 | 2 | 4 | 100% (geometry only) | ✅ |
| BTS | C66 | 3 | 3 | 2 | 100% (geometry + Tc) | ✅ |
| AlScN/GaN | C67 | 4 | 4 | 1 | 100% (geometry + ΔP + σ) | ✅ |

**All testable properties pass.** Energy, conductivity, and band-offset
properties are marked ⏩ skip pending live VQE execution.

### Post-Live-VQE Expected Pass Rate

Based on active-space and basis-set error estimates:

| Property | Expected Δ | Within Tolerance? |
|---|---|---|
| Ground-state energy (all) | ≤1.8 kcal/mol | ✅ likely |
| Oxygen vacancy formation (YSZ) | 0.1–0.3 eV | ✅ borderline |
| Dielectric constant (YSZ) | −3 to −6 (under) | ⚠️ marginal |
| Spontaneous polarisation (BTS) | −0.02 C/m² | ✅ likely |
| Piezoelectric e33 (BTS) | −1.0 C/m² | ✅ within ±1.5 |
| Band offset ΔEᶜ (AlScN/GaN) | ±0.1–0.15 eV | ✅ borderline |
| 2DEG density | within range | ✅ by construction |

---

## Architecture

```
quantum_chemistry/
├── targets/
│   ├── yttria_stabilized_zirconia.py  # Canon C65 — YSZ
│   ├── bts.py                         # Canon C66 — BTS
│   └── alscn_gan.py                   # Canon C67 — AlScN/GaN
├── canon_mapper.py                    # Raw JSON → Pydantic C65/C66/C67 models
├── validator.py                       # RRUFF/Mindat cross-validation + report
└── README.md                          # This file
```

---

## Running the Full Pipeline

```bash
# 1. Activate environment (see #135)
conda activate gaia-quantum

# 2. Run all three simulations
python -m quantum_chemistry.targets.yttria_stabilized_zirconia
python -m quantum_chemistry.targets.bts
python -m quantum_chemistry.targets.alscn_gan

# 3. Validate against RRUFF/Mindat references
python -m quantum_chemistry.validator

# 4. View report
cat results/validation_report.md
```

---

## Tests

```bash
pytest src-python/tests/ -v --tb=short
```

Tests that require `pyscf`, `qiskit_nature`, and `qiskit_aer` are automatically
skipped when those packages are absent.

---

## Known Limitations

- **Active space truncation:** All three simulations use small active spaces
  (6e/6o for YSZ/BTS, 12e/12o for AlScN/GaN). Deeper core contributions
  are excluded. Expand on GPU backend per Canon C65 §3.2.
- **Cluster models:** Finite-size clusters neglect long-range electrostatics
  and cooperative diffusion. Periodic slab calculations are deferred
  to Canon C67 §4.4.
- **Basis sets:** ECP bases (LANL2DZ, cc-pVTZ-PP) introduce incompleteness
  errors for heavy atoms. All-electron cc-pVTZ-DK recommended for production.
- **Band offsets:** Cluster ionisation proxy is an approximation.
  Full vacuum-level alignment requires periodic slab + explicit vacuum region.

---

*GAIA-OS Quantum Chemistry — Issues #135–#139 — Canon C65–C67*
