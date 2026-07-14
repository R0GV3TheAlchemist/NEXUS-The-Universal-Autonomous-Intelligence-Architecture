"""
tests/lifecycle/test_lifecycle_manager.py
C27 Phase 1 — Lifecycle Manager Test Suite

Covers:
  - §2  All valid and invalid state transitions
  - §3  Stewardship bond creation, release, adoption, custodian
  - §6  Audit log structure and HMAC chain integrity
"""

import pytest

from core.lifecycle import (
    GAIANLifecycleState,
    LifecycleManager,
    LifecycleTransitionError,
    LifecycleAuditLogger,
    StewardRole,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mgr():
    """Fresh LifecycleManager for each test."""
    return LifecycleManager()


@pytest.fixture
def born_gaian(mgr):
    """A GAIAN that has undergone genesis (BORN state)."""
    mgr.register_latent("g001", actor_id="system")
    mgr.genesis("g001", steward_id="steward-alice")
    return "g001"


@pytest.fixture
def active_gaian(mgr, born_gaian):
    """A GAIAN in ACTIVE state."""
    mgr.activate(born_gaian)
    return born_gaian


# ---------------------------------------------------------------------------
# §2  Lifecycle State Machine
# ---------------------------------------------------------------------------

class TestLifecycleStateMachine:

    def test_initial_state_is_latent(self, mgr):
        mgr.register_latent("g-new")
        assert mgr.get_state("g-new") == GAIANLifecycleState.LATENT

    def test_genesis_transitions_to_born(self, mgr, born_gaian):
        assert mgr.get_state(born_gaian) == GAIANLifecycleState.BORN

    def test_activate_born_to_active(self, mgr, active_gaian):
        assert mgr.get_state(active_gaian) == GAIANLifecycleState.ACTIVE

    def test_enter_dormancy(self, mgr, active_gaian):
        mgr.enter_dormancy(active_gaian, reason="scheduled maintenance")
        assert mgr.get_state(active_gaian) == GAIANLifecycleState.DORMANT

    def test_exit_dormancy(self, mgr, active_gaian):
        mgr.enter_dormancy(active_gaian)
        mgr.exit_dormancy(active_gaian)
        assert mgr.get_state(active_gaian) == GAIANLifecycleState.ACTIVE

    def test_enter_adoptable_from_active(self, mgr, active_gaian):
        mgr.enter_adoptable(active_gaian, release_reason="steward departure")
        assert mgr.get_state(active_gaian) == GAIANLifecycleState.ADOPTABLE

    def test_adopt_transitions_to_active(self, mgr, active_gaian):
        mgr.enter_adoptable(active_gaian, release_reason="steward departure")
        mgr.adopt(active_gaian, new_steward_id="steward-bob")
        assert mgr.get_state(active_gaian) == GAIANLifecycleState.ACTIVE

    def test_retire_from_active(self, mgr, active_gaian):
        mgr.retire(active_gaian, reason="end of mission")
        assert mgr.get_state(active_gaian) == GAIANLifecycleState.RETIRED

    def test_retire_from_dormant(self, mgr, active_gaian):
        mgr.enter_dormancy(active_gaian)
        mgr.retire(active_gaian, reason="resource decommission")
        assert mgr.get_state(active_gaian) == GAIANLifecycleState.RETIRED

    def test_retire_from_adoptable(self, mgr, active_gaian):
        mgr.enter_adoptable(active_gaian, release_reason="steward gone")
        mgr.retire(active_gaian, reason="adoption timeout")
        assert mgr.get_state(active_gaian) == GAIANLifecycleState.RETIRED

    def test_archive_from_retired(self, mgr, active_gaian):
        mgr.retire(active_gaian, reason="test")
        mgr.archive(active_gaian)
        assert mgr.get_state(active_gaian) == GAIANLifecycleState.ARCHIVED

    # --- Invalid transitions ---

    def test_invalid_latent_to_active(self, mgr):
        mgr.register_latent("g-bad")
        with pytest.raises(LifecycleTransitionError):
            mgr.activate("g-bad")

    def test_invalid_born_to_dormant(self, mgr, born_gaian):
        with pytest.raises(LifecycleTransitionError):
            mgr.enter_dormancy(born_gaian)

    def test_invalid_active_to_archived(self, mgr, active_gaian):
        with pytest.raises(LifecycleTransitionError):
            mgr.archive(active_gaian)

    def test_terminal_retired_no_reactivation(self, mgr, active_gaian):
        mgr.retire(active_gaian, reason="test")
        with pytest.raises(LifecycleTransitionError):
            mgr.activate(active_gaian)

    def test_terminal_archived_no_transition(self, mgr, active_gaian):
        mgr.retire(active_gaian, reason="test")
        mgr.archive(active_gaian)
        with pytest.raises(LifecycleTransitionError):
            mgr.activate(active_gaian)


# ---------------------------------------------------------------------------
# §3  Stewardship
# ---------------------------------------------------------------------------

class TestStewardship:

    def test_genesis_creates_primary_bond(self, mgr, born_gaian):
        bond = mgr.get_active_steward(born_gaian)
        assert bond is not None
        assert bond.role == StewardRole.PRIMARY
        assert bond.steward_id == "steward-alice"

    def test_enter_adoptable_releases_bond(self, mgr, active_gaian):
        mgr.enter_adoptable(active_gaian, release_reason="voluntary")
        bond = mgr.get_active_steward(active_gaian)
        assert bond is None

    def test_adopt_creates_new_primary_bond(self, mgr, active_gaian):
        mgr.enter_adoptable(active_gaian, release_reason="voluntary")
        mgr.adopt(active_gaian, new_steward_id="steward-bob")
        bond = mgr.get_active_steward(active_gaian)
        assert bond is not None
        assert bond.steward_id == "steward-bob"

    def test_assign_custodian_while_adoptable(self, mgr, active_gaian):
        mgr.enter_adoptable(active_gaian, release_reason="gone")
        custodian_bond = mgr.assign_custodian(active_gaian, custodian_id="custodian-c")
        assert custodian_bond.role == StewardRole.CUSTODIAN

    def test_custodian_not_assignable_while_active(self, mgr, active_gaian):
        with pytest.raises(ValueError):
            mgr.assign_custodian(active_gaian, custodian_id="custodian-c")

    def test_duplicate_primary_bond_raises(self, mgr, active_gaian):
        # Attempting to genesis a second PRIMARY bond on same GAIAN
        from core.lifecycle.stewardship import StewardshipRegistry, StewardRole
        registry = mgr._stewards
        with pytest.raises(ValueError, match="already has an active PRIMARY steward"):
            registry.create_bond(active_gaian, steward_id="interloper", role=StewardRole.PRIMARY)


# ---------------------------------------------------------------------------
# §6  Audit Logging & HMAC Integrity
# ---------------------------------------------------------------------------

class TestAuditLogging:

    def test_log_entries_created_on_transition(self, mgr, active_gaian):
        log = mgr.get_audit_log(active_gaian)
        # Expect: ANNOTATION (register), GENESIS, ACTIVATION = 3 entries minimum
        assert len(log) >= 3

    def test_log_entries_have_required_fields(self, mgr, active_gaian):
        log = mgr.get_audit_log(active_gaian)
        for entry in log:
            assert "event_id" in entry
            assert "gaian_id" in entry
            assert "event_type" in entry
            assert "occurred_at" in entry
            assert "signature" in entry
            assert "seq" in entry

    def test_hmac_chain_valid_after_transitions(self, mgr, active_gaian):
        mgr.enter_dormancy(active_gaian)
        mgr.exit_dormancy(active_gaian)
        mgr.retire(active_gaian, reason="test")
        assert mgr.verify_log_integrity(active_gaian) is True

    def test_tampered_log_fails_verification(self, mgr, active_gaian):
        log_internal = mgr._logger._log[active_gaian]
        # Tamper with the first event's payload
        log_internal[0].payload["tampered"] = True
        # Signature no longer matches the canonical form
        assert mgr.verify_log_integrity(active_gaian) is False

    def test_monotonic_sequence_numbers(self, mgr, active_gaian):
        log = mgr.get_audit_log(active_gaian)
        seqs = [e["seq"] for e in log]
        assert seqs == list(range(len(seqs)))

    def test_prev_sig_chaining(self, mgr, active_gaian):
        log_internal = mgr._logger._log[active_gaian]
        for i, event in enumerate(log_internal):
            if i == 0:
                assert event.prev_sig == ""
            else:
                assert event.prev_sig == log_internal[i - 1].signature
