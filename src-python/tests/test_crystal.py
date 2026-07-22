"""tests/test_crystal.py

Test scaffold for src-python/crystal

Covers: CrystalCore, CrystalLattice, CrystalNode, crystal_router
"""
import pytest

crystal = pytest.importorskip("crystal")


class TestCrystalCore:

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_init_crystal_core(self):
        from crystal import init_crystal_core
        core = init_crystal_core()
        assert core is not None

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_lattice_has_nodes(self):
        from crystal.engine import CrystalLattice, CrystalNode
        node = CrystalNode(node_id="n1", element="C", position=(0.0, 0.0, 0.0))
        lattice = CrystalLattice(nodes=[node])
        assert len(lattice.nodes) == 1

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_phonon_modes_not_empty(self):
        from crystal.engine import CrystalCore
        core = CrystalCore()
        modes = core.compute_phonon_modes()
        assert len(modes) > 0
