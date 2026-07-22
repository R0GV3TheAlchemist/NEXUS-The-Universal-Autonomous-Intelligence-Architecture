"""quantumchemistry

NEXUS Quantum Chemistry Simulation APIs

High-level stubs for the NEXUS quantum chemistry pipeline:
    1. Define molecular geometry (MoleculeSpec).
    2. Classical pre-computation via PySCF (MolecularSimulator).
    3. Build fermionic Hamiltonian via OpenFermion (HamiltonianBuilder).
    4. Apply fermion-to-qubit transform (HamiltonianBuilder.to_qubit).
    5. Run VQE via Qiskit Nature or CUDA-Q (EnergyMinimizer).

Architecture reference:
    NEXUS_UNIVERSAL_OS.md  Domain 5.1 - Quantum Chemistry
Research reference:
    PySCF   github.com/pyscf/pyscf
    OpenFermion quantumai.google/openfermion
    openfermion-pyscf bridge
    qiskit-nature-pyscf plugin
    NVIDIA CUDA-Q VQE tutorial
"""
from __future__ import annotations

from quantumchemistry.qchem import (
    Atom,
    MoleculeSpec,
    ClassicalResult,
    FermionicHamiltonian,
    QubitHamiltonian,
    VQEResult,
    MolecularSimulator,
    HamiltonianBuilder,
    EnergyMinimizer,
)

__all__ = [
    "Atom",
    "MoleculeSpec",
    "ClassicalResult",
    "FermionicHamiltonian",
    "QubitHamiltonian",
    "VQEResult",
    "MolecularSimulator",
    "HamiltonianBuilder",
    "EnergyMinimizer",
]
