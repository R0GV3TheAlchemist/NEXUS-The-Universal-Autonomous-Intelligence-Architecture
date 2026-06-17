"""
tests/test_talisman.py

Backend tests — Talisman Object v1.

Covers:
  1. create_talisman returns a valid Talisman with DORMANT status
  2. list_talismans includes newly created talismans
  3. get_talisman returns correct object by ID
  4. get_talisman returns None for unknown ID
  5. activate_talisman sets status to ACTIVE and records timestamp
  6. activation applies relative deltas (core fix) not raw values
  7. deactivate_talisman sets status back to DORMANT
  8. double-activation is idempotent (status stays ACTIVE)
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

from gaia.core.talisman import TalismanStatus
from gaia.core.talisman_store import (
    activate_talisman,
    create_talisman,
    deactivate_talisman,
    get_talisman,
    list_talismans,
)
from gaia.core.state import GAIAState, GAIAOperationalMode


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_talisman(**kwargs):
    return create_talisman(
        name=kwargs.get("name", "Test Talisman"),
        purpose=kwargs.get("purpose", "Testing."),
        coherence_delta=kwargs.get("coherence_delta", 0.1),
        energy_delta=kwargs.get("energy_delta", 0.05),
        stress_delta=kwargs.get("stress_delta", -0.05),
        entropy_delta=kwargs.get("entropy_delta", -0.02),
        notes=kwargs.get("notes", ""),
    )


def _mock_state(coherence=0.6, energy=0.7, stress=0.3, entropy=0.2):
    """Return a realistic GAIAState for patching get_state()."""
    return GAIAState(
        system_state=GAIAOperationalMode.BUILD,
        coherence=coherence,
        energy=energy,
        stress=stress,
        entropy=entropy,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestTalismanCRUD:
    def test_create_returns_dormant_talisman(self):
        t = _make_talisman(name="Create Test")
        assert t.status == TalismanStatus.DORMANT
        assert t.id is not None
        assert t.last_activated_at is None

    def test_list_includes_created_talisman(self):
        t = _make_talisman(name="List Test")
        ids = [x.id for x in list_talismans()]
        assert t.id in ids

    def test_get_returns_correct_talisman(self):
        t = _make_talisman(name="Get Test")
        fetched = get_talisman(t.id)
        assert fetched is not None
        assert fetched.id == t.id
        assert fetched.name == "Get Test"

    def test_get_unknown_returns_none(self):
        result = get_talisman("00000000-0000-0000-0000-000000000000")
        assert result is None


class TestTalismanActivation:
    def test_activate_sets_active_status(self):
        t = _make_talisman(name="Activate Test")
        with patch("gaia.core.talisman_store.get_state", return_value=_mock_state()):
            talisman, _decision = activate_talisman(t.id)
        assert talisman.status == TalismanStatus.ACTIVE
        assert talisman.last_activated_at is not None

    def test_activation_applies_relative_deltas(self):
        """
        Core fix: coherence passed to run_d6_cycle must equal
        current_coherence + coherence_delta, not just coherence_delta.
        """
        base_coherence = 0.5
        c_delta = 0.1
        t = _make_talisman(name="Delta Test", coherence_delta=c_delta)
        mock_state = _mock_state(coherence=base_coherence)

        captured_args = {}

        def _capture_d6(**kwargs):
            captured_args.update(kwargs)
            from gaia.core.d6_engine import run_d6
            return run_d6(_mock_state(**kwargs) if False else mock_state)

        with patch("gaia.core.talisman_store.get_state", return_value=mock_state), \
             patch("gaia.core.talisman_store.run_d6_cycle", side_effect=_capture_d6):
            activate_talisman(t.id)

        expected = round(base_coherence + c_delta, 10)
        assert abs(captured_args.get("coherence", 0) - expected) < 1e-9, (
            f"Expected coherence {expected}, got {captured_args.get('coherence')}"
        )

    def test_deactivate_sets_dormant(self):
        t = _make_talisman(name="Deactivate Test")
        with patch("gaia.core.talisman_store.get_state", return_value=_mock_state()):
            activate_talisman(t.id)
        result = deactivate_talisman(t.id)
        assert result.status == TalismanStatus.DORMANT

    def test_double_activate_stays_active(self):
        t = _make_talisman(name="Idempotent Test")
        mock_state = _mock_state()
        with patch("gaia.core.talisman_store.get_state", return_value=mock_state):
            activate_talisman(t.id)
            activate_talisman(t.id)
        assert get_talisman(t.id).status == TalismanStatus.ACTIVE
