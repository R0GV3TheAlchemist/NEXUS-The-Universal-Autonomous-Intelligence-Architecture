"""tests/test_wirelesspowersim.py

Test scaffold for src-python/wirelesspowersim

Covers: ResonantCoupler, PowerBeam, PowerGridSim
"""
import pytest

from wirelesspowersim import ResonantCoupler, PowerBeam, PowerGridSim


class TestResonantCoupler:

    def test_coupler_constructs(self):
        coupler = ResonantCoupler(
            node_id="node-1",
            resonant_frequency=6.78e6,
            quality_factor=300.0,
            coupling_coefficient=0.1,
        )
        assert coupler.node_id == "node-1"

    def test_efficiency_raises_not_implemented(self):
        coupler = ResonantCoupler(
            node_id="n", resonant_frequency=6.78e6, quality_factor=300.0
        )
        with pytest.raises(NotImplementedError):
            coupler.efficiency()


class TestPowerGridSim:

    def test_register_coupler(self):
        sim = PowerGridSim()
        coupler = ResonantCoupler(
            node_id="n1", resonant_frequency=6.78e6, quality_factor=300.0
        )
        sim.register_coupler(coupler)
        # Verify internal registry
        assert "n1" in sim._couplers

    def test_simulate_power_flow_raises_not_implemented(self):
        sim = PowerGridSim()
        with pytest.raises(NotImplementedError):
            sim.simulate_power_flow()


class TestPowerBeam:

    def test_power_beam_constructs(self):
        beam = PowerBeam(transmitter_ids=["tx1", "tx2"], receiver_id="rx1")
        assert len(beam.transmitter_ids) == 2

    def test_optimize_currents_raises_not_implemented(self):
        beam = PowerBeam(transmitter_ids=["tx1"], receiver_id="rx1")
        with pytest.raises(NotImplementedError):
            beam.optimize_currents(rx_position=None)
