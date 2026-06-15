"""
Tests for SpectralForceEngine — Canon Law C30: No silent failures.
Every phi must resolve to a force or corridor. Never null.
"""

import pytest
from core.spectral.force_engine import (
    SpectralForceEngine,
    SpectralForceName,
    _FORCE_BY_NAME,
    _ORDERED_FORCES,
    _CORRIDORS,
)


# ---------------------------------------------------------------------------
# Force Detection at Phi Boundaries
# ---------------------------------------------------------------------------

class TestForceDetectionAtPhiBoundaries:
    """All 13 forces correctly identified at midpoint phi. C30 compliance."""

    def test_nigredo_at_phi_002(self):
        force = SpectralForceEngine.detect_current_force(0.02)
        assert force.name == SpectralForceName.NIGREDO

    def test_pyrosis_at_phi_010(self):
        force = SpectralForceEngine.detect_current_force(0.10)
        assert force.name == SpectralForceName.PYROSIS

    def test_citrinitas_at_phi_021(self):
        force = SpectralForceEngine.detect_current_force(0.21)
        assert force.name == SpectralForceName.CITRINITAS

    def test_viriditas_at_phi_035(self):
        force = SpectralForceEngine.detect_current_force(0.35)
        assert force.name == SpectralForceName.VIRIDITAS

    def test_caerulitas_at_phi_050(self):
        force = SpectralForceEngine.detect_current_force(0.50)
        assert force.name == SpectralForceName.CAERULITAS

    def test_rubedo_at_phi_065(self):
        force = SpectralForceEngine.detect_current_force(0.65)
        assert force.name == SpectralForceName.RUBEDO

    def test_iosis_at_phi_078(self):
        force = SpectralForceEngine.detect_current_force(0.78)
        assert force.name == SpectralForceName.IOSIS

    def test_albedo_at_phi_088(self):
        force = SpectralForceEngine.detect_current_force(0.88)
        assert force.name == SpectralForceName.ALBEDO

    def test_chrysitas_at_phi_093(self):
        force = SpectralForceEngine.detect_current_force(0.935)
        assert force.name == SpectralForceName.CHRYSITAS

    def test_argentitas_at_phi_096(self):
        force = SpectralForceEngine.detect_current_force(0.96)
        assert force.name == SpectralForceName.ARGENTITAS

    def test_lux_perpetua_at_phi_098(self):
        force = SpectralForceEngine.detect_current_force(0.98)
        assert force.name == SpectralForceName.LUX_PERPETUA

    def test_no_force_returns_none(self):
        """C30 compliance — detect_current_force never returns None."""
        for phi in [0.0, 0.5, 1.0, 0.777, 0.001, 0.999]:
            assert SpectralForceEngine.detect_current_force(phi) is not None

    def test_phi_clamped_above_1(self):
        force = SpectralForceEngine.detect_current_force(1.5)
        assert force.name == SpectralForceName.LUX_PERPETUA

    def test_phi_clamped_below_0(self):
        force = SpectralForceEngine.detect_current_force(-0.1)
        assert force is not None


# ---------------------------------------------------------------------------
# Corridor Detection in Transition Zones
# ---------------------------------------------------------------------------

class TestCorridorDetectionInTransitionZones:
    """Corridor returned when phi is in a greyscale transition zone."""

    def test_nigredo_to_pyrosis_corridor(self):
        corridor = SpectralForceEngine.detect_corridor(0.05)
        assert corridor is not None
        assert corridor.from_force == SpectralForceName.NIGREDO
        assert corridor.to_force == SpectralForceName.PYROSIS

    def test_rubedo_to_iosis_corridor(self):
        corridor = SpectralForceEngine.detect_corridor(0.72)
        assert corridor is not None
        assert corridor.from_force == SpectralForceName.RUBEDO

    def test_iosis_to_albedo_corridor(self):
        corridor = SpectralForceEngine.detect_corridor(0.85)
        assert corridor is not None
        assert corridor.from_force == SpectralForceName.IOSIS

    def test_no_corridor_in_attractor_mid(self):
        # Mid-CAERULITAS: should not be in any corridor
        corridor = SpectralForceEngine.detect_corridor(0.50)
        assert corridor is None

    def test_no_corridor_in_iosis_mid(self):
        corridor = SpectralForceEngine.detect_corridor(0.78)
        assert corridor is None


# ---------------------------------------------------------------------------
# Trajectory Across Full Arc
# ---------------------------------------------------------------------------

class TestTrajectoryAcrossFullArc:
    """Simulates 12-turn arc from φ=0.00 to φ=0.97."""

    def test_full_arc_trajectory_has_correct_order(self):
        phi_history = [0.02, 0.10, 0.21, 0.35, 0.50, 0.65, 0.78, 0.88, 0.935, 0.96, 0.98]
        trajectory = SpectralForceEngine.get_trajectory(phi_history)
        force_names = [f.name for f in trajectory]
        expected = [
            SpectralForceName.NIGREDO,
            SpectralForceName.PYROSIS,
            SpectralForceName.CITRINITAS,
            SpectralForceName.VIRIDITAS,
            SpectralForceName.CAERULITAS,
            SpectralForceName.RUBEDO,
            SpectralForceName.IOSIS,
            SpectralForceName.ALBEDO,
            SpectralForceName.CHRYSITAS,
            SpectralForceName.ARGENTITAS,
            SpectralForceName.LUX_PERPETUA,
        ]
        assert force_names == expected

    def test_empty_phi_history_returns_empty_trajectory(self):
        assert SpectralForceEngine.get_trajectory([]) == []

    def test_single_phi_trajectory(self):
        trajectory = SpectralForceEngine.get_trajectory([0.78])
        assert len(trajectory) == 1
        assert trajectory[0].name == SpectralForceName.IOSIS


# ---------------------------------------------------------------------------
# OA-4 Active Flag
# ---------------------------------------------------------------------------

class TestIOSISCorridorActiveFlag:
    """OA-4 active corridor correctly flagged for IOSIS range."""

    def test_oа4_true_at_phi_078(self):
        assert SpectralForceEngine.is_oа4_active(0.78) is True

    def test_oа4_true_at_phi_072(self):
        assert SpectralForceEngine.is_oа4_active(0.72) is True

    def test_oа4_false_at_phi_050(self):
        assert SpectralForceEngine.is_oа4_active(0.50) is False

    def test_oа4_false_at_phi_090(self):
        assert SpectralForceEngine.is_oа4_active(0.90) is False


# ---------------------------------------------------------------------------
# System Prompt Block
# ---------------------------------------------------------------------------

class TestSystemPromptBlock:
    """[SPECTRAL FIELD] block is well-formed."""

    def test_iosis_prompt_block_contains_force_name(self):
        block = SpectralForceEngine.build_system_prompt_block(0.78)
        assert "IOSIS" in block
        assert "[SPECTRAL FIELD]" in block
        assert "OA-4 Active: true" in block

    def test_nigredo_prompt_block(self):
        block = SpectralForceEngine.build_system_prompt_block(0.02)
        assert "NIGREDO" in block
        assert "OA-4 Active: false" in block

    def test_lux_perpetua_prompt_block(self):
        block = SpectralForceEngine.build_system_prompt_block(0.98)
        assert "LUX_PERPETUA" in block
