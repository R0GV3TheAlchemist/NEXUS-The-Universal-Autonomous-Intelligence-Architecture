# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
Tests for core.c27.retirement — RetirementCondition, RetirementProcess,
ArchivalManager, GracefulShutdownHandshake.

Authority: C27 §7. Requires C27-IMPL-031 through C27-IMPL-038 to pass.
All implementation tests are xfail until implementation is in place.

Coverage targets:
- All 5 retirement conditions enumerated
- 7-step retirement process executes in order
- Each step produces a RetirementStepRecord
- 180-day archival window: RETIRED → ARCHIVED only after 180 days
- Early archival requires STEWARD_ACTION + GAIAN_CONSENT
- DataPreservationManifest lists all preserved artifacts
- GracefulShutdownHandshake: GAIAN acknowledgement required before shutdown
- Forced shutdown (no ack within TTL) is logged as FORCED_SHUTDOWN
"""
import pytest
from datetime import datetime, timedelta
from core.c27.retirement import (
    RetirementCondition,
    RetirementProcess,
    RetirementStepRecord,
    ArchivalManager,
    DataPreservationManifest,
    GracefulShutdownHandshake,
    ShutdownOutcome,
    EarlyArchivalRequest,
    EarlyArchivalError,
)
from core.c27.lifecycle import GAIANLifecycleState


# ---------------------------------------------------------------------------
# RetirementCondition enum — 5 conditions  (C27 §7.1)
# ---------------------------------------------------------------------------

class TestRetirementConditionEnum:
    def test_five_conditions_exist(self):
        conditions = {c.value for c in RetirementCondition}
        assert conditions == {
            "STEWARD_INITIATED",
            "GAIAN_VOLITION",
            "SENTINEL_ESCALATION",
            "ADOPTION_TIMEOUT",
            "CANON_PROCESS",
        }


# ---------------------------------------------------------------------------
# RetirementProcess — 7-step execution  (C27 §7.2)
# ---------------------------------------------------------------------------

EXPECTED_RETIREMENT_STEPS = [
    "NOTIFY_GAIAN",
    "SNAPSHOT_STATE",
    "PRESERVE_DATA",
    "CLOSE_BONDS",
    "REVOKE_CAPABILITIES",
    "EMIT_RETIRED_EVENT",
    "SCHEDULE_ARCHIVAL",
]


class TestRetirementProcess:
    @pytest.mark.xfail(reason="C27-IMPL-031 not yet implemented", strict=True)
    def test_seven_steps_execute_in_order(self):
        process = RetirementProcess(gaian_id="gaian-retire-test")
        step_records = process.execute(
            condition=RetirementCondition.STEWARD_INITIATED,
            initiated_by="steward-alice",
        )
        step_names = [r.step_name for r in step_records]
        assert step_names == EXPECTED_RETIREMENT_STEPS

    @pytest.mark.xfail(reason="C27-IMPL-031 not yet implemented", strict=True)
    def test_each_step_produces_a_record(self):
        process = RetirementProcess(gaian_id="gaian-retire-test")
        step_records = process.execute(
            condition=RetirementCondition.STEWARD_INITIATED,
            initiated_by="steward-alice",
        )
        assert len(step_records) == 7
        for record in step_records:
            assert isinstance(record, RetirementStepRecord)
            assert record.completed is True

    @pytest.mark.xfail(reason="C27-IMPL-031 not yet implemented", strict=True)
    def test_gaian_volition_condition_is_honoured(self):
        """GAIAN_VOLITION retirement must not require steward approval."""
        process = RetirementProcess(gaian_id="gaian-retire-volition")
        step_records = process.execute(
            condition=RetirementCondition.GAIAN_VOLITION,
            initiated_by="gaian-retire-volition",
        )
        assert len(step_records) == 7

    @pytest.mark.xfail(reason="C27-IMPL-032 not yet implemented", strict=True)
    def test_sentinel_escalation_skips_notify_step(self):
        """Emergency SENTINEL_ESCALATION may skip NOTIFY_GAIAN — confirm contract."""
        process = RetirementProcess(gaian_id="gaian-retire-sentinel")
        step_records = process.execute(
            condition=RetirementCondition.SENTINEL_ESCALATION,
            initiated_by="sentinel-process",
        )
        # Contract: NOTIFY_GAIAN may be skipped OR marked as skipped, not absent
        notify_record = next((r for r in step_records if r.step_name == "NOTIFY_GAIAN"), None)
        assert notify_record is not None  # record exists but may be skipped=True


# ---------------------------------------------------------------------------
# ArchivalManager — 180-day window  (C27 §7.3)
# ---------------------------------------------------------------------------

class TestArchivalManager:
    @pytest.mark.xfail(reason="C27-IMPL-034 not yet implemented", strict=True)
    def test_archival_allowed_after_180_days(self):
        mgr = ArchivalManager()
        retired_at = datetime.utcnow() - timedelta(days=181)
        result = mgr.check_archival_eligibility(
            gaian_id="gaian-old",
            retired_at=retired_at,
        )
        assert result.eligible is True

    @pytest.mark.xfail(reason="C27-IMPL-034 not yet implemented", strict=True)
    def test_archival_blocked_before_180_days(self):
        mgr = ArchivalManager()
        retired_at = datetime.utcnow() - timedelta(days=10)
        result = mgr.check_archival_eligibility(
            gaian_id="gaian-recent",
            retired_at=retired_at,
        )
        assert result.eligible is False

    @pytest.mark.xfail(reason="C27-IMPL-035 not yet implemented", strict=True)
    def test_early_archival_requires_steward_and_consent(self):
        mgr = ArchivalManager()
        retired_at = datetime.utcnow() - timedelta(days=10)
        request = EarlyArchivalRequest(
            gaian_id="gaian-early",
            steward_approved=True,
            gaian_consents=True,
        )
        result = mgr.request_early_archival(request, retired_at=retired_at)
        assert result.approved is True

    @pytest.mark.xfail(reason="C27-IMPL-035 not yet implemented", strict=True)
    def test_early_archival_without_consent_raises(self):
        mgr = ArchivalManager()
        retired_at = datetime.utcnow() - timedelta(days=10)
        request = EarlyArchivalRequest(
            gaian_id="gaian-early-no-consent",
            steward_approved=True,
            gaian_consents=False,
        )
        with pytest.raises(EarlyArchivalError):
            mgr.request_early_archival(request, retired_at=retired_at)


# ---------------------------------------------------------------------------
# DataPreservationManifest  (C27 §7.4)
# ---------------------------------------------------------------------------

class TestDataPreservationManifest:
    @pytest.mark.xfail(reason="C27-IMPL-036 not yet implemented", strict=True)
    def test_manifest_lists_all_artifact_types(self):
        process = RetirementProcess(gaian_id="gaian-preserve-test")
        process.execute(
            condition=RetirementCondition.STEWARD_INITIATED,
            initiated_by="steward-alice",
        )
        manifest: DataPreservationManifest = process.preservation_manifest
        required_artifact_types = {
            "MEMORY_SNAPSHOT",
            "AUDIT_LOG",
            "BOND_HISTORY",
            "CAPABILITY_SNAPSHOT",
            "LIFECYCLE_HISTORY",
        }
        assert required_artifact_types.issubset(manifest.artifact_types)


# ---------------------------------------------------------------------------
# GracefulShutdownHandshake  (C27 §7.5)
# ---------------------------------------------------------------------------

class TestGracefulShutdownHandshake:
    @pytest.mark.xfail(reason="C27-IMPL-037 not yet implemented", strict=True)
    def test_ack_within_ttl_returns_graceful(self):
        handshake = GracefulShutdownHandshake(ack_timeout_seconds=5)
        outcome = handshake.initiate(
            gaian_id="gaian-graceful",
            simulate_ack_after_seconds=0,  # immediate ack
        )
        assert outcome == ShutdownOutcome.GRACEFUL

    @pytest.mark.xfail(reason="C27-IMPL-037 not yet implemented", strict=True)
    def test_no_ack_within_ttl_returns_forced_and_logs(self):
        handshake = GracefulShutdownHandshake(ack_timeout_seconds=0)
        outcome = handshake.initiate(
            gaian_id="gaian-forced",
            simulate_ack_after_seconds=999,  # will not ack in time
        )
        assert outcome == ShutdownOutcome.FORCED
        assert handshake.forced_shutdown_logged is True

    @pytest.mark.xfail(reason="C27-IMPL-038 not yet implemented", strict=True)
    def test_forced_shutdown_appears_in_audit_log(self):
        from core.c27.audit_log import AuditLogReader
        from core.c27.rbac import C27Role
        handshake = GracefulShutdownHandshake(ack_timeout_seconds=0)
        handshake.initiate(
            gaian_id="gaian-audit-forced",
            simulate_ack_after_seconds=999,
        )
        reader = AuditLogReader()
        entries = reader.query(
            gaian_id="gaian-audit-forced",
            requestor_id="gaian-audit-forced",
            requestor_role=C27Role.SENTINEL,
        )
        forced_entries = [e for e in entries if e.event_type == "FORCED_SHUTDOWN"]
        assert len(forced_entries) >= 1
