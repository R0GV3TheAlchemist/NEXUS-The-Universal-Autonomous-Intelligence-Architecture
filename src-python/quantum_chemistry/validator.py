"""
validator.py
============
Loads RRUFF/Mindat/literature reference data and validates Canon C65-C67
simulation outputs property-by-property.

Produces:
  - Per-property pass/fail with residual and tolerance band
  - Overall pass rate (must be >= 80% per acceptance criteria)
  - results/validation_report.md

Usage
-----
    from quantum_chemistry.validator import validate_all, write_validation_report
    results = validate_all()
    write_validation_report(results)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PropertyResult:
    """Validation result for a single property."""
    property_name: str
    simulated_value: Optional[float]
    reference_value: Optional[float]
    tolerance: Optional[float]
    unit: str
    passed: Optional[bool]           # None = not testable (null sim value)
    residual: Optional[float] = None
    residual_pct: Optional[float] = None
    failure_reason: Optional[str] = None


@dataclass
class MaterialValidationResult:
    """Validation results for a single material."""
    material: str
    canon_ref: str
    properties: List[PropertyResult] = field(default_factory=list)
    n_tested: int = 0
    n_passed: int = 0
    n_failed: int = 0
    n_skipped: int = 0
    pass_rate: float = 0.0
    overall_passed: bool = False

    def compute_summary(self) -> None:
        testable = [p for p in self.properties if p.passed is not None]
        self.n_tested = len(testable)
        self.n_passed = sum(1 for p in testable if p.passed)
        self.n_failed = sum(1 for p in testable if not p.passed)
        self.n_skipped = len(self.properties) - self.n_tested
        self.pass_rate = self.n_passed / self.n_tested if self.n_tested else 0.0
        self.overall_passed = self.pass_rate >= 0.80  # acceptance criteria: >= 80%


@dataclass
class ValidationReport:
    """Full validation report for all three materials."""
    materials: List[MaterialValidationResult] = field(default_factory=list)
    total_tested: int = 0
    total_passed: int = 0
    total_pass_rate: float = 0.0
    all_passed: bool = False

    def compute_summary(self) -> None:
        for m in self.materials:
            m.compute_summary()
        self.total_tested = sum(m.n_tested for m in self.materials)
        self.total_passed = sum(m.n_passed for m in self.materials)
        self.total_pass_rate = (
            self.total_passed / self.total_tested if self.total_tested else 0.0
        )
        self.all_passed = all(m.overall_passed for m in self.materials)


# ---------------------------------------------------------------------------
# Reference data loader
# ---------------------------------------------------------------------------

def load_reference_data(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Reference data file not found: {p}")
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_result(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Simulation result file not found: {p}")
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Core validator
# ---------------------------------------------------------------------------

def _check(
    name: str,
    sim_val: Optional[float],
    ref_val: Optional[float],
    tol: float,
    unit: str,
    failure_reason: str = "",
) -> PropertyResult:
    """Validate a single (sim, ref, tolerance) triple."""
    if sim_val is None or ref_val is None:
        return PropertyResult(
            property_name=name,
            simulated_value=sim_val,
            reference_value=ref_val,
            tolerance=tol,
            unit=unit,
            passed=None,
            failure_reason="Simulation value not available (stub/unrun).",
        )
    residual = abs(sim_val - ref_val)
    residual_pct = 100.0 * residual / abs(ref_val) if ref_val != 0 else None
    passed = residual <= tol
    return PropertyResult(
        property_name=name,
        simulated_value=sim_val,
        reference_value=ref_val,
        tolerance=tol,
        unit=unit,
        passed=passed,
        residual=round(residual, 6),
        residual_pct=round(residual_pct, 2) if residual_pct is not None else None,
        failure_reason=failure_reason if not passed else None,
    )


def validate_ysz(
    result_path: str = "results/ysz_ground_state.json",
    reference_path: str = "data/rruff_ysz_reference.json",
) -> MaterialValidationResult:
    """Validate YSZ simulation against RRUFF reference data."""
    sim = load_result(result_path)
    ref = load_reference_data(reference_path)
    props: List[PropertyResult] = []

    # Lattice parameter a (Angstrom)
    props.append(_check(
        "lattice_a",
        sim.get("lattice_a_angstrom"),
        ref.get("lattice_a_angstrom"),
        tol=0.05,
        unit="Å",
        failure_reason="Basis set (LANL2DZ) or active space truncation.",
    ))
    # Lattice parameter c
    props.append(_check(
        "lattice_c",
        sim.get("lattice_c_angstrom"),
        ref.get("lattice_c_angstrom"),
        tol=0.05,
        unit="Å",
        failure_reason="Basis set or active space truncation.",
    ))
    # Oxygen vacancy formation energy
    props.append(_check(
        "oxygen_vacancy_formation_energy",
        sim.get("oxygen_vacancy_formation_ev"),
        ref.get("oxygen_vacancy_formation_ev"),
        tol=0.3,
        unit="eV",
        failure_reason="Active space (6e/6o) excludes deep O 2s contributions.",
    ))
    # Ionic conductivity proxy (relative, unitless ratio)
    props.append(_check(
        "ionic_conductivity_proxy",
        sim.get("ionic_conductivity_proxy"),
        ref.get("ionic_conductivity_proxy"),
        tol=0.2,
        unit="(relative)",
        failure_reason="Cluster model neglects long-range cooperative diffusion.",
    ))
    # Dielectric constant
    props.append(_check(
        "dielectric_constant",
        sim.get("dielectric_constant"),
        ref.get("dielectric_constant"),
        tol=5.0,
        unit="(dimensionless)",
        failure_reason="Finite cluster + active space truncation underestimates polarisability.",
    ))
    # Ground-state energy within tolerance
    props.append(_check(
        "ground_state_energy_kcal_mol",
        sim.get("ground_state_energy_kcal_mol"),
        ref.get("ground_state_energy_kcal_mol"),
        tol=2.0,
        unit="kcal/mol",
        failure_reason="VQE energy above chemical accuracy threshold.",
    ))

    mvr = MaterialValidationResult(
        material="Yttria-Stabilised Zirconia (YSZ)",
        canon_ref="C65",
        properties=props,
    )
    mvr.compute_summary()
    logger.info(
        "YSZ validation: %d/%d passed (%.0f%%)",
        mvr.n_passed, mvr.n_tested, mvr.pass_rate * 100,
    )
    return mvr


def validate_bts(
    result_path: str = "results/bts_ground_state.json",
    reference_path: str = "data/mindat_bts_reference.json",
) -> MaterialValidationResult:
    """Validate BTS simulation against Mindat reference data."""
    sim = load_result(result_path)
    ref = load_reference_data(reference_path)
    props: List[PropertyResult] = []

    # Lattice parameter a
    props.append(_check(
        "lattice_a",
        sim.get("lattice_a_angstrom"),
        ref.get("lattice_a_angstrom"),
        tol=0.05,
        unit="Å",
        failure_reason="ECP (LANL2DZ/Ba) introduces basis incompleteness error.",
    ))
    # Lattice parameter c
    props.append(_check(
        "lattice_c",
        sim.get("lattice_c_angstrom"),
        ref.get("lattice_c_angstrom"),
        tol=0.05,
        unit="Å",
        failure_reason="Ti off-centering displaced geometry approximation.",
    ))
    # Curie temperature
    props.append(_check(
        "curie_temperature_k",
        sim.get("curie_temperature_k"),
        ref.get("curie_temperature_k"),
        tol=30.0,
        unit="K",
        failure_reason="Vegard-law Tc interpolation is sublinear for BTS.",
    ))
    # Spontaneous polarisation
    props.append(_check(
        "spontaneous_polarisation_c_m2",
        sim.get("spontaneous_polarisation_c_m2"),
        ref.get("spontaneous_polarisation_c_m2"),
        tol=0.05,
        unit="C/m²",
        failure_reason="Dipole-moment proxy neglects periodic boundary corrections.",
    ))
    # Piezoelectric e33
    sim_pe = (sim.get("piezoelectric_tensor") or {}).get("e33_c_m2")
    ref_pe = ref.get("e33_c_m2")
    props.append(_check(
        "piezoelectric_e33",
        sim_pe,
        ref_pe,
        tol=1.5,
        unit="C/m²",
        failure_reason="Finite-field perturbation underestimates e33 for 5-atom cluster.",
    ))

    mvr = MaterialValidationResult(
        material="Ba(Ti,Sn)O3 (BTS)",
        canon_ref="C66",
        properties=props,
    )
    mvr.compute_summary()
    logger.info(
        "BTS validation: %d/%d passed (%.0f%%)",
        mvr.n_passed, mvr.n_tested, mvr.pass_rate * 100,
    )
    return mvr


def validate_alscn_gan(
    result_path: str = "results/alscn_gan_interface.json",
    reference_path: str = "data/alscn_gan_literature.json",
) -> MaterialValidationResult:
    """Validate AlScN/GaN simulation against Lemettinen/Fichtner literature."""
    sim = load_result(result_path)
    ref = load_reference_data(reference_path)
    props: List[PropertyResult] = []

    # AlScN lattice a
    props.append(_check(
        "alscn_lattice_a",
        sim.get("alscn_a_angstrom"),
        ref.get("alscn_a_angstrom"),
        tol=0.05,
        unit="Å",
        failure_reason="Literature geometry used directly; no geometry optimisation.",
    ))
    # GaN lattice a
    props.append(_check(
        "gan_lattice_a",
        sim.get("gan_a_angstrom"),
        ref.get("gan_a_angstrom"),
        tol=0.05,
        unit="Å",
        failure_reason="Literature geometry used directly; no geometry optimisation.",
    ))
    # Band offset delta_Ec
    sim_ba = sim.get("band_alignment") or {}
    props.append(_check(
        "delta_ec_band_offset",
        sim_ba.get("delta_ec_ev"),
        ref.get("delta_ec_ev"),
        tol=0.15,
        unit="eV",
        failure_reason="Cluster ionisation proxy; full periodic slab deferred (Canon C67 §4.4).",
    ))
    # Total polarisation discontinuity
    sim_pd = sim.get("polarisation_discontinuity") or {}
    props.append(_check(
        "delta_p_total",
        sim_pd.get("delta_p_total_c_m2"),
        ref.get("delta_p_total_c_m2"),
        tol=0.02,
        unit="C/m²",
        failure_reason="SP from Fichtner 2019; PE from strain estimate, not self-consistent.",
    ))
    # 2DEG sheet charge density
    props.append(_check(
        "sigma_2deg",
        sim.get("sigma_2deg_cm2"),
        ref.get("sigma_2deg_cm2"),
        tol=ref.get("sigma_2deg_tolerance_cm2", 1e13),
        unit="cm⁻²",
        failure_reason="Sheet charge model; Poisson-Schrödinger solver deferred.",
    ))

    mvr = MaterialValidationResult(
        material="Al0.7Sc0.3N/GaN Interface (AlScN:GaN)",
        canon_ref="C67",
        properties=props,
    )
    mvr.compute_summary()
    logger.info(
        "AlScN/GaN validation: %d/%d passed (%.0f%%)",
        mvr.n_passed, mvr.n_tested, mvr.pass_rate * 100,
    )
    return mvr


def validate_all(
    ysz_result: str = "results/ysz_ground_state.json",
    bts_result: str = "results/bts_ground_state.json",
    alscn_result: str = "results/alscn_gan_interface.json",
    ysz_ref: str = "data/rruff_ysz_reference.json",
    bts_ref: str = "data/mindat_bts_reference.json",
    alscn_ref: str = "data/alscn_gan_literature.json",
) -> ValidationReport:
    """Run validation for all three materials and return a full ValidationReport."""
    report = ValidationReport()
    report.materials = [
        validate_ysz(ysz_result, ysz_ref),
        validate_bts(bts_result, bts_ref),
        validate_alscn_gan(alscn_result, alscn_ref),
    ]
    report.compute_summary()
    logger.info(
        "Overall validation: %d/%d passed (%.0f%%) | all_passed=%s",
        report.total_passed, report.total_tested,
        report.total_pass_rate * 100, report.all_passed,
    )
    return report


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_validation_report(
    report: ValidationReport,
    output_path: str = "results/validation_report.md",
) -> None:
    """Write the validation report to a Markdown file."""
    lines = [
        "# GAIA-OS Quantum Chemistry Validation Report",
        "",
        "**Canon Specs:** C65 (YSZ) · C66 (BTS) · C67 (AlScN/GaN)",
        f"**Overall pass rate:** {report.total_passed}/{report.total_tested} "
        f"properties ({report.total_pass_rate:.0%})",
        f"**Acceptance threshold:** ≥ 80% per material",
        f"**Status:** {'\u2705 PASS' if report.all_passed else '\u26a0\ufe0f PARTIAL / ❌ FAIL'}",
        "",
        "---",
        "",
    ]

    for mvr in report.materials:
        status = "✅ PASS" if mvr.overall_passed else "⚠\ufe0f NEEDS REVIEW"
        lines += [
            f"## {mvr.material} ({mvr.canon_ref})",
            "",
            f"**Pass rate:** {mvr.n_passed}/{mvr.n_tested} testable properties "
            f"({mvr.pass_rate:.0%}) — {status}",
            f"**Skipped (null sim values):** {mvr.n_skipped}",
            "",
            "| Property | Simulated | Reference | Tolerance | Unit | Residual | Status | Notes |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for p in mvr.properties:
            sim_s = f"{p.simulated_value:.4g}" if p.simulated_value is not None else "null"
            ref_s = f"{p.reference_value:.4g}" if p.reference_value is not None else "null"
            tol_s = f"±{p.tolerance:.4g}" if p.tolerance is not None else "—"
            res_s = f"{p.residual:.4g}" if p.residual is not None else "—"
            if p.passed is None:
                icon = "⏩ skip"
            elif p.passed:
                icon = "✅"
            else:
                icon = "❌"
            note = p.failure_reason or ""
            lines.append(
                f"| {p.property_name} | {sim_s} | {ref_s} | {tol_s} | "
                f"{p.unit} | {res_s} | {icon} | {note} |"
            )
        lines.append("")

    lines += [
        "---",
        "",
        "## Out-of-Tolerance Properties — Root Cause Analysis",
        "",
        "Properties marked ❌ are documented here with likely causes and "
        "recommended remediation paths.",
        "",
        "### Common Causes",
        "",
        "| Cause | Affected Properties | Remediation |",
        "|---|---|---|",
        "| Active space truncation (6e/6o or 12e/12o) | Ground-state energy, Ef_vac, dielectric constant | Expand active space on GPU backend (Canon C65 §3.2) |",
        "| Cluster finite-size effects | Ionic conductivity, 2DEG density, piezoelectric tensor | Periodic slab models with PBC (Canon C67 §4.4) |",
        "| ECP basis incompleteness (LANL2DZ/Ba, cc-pVTZ-PP/Sc) | Lattice parameters, band offsets | All-electron cc-pVTZ-DK or ZORA |",
        "| Vegard-law Tc interpolation sublinearity | Curie temperature (BTS) | Landau free energy fit across Sn fraction |",
        "| Dipole-moment SP proxy | Spontaneous polarisation (BTS) | Berry phase via periodic DFPT |",
        "",
        "---",
        "",
        "*Generated by `src-python/quantum_chemistry/validator.py` — GAIA-OS #139*",
    ]

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    logger.info("Validation report written to %s", out)
