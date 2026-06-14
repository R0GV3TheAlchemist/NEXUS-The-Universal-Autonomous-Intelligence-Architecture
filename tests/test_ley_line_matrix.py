"""
Tests — Ley Line Matrix

Covers:
  - Node registration
  - Line addition and blockage
  - Standard pulse routing
  - Quantum superposition routing
  - Schumann frequency alignment
  - Canon-law enforcement
  - Broadcast routing
  - Snapshot / visualizer output
"""

from __future__ import annotations

import pytest

from core.ley_line_matrix.matrix import LeyLineMatrix
from core.ley_line_matrix.models import FlowType, LeyLine, LeyNode, LeyPulse
from core.ley_line_matrix.router import broadcast, priority_score, route_batch
from core.ley_line_matrix.schumann_sync import align_pulse_frequency
from core.ley_line_matrix.visualizer import render_topology


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def matrix() -> LeyLineMatrix:
    """Fresh matrix for each test."""
    return LeyLineMatrix()


@pytest.fixture
def two_nodes() -> tuple[LeyNode, LeyNode]:
    a = LeyNode(name="alpha", module_path="core.alpha", description="Node A")
    b = LeyNode(name="beta", module_path="core.beta", description="Node B")
    return a, b


@pytest.fixture
def connected_matrix(matrix, two_nodes) -> LeyLineMatrix:
    a, b = two_nodes
    line = LeyLine(source=a, target=b, flow_type=FlowType.RESONANCE, strength=1.0)
    matrix.add_line(line)
    return matrix


# ---------------------------------------------------------------------------
# Node registration
# ---------------------------------------------------------------------------

class TestNodeRegistration:
    def test_register_node(self, matrix, two_nodes):
        a, _ = two_nodes
        matrix.register_node(a)
        assert "alpha" in matrix._nodes

    def test_duplicate_registration_is_idempotent(self, matrix, two_nodes):
        a, _ = two_nodes
        matrix.register_node(a)
        matrix.register_node(a)
        assert len(matrix._nodes) == 1

    def test_deregister_node(self, matrix, two_nodes):
        a, _ = two_nodes
        matrix.register_node(a)
        matrix.deregister_node("alpha")
        assert "alpha" not in matrix._nodes


# ---------------------------------------------------------------------------
# Line management
# ---------------------------------------------------------------------------

class TestLineManagement:
    def test_add_line_registers_nodes(self, matrix, two_nodes):
        a, b = two_nodes
        line = LeyLine(source=a, target=b, flow_type=FlowType.RESONANCE)
        matrix.add_line(line)
        assert "alpha" in matrix._nodes
        assert "beta" in matrix._nodes

    def test_block_line(self, matrix, two_nodes):
        a, b = two_nodes
        line = LeyLine(source=a, target=b, flow_type=FlowType.RESONANCE)
        matrix.add_line(line)
        matrix.block_line("alpha", "beta")
        assert matrix._lines[0].blocked is True

    def test_unblock_line(self, matrix, two_nodes):
        a, b = two_nodes
        line = LeyLine(source=a, target=b, flow_type=FlowType.RESONANCE)
        matrix.add_line(line)
        matrix.block_line("alpha", "beta")
        matrix.unblock_line("alpha", "beta")
        assert matrix._lines[0].blocked is False

    def test_dark_lines(self, matrix, two_nodes):
        a, b = two_nodes
        line = LeyLine(source=a, target=b, flow_type=FlowType.SHADOW, strength=0.0)
        matrix.add_line(line)
        assert len(matrix.get_dark_lines()) == 1


# ---------------------------------------------------------------------------
# Pulse routing
# ---------------------------------------------------------------------------

class TestPulseRouting:
    def test_successful_route(self, connected_matrix):
        pulse = LeyPulse(origin="alpha", destination="beta", flow_type=FlowType.RESONANCE)
        result = connected_matrix.emit(pulse)
        assert result is True
        assert pulse.routed is True

    def test_blocked_route(self, matrix, two_nodes):
        a, b = two_nodes
        line = LeyLine(source=a, target=b, flow_type=FlowType.RESONANCE)
        matrix.add_line(line)
        matrix.block_line("alpha", "beta")
        pulse = LeyPulse(origin="alpha", destination="beta", flow_type=FlowType.RESONANCE)
        result = matrix.emit(pulse)
        assert result is False
        assert pulse.blocked is True

    def test_unknown_origin_blocked(self, matrix):
        pulse = LeyPulse(origin="ghost", destination="beta", flow_type=FlowType.RAW)
        result = matrix.emit(pulse)
        assert result is False

    def test_quantum_route_superposition(self, matrix):
        a = LeyNode(name="q_a", module_path="core.q_a")
        b = LeyNode(name="q_b", module_path="core.q_b")
        c = LeyNode(name="q_c", module_path="core.q_c")
        matrix.add_line(LeyLine(source=a, target=b, flow_type=FlowType.QUANTUM))
        matrix.add_line(LeyLine(source=a, target=c, flow_type=FlowType.QUANTUM))
        matrix.add_line(LeyLine(source=b, target=c, flow_type=FlowType.QUANTUM))
        pulse = LeyPulse(origin="q_a", destination="q_c", flow_type=FlowType.QUANTUM)
        result = matrix.emit(pulse)
        assert result is True
        assert "quantum_paths" in pulse.metadata
        assert len(pulse.metadata["quantum_paths"]) >= 2


# ---------------------------------------------------------------------------
# Schumann alignment
# ---------------------------------------------------------------------------

class TestSchumannSync:
    def test_align_resonance_pulse(self):
        pulse = LeyPulse(origin="a", destination="b", flow_type=FlowType.RESONANCE, frequency_hz=0.0)
        aligned = align_pulse_frequency(pulse)
        assert aligned.frequency_hz == 7.83
        assert aligned.metadata.get("schumann_aligned") is True

    def test_align_quantum_pulse(self):
        pulse = LeyPulse(origin="a", destination="b", flow_type=FlowType.QUANTUM, frequency_hz=0.0)
        aligned = align_pulse_frequency(pulse)
        assert aligned.frequency_hz == 33.8

    def test_align_noospheric_pulse(self):
        pulse = LeyPulse(origin="a", destination="b", flow_type=FlowType.NOOSPHERIC, frequency_hz=0.0)
        aligned = align_pulse_frequency(pulse)
        assert aligned.frequency_hz == 27.3


# ---------------------------------------------------------------------------
# Router utilities
# ---------------------------------------------------------------------------

class TestRouter:
    def test_priority_score_canon_first(self):
        canon_pulse = LeyPulse(origin="a", destination="b", flow_type=FlowType.CANON_LAW)
        raw_pulse = LeyPulse(origin="a", destination="b", flow_type=FlowType.RAW)
        assert priority_score(canon_pulse) < priority_score(raw_pulse)


# ---------------------------------------------------------------------------
# Snapshot & Visualizer
# ---------------------------------------------------------------------------

class TestSnapshot:
    def test_snapshot_keys(self, connected_matrix):
        snap = connected_matrix.snapshot()
        assert "nodes" in snap
        assert "lines" in snap
        assert "dark_lines" in snap
        assert "pulse_count" in snap

    def test_visualizer_topology(self, connected_matrix):
        topo = render_topology(connected_matrix)
        assert "nodes" in topo
        assert "edges" in topo
        assert "stats" in topo
        assert len(topo["nodes"]) == 2
        assert len(topo["edges"]) == 1
