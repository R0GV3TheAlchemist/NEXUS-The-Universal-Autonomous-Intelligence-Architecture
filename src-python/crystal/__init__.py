"""
crystal — Crystal Lattice Engine

Models crystalline lattice structures and phonon propagation for NEXUS
quantum-material interfaces. Provides CrystalCore for lattice management.

Architecture reference: NEXUS_UNIVERSAL_OS.md Domain 3.1
Design reference:       ASE (Atomic Simulation Environment); pymatgen
"""
from __future__ import annotations

from crystal.engine import CrystalCore, CrystalNode, CrystalLattice
from crystal.router import crystal_router, init_crystal_core

__all__ = ["CrystalCore", "CrystalNode", "CrystalLattice", "crystal_router", "init_crystal_core"]
