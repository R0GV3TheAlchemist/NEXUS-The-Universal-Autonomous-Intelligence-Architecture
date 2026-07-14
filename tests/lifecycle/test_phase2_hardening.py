"""
tests/lifecycle/test_phase2_hardening.py
C27 Phase 2 hardening — signing, vault, 180-day gate, legacy package
"""

import pytest
from datetime import datetime, timedelta, timezone

from core.lifecycle import (
    LifecycleManager,
    PermissionEnvelope,
    GAIANLifecycleState,
    RetirementReason,
    InProcessVault,
    Ed25519LifecycleSigner,
)


def _active_mgr(gaian_id: str = "g-harden") -> tuple:
    vault = InProcessVault()
    vault.generate_key("test-key")
    signer = Ed25519LifecycleSigner(vault=vault, key_id="test-key")
    mgr = LifecycleManager(signer=signer)
    mgr.register_latent(gaian_id)
    mgr.genesis(gaian_id, steward_id="steward-alpha")
    mgr.activate(gaian_id, actor_id="steward-alpha",
                 justification="orientation complete", trigger_class="STEWARD_ACTION")
    return mgr, gaian_id


class TestEd25519Signing:

    def test_canonical_log_entries_signed(self):
        mgr, gid = _active_mgr()
        entries = mgr._get_record(gid).canonical_audit
        assert len(entries) >= 2
        for e in entries:
            assert e.signature.algorithm == "Ed25519"
            assert len(e.signature.value) > 0

    def test_canonical_chain_valid(self):
        mgr, gid = _active_mgr()
        mgr.enter_dormancy(gid, reason="test")
        mgr.exit_dormancy(gid)
        assert mgr.verify_canonical_chain(gid) is True

    def test_tampered_canonical_entry_fails_verification(self):
        mgr, gid = _active_mgr()
        entries = mgr._get_record(gid).canonical_audit
        entries[0].justification = "TAMPERED"
        assert mgr.verify_canonical_chain(gid) is False

    def test_vault_missing_key_raises(self):
        vault = InProcessVault()
        with pytest.raises(Exception):  # noqa: B017
            vault.get_private_key("nonexistent-key")

    def test_signer_verify_valid_entry(self):
        vault = InProcessVault()
        vault.generate_key("k1")
        signer = Ed25519LifecycleSigner(vault=vault, key_id="k1")
        mgr = LifecycleManager(signer=signer)
        gid = "g-verify"
        mgr.register_latent(gid)
        mgr.genesis(gid, steward_id="s1")
        entries = mgr._get_record(gid).canonical_audit
        assert signer.verify(entries[0]) is True


class TestRetirementLegacyPackage:

    def test_retire_returns_legacy_package(self):
        mgr, gid = _active_mgr()
        legacy = mgr.retire(
            gid,
            reason="mission complete",
            actor_id="steward-alpha",
            retirement_reason=RetirementReason.STEWARD_INITIATED,
            waive_notice=True,
            contributions=["analysis-v1", "report-2026"],
            knowledge_artifacts=["kb-entry-42"],
            memory_data=b"serialised memory blob",
        )
        assert legacy.gaian_id == gid
        assert legacy.memory_seal_hash != ""
        assert "analysis-v1" in legacy.contributions
        assert mgr.get_state(gid) == GAIANLifecycleState.RETIRED

    def test_legacy_package_retrievable_post_retirement(self):
        mgr, gid = _active_mgr()
        mgr.retire(gid, reason="done", waive_notice=True)
        pkg = mgr.get_legacy_package(gid)
        assert pkg is not None
        assert pkg.gaian_id == gid

    def test_retire_notice_period_enforced(self):
        mgr, gid = _active_mgr()
        mgr.initiate_retirement(gid, reason=RetirementReason.STEWARD_INITIATED,
                                justification="planned", waive_notice=False)
        with pytest.raises(ValueError, match="notice period has not elapsed"):
            from core.lifecycle.retirement_engine import RetirementEngine
            engine = mgr._retirement
            engine.complete_retirement(
                gaian_id=gid,
                audit_log=mgr.get_audit_log(gid),
                steward_history=[],
            )


class TestArchival180DayGate:

    def test_immediate_archive_blocked(self):
        mgr, gid = _active_mgr()
        mgr.retire(gid, reason="done", waive_notice=True)
        with pytest.raises(ValueError, match="180 days"):
            mgr.archive(gid)

    def test_archive_allowed_after_180_days(self):
        mgr, gid = _active_mgr()
        mgr.retire(gid, reason="done", waive_notice=True)
        record = mgr._get_record(gid)
        record.retired_at = datetime.now(timezone.utc) - timedelta(days=181)
        mgr.archive(gid)
        assert mgr.get_state(gid) == GAIANLifecycleState.ARCHIVED

    def test_archive_bypass_flag_works(self):
        mgr, gid = _active_mgr()
        mgr.retire(gid, reason="done", waive_notice=True)
        mgr.archive(gid, bypass_180_day_check=True)
        assert mgr.get_state(gid) == GAIANLifecycleState.ARCHIVED

    def test_archive_non_retired_still_blocked(self):
        mgr, gid = _active_mgr()
        from core.lifecycle import LifecycleTransitionError
        with pytest.raises((LifecycleTransitionError, ValueError)):
            mgr.archive(gid, bypass_180_day_check=True)
