"""tests/test_quantumchemistry.py

Test scaffold for src-python/quantumchemistry

Covers: MolecularSimulator, HamiltonianBuilder, EnergyMinimizer,
        MoleculeSpec, VQEResult
"""
import pytest

from quantumchemistry import (
    Atom, MoleculeSpec, MolecularSimulator, HamiltonianBuilder, EnergyMinimizer
)


class TestMoleculeSpec:

    def test_molecule_spec_constructs(self):
        """MoleculeSpec should construct cleanly — no external deps."""
        mol = MoleculeSpec(
            atoms=[Atom("H", 0.0, 0.0, 0.0), Atom("H", 0.0, 0.0, 0.74)],
            charge=0,
            multiplicity=1,
            basis="sto-3g",
        )
        assert len(mol.atoms) == 2
        assert mol.basis == "sto-3g"

    def test_default_basis_is_sto3g(self):
        mol = MoleculeSpec()
        assert mol.basis == "sto-3g"


class TestMolecularSimulatorStub:

    def test_run_hf_raises_not_implemented(self):
        sim = MolecularSimulator()
        mol = MoleculeSpec(atoms=[Atom("H", 0, 0, 0)])
        with pytest.raises(NotImplementedError):
            sim.run_hf(mol)

    def test_run_correlated_raises_not_implemented(self):
        sim = MolecularSimulator()
        mol = MoleculeSpec(atoms=[Atom("H", 0, 0, 0)])
        with pytest.raises(NotImplementedError):
            sim.run_correlated(mol, method="CCSD")


class TestHamiltonianBuilderStub:

    def test_build_fermionic_raises_not_implemented(self):
        from quantumchemistry import ClassicalResult, FermionicHamiltonian
        builder = HamiltonianBuilder()
        mol = MoleculeSpec()
        classical = ClassicalResult(method="HF", energy_hartree=-1.117)
        with pytest.raises(NotImplementedError):
            builder.build_fermionic(mol, classical)

    def test_to_qubit_raises_not_implemented(self):
        from quantumchemistry import FermionicHamiltonian
        builder = HamiltonianBuilder()
        fermionic = FermionicHamiltonian(description="stub")
        with pytest.raises(NotImplementedError):
            builder.to_qubit(fermionic)


class TestEnergyMinimizerStub:

    def test_run_vqe_raises_not_implemented(self):
        from quantumchemistry import QubitHamiltonian
        minimizer = EnergyMinimizer()
        h = QubitHamiltonian(transform="jordan-wigner")
        with pytest.raises(NotImplementedError):
            minimizer.run_vqe(h)
