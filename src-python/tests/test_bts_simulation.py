"""
test_bts_simulation.py
======================
Tests for the BTS quantum chemistry simulation driver.

Same skipif strategy as test_ysz_simulation.py:
  - Structural / schema tests run unconditionally.
  - Live simulation tests skipped when quantum packages absent.

Run with:
    pytest src-python/tests/test_bts_simulation.py -v
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _qpkgs_installed() -> bool:
    for pkg in ("pyscf", "qiskit_nature", "qiskit_aer"):
        try:
            importlib.import_module(pkg)
        except ImportError:
            return False
    return True


QPKGS_MARK = pytest.mark.skipif(
    not _qpkgs_installed(),
    reason="Quantum chemistry packages not installed — skipping live BTS tests.",
)


# ---------------------------------------------------------------------------
# Structural / schema tests (no packages required)
# ---------------------------------------------------------------------------

def test_bts_module_importable():
    """bts module must import without error."""
    import quantum_chemistry.targets.bts as bts  # noqa: F401
    assert bts is not None


def test_bts_atom_list_structure():
    """BTS_ATOMS must have 5 entries, each (symbol, (x,y,z))."""
    from quantum_chemistry.targets.bts import BTS_ATOMS
    assert len(BTS_ATOMS) == 5
    for sym, coords in BTS_ATOMS:
        assert isinstance(sym, str)
        assert len(coords) == 3


def test_bts_atom_list_elements():
    """BTS cluster must contain Ba, Ti, and O atoms."""
    from quantum_chemistry.targets.bts import BTS_ATOMS
    symbols = {sym for sym, _ in BTS_ATOMS}
    assert "Ba" in symbols
    assert "Ti" in symbols
    assert "O" in symbols


def test_bts_lattice_parameters():
    """BTS lattice parameters must match Mindat ID 4219 interpolated values."""
    from quantum_chemistry.targets.bts import BTS_LATTICE_A, BTS_LATTICE_C, BTS_TETRAGONALITY
    assert BTS_LATTICE_A == pytest.approx(3.9835, abs=1e-4)
    assert BTS_LATTICE_C == pytest.approx(4.0361, abs=1e-4)
    assert BTS_TETRAGONALITY == pytest.approx(BTS_LATTICE_C / BTS_LATTICE_A, rel=1e-6)


def test_bts_tc_estimate():
    """Phase transition temperature estimate must lie between SrTiO3 and BaTiO3 Tc."""
    from quantum_chemistry.targets.bts import (
        TC_BTS_ESTIMATE_K, TC_BATIO3_K, TC_SRTIO3_K
    )
    assert TC_SRTIO3_K < TC_BTS_ESTIMATE_K < TC_BATIO3_K


def test_bts_polarisation_reference():
    """Spontaneous polarisation reference must be 0.26 C/m² (BaTiO₃, Lines & Glass 1977)."""
    from quantum_chemistry.targets.bts import PS_REFERENCE_C_M2
    assert PS_REFERENCE_C_M2 == pytest.approx(0.26, abs=0.01)


def test_bts_simulation_result_defaults():
    """BTSSimulationResult must instantiate with correct identity defaults."""
    from quantum_chemistry.targets.bts import BTSSimulationResult
    r = BTSSimulationResult()
    assert r.material == "BTS"
    assert r.formula == "Ba0.6Sr0.4TiO3"
    assert r.canon_ref == "C66"
    assert r.mindat_ref == "4219"
    assert r.vqe_ansatz == "UCCSD"
    assert r.vqe_optimizer == "SLSQP"
    assert len(r.known_limitations) >= 5


def test_bts_to_canon_c66_dict_keys():
    """to_canon_c66_dict() must include all required Canon C66 keys."""
    from quantum_chemistry.targets.bts import BTSSimulationResult
    r = BTSSimulationResult()
    d = r.to_canon_c66_dict()
    required_keys = {
        "material", "formula", "canon_ref", "mindat_ref",
        "ground_state_energy_hartree", "ground_state_energy_ev",
        "vqe_converged", "vqe_ansatz", "vqe_optimizer",
        "polarisation_c_m2", "polarisation_reference_c_m2",
        "polarisation_within_tolerance", "piezoelectric_tensor",
        "tc_estimate_k", "sr_fraction",
        "within_tolerance", "delta_kcal_mol",
        "simulator_backend", "known_limitations",
    }
    missing = required_keys - d.keys()
    assert not missing, f"Missing Canon C66 keys: {missing}"


def test_bts_results_json_schema_stub_valid():
    """results/bts_ground_state.json must be valid JSON with expected keys."""
    json_path = Path("results/bts_ground_state.json")
    assert json_path.exists(), "results/bts_ground_state.json not found"
    with json_path.open() as fh:
        data = json.load(fh)
    assert data["material"] == "BTS"
    assert data["canon_ref"] == "C66"
    assert data["mindat_ref"] == "4219"
    assert "polarisation_c_m2" in data
    assert "piezoelectric_tensor" in data
    assert data["piezoelectric_tensor"]["reference_e33_c_m2"] == pytest.approx(6.7)


# ---------------------------------------------------------------------------
# Live simulation tests (skipped when packages absent)
# ---------------------------------------------------------------------------

@QPKGS_MARK
def test_build_bts_mole_displaced():
    """build_bts_mole(centrosymmetric=False) must return a valid 5-atom Mole."""
    from quantum_chemistry.targets.bts import build_bts_mole
    mol = build_bts_mole(centrosymmetric=False)
    assert mol.natm == 5
    assert mol.nao_nr() > 0


@QPKGS_MARK
def test_full_bts_simulation_runs(tmp_path):
    """
    Full BTS pipeline must complete without error and produce Canon C66 JSON.
    Polarisation and piezoelectric skipped for CI speed.
    """
    from quantum_chemistry.targets.bts import run_bts_simulation
    out = str(tmp_path / "bts_test.json")
    result = run_bts_simulation(
        output_path=out,
        skip_polarisation=True,
        skip_piezoelectric=True,
    )
    assert result.vqe_converged
    assert result.ground_state_energy_ev < 0
    import json
    from pathlib import Path
    with Path(out).open() as fh:
        data = json.load(fh)
    assert data["canon_ref"] == "C66"
    assert data["vqe_converged"] is True
