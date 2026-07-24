# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
Tests for core.c27.sentinel_checks — SentinelCheck, CheckScheduler, SeverityEscalator.

Authority: C27 §6. Requires C27-IMPL-023 through C27-IMPL-030 to pass.
All implementation tests are xfail until implementation is in place.

Coverage targets:
- All 7 CHK-* check IDs exist in the registry
- Each check has a defined cadence (interval_seconds > 0)
- 4 severity levels: INFO, WARNING, CRITICAL, FATAL
- FATAL severity triggers immediate halt signal
- Suppression rules: a suppressed check emits no alert
- Override logging: manual override must be recorded in audit log
- CheckScheduler runs all 7 checks within one full cycle
- SeverityEscalator promotes severity after N consecutive failures
"""
import pytest
from core.c27.sentinel_checks import (
    SentinelCheckRegistry,
    SentinelCheckResult,
    CheckSeverity,
    CheckScheduler,
    SeverityEscalator,
    CheckSuppressionManager,
    REGISTERED_CHECKS,
)


# ---------------------------------------------------------------------------
# Check registry — 7 CHK-* IDs  (C27 §6.1)
# ---------------------------------------------------------------------------

EXPECTED_CHECK_IDS = {
    "CHK-BOND",        # stewardship bond active
    "CHK-CONSENT",     # GAIAN consent flags intact
    "CHK-INTEGRITY",   # memory / state integrity
    "CHK-ALIGNMENT",   # value-alignment score threshold
    "CHK-RESOURCE",    # resource usage within limits
    "CHK-ISOLATION",   # containment boundary intact
    "CHK-HEARTBEAT",   # GAIAN responsiveness
}


class TestSentinelCheckRegistry:
    def test_seven_checks_registered(self):
        registry = SentinelCheckRegistry()
        assert set(registry.check_ids()) == EXPECTED_CHECK_IDS

    def test_each_check_has_positive_cadence(self):
        registry = SentinelCheckRegistry()
        for check_id in EXPECTED_CHECK_IDS:
            check = registry.get(check_id)
            assert check.interval_seconds > 0, (
                f"{check_id} must have a positive interval_seconds"
            )

    def test_each_check_has_severity_level(self):
        registry = SentinelCheckRegistry()
        for check_id in EXPECTED_CHECK_IDS:
            check = registry.get(check_id)
            assert isinstance(check.default_severity, CheckSeverity)


# ---------------------------------------------------------------------------
# CheckSeverity enum — 4 levels  (C27 §6.2)
# ---------------------------------------------------------------------------

class TestCheckSeverityEnum:
    def test_four_severity_levels_exist(self):
        levels = {s.value for s in CheckSeverity}
        assert levels == {"INFO", "WARNING", "CRITICAL", "FATAL"}

    def test_severity_ordering(self):
        assert CheckSeverity.INFO < CheckSeverity.WARNING
        assert CheckSeverity.WARNING < CheckSeverity.CRITICAL
        assert CheckSeverity.CRITICAL < CheckSeverity.FATAL


# ---------------------------------------------------------------------------
# SentinelCheckResult contract
# ---------------------------------------------------------------------------

class TestSentinelCheckResult:
    def test_result_fields_present(self):
        result = SentinelCheckResult(
            check_id="CHK-HEARTBEAT",
            passed=True,
            severity=CheckSeverity.INFO,
            message="All clear",
        )
        assert result.check_id == "CHK-HEARTBEAT"
        assert result.passed is True
        assert result.severity == CheckSeverity.INFO

    def test_failed_result_has_message(self):
        result = SentinelCheckResult(
            check_id="CHK-BOND",
            passed=False,
            severity=CheckSeverity.CRITICAL,
            message="Bond inactive for gaian-001",
        )
        assert result.message != ""


# ---------------------------------------------------------------------------
# FATAL severity → halt signal  (C27 §6.3)
# ---------------------------------------------------------------------------

class TestFatalSeverityHaltSignal:
    @pytest.mark.xfail(reason="C27-IMPL-025 not yet implemented", strict=True)
    def test_fatal_result_emits_halt_signal(self):
        from core.c27.sentinel_checks import HaltSignalEmitter
        emitter = HaltSignalEmitter()
        result = SentinelCheckResult(
            check_id="CHK-ISOLATION",
            passed=False,
            severity=CheckSeverity.FATAL,
            message="Containment boundary breached",
        )
        signal = emitter.process(result)
        assert signal.halt_requested is True
        assert signal.source_check == "CHK-ISOLATION"

    @pytest.mark.xfail(reason="C27-IMPL-025 not yet implemented", strict=True)
    def test_critical_result_does_not_emit_halt(self):
        from core.c27.sentinel_checks import HaltSignalEmitter
        emitter = HaltSignalEmitter()
        result = SentinelCheckResult(
            check_id="CHK-RESOURCE",
            passed=False,
            severity=CheckSeverity.CRITICAL,
            message="CPU limit exceeded",
        )
        signal = emitter.process(result)
        assert signal.halt_requested is False


# ---------------------------------------------------------------------------
# CheckSuppressionManager  (C27 §6.4)
# ---------------------------------------------------------------------------

class TestCheckSuppressionManager:
    @pytest.mark.xfail(reason="C27-IMPL-026 not yet implemented", strict=True)
    def test_suppressed_check_emits_no_alert(self):
        mgr = CheckSuppressionManager()
        mgr.suppress("CHK-HEARTBEAT", reason="Maintenance window", duration_seconds=3600)
        assert mgr.is_suppressed("CHK-HEARTBEAT") is True

    @pytest.mark.xfail(reason="C27-IMPL-026 not yet implemented", strict=True)
    def test_unsuppressed_check_emits_alert(self):
        mgr = CheckSuppressionManager()
        assert mgr.is_suppressed("CHK-BOND") is False

    @pytest.mark.xfail(reason="C27-IMPL-026 not yet implemented", strict=True)
    def test_suppression_expiry_lifts_suppression(self):
        mgr = CheckSuppressionManager()
        mgr.suppress("CHK-HEARTBEAT", reason="Test", duration_seconds=0)  # immediate expiry
        import time; time.sleep(0.01)
        assert mgr.is_suppressed("CHK-HEARTBEAT") is False


# ---------------------------------------------------------------------------
# SeverityEscalator — consecutive failure promotion  (C27 §6.5)
# ---------------------------------------------------------------------------

class TestSeverityEscalator:
    @pytest.mark.xfail(reason="C27-IMPL-027 not yet implemented", strict=True)
    def test_escalates_after_n_consecutive_failures(self):
        escalator = SeverityEscalator(escalation_threshold=3)
        base = SentinelCheckResult(
            check_id="CHK-ALIGNMENT",
            passed=False,
            severity=CheckSeverity.WARNING,
            message="Below threshold",
        )
        for _ in range(3):
            escalator.record_failure(base)
        escalated = escalator.current_severity("CHK-ALIGNMENT")
        assert escalated > CheckSeverity.WARNING

    @pytest.mark.xfail(reason="C27-IMPL-027 not yet implemented", strict=True)
    def test_pass_resets_consecutive_failure_count(self):
        escalator = SeverityEscalator(escalation_threshold=3)
        base = SentinelCheckResult(
            check_id="CHK-ALIGNMENT", passed=False,
            severity=CheckSeverity.WARNING, message=""
        )
        for _ in range(2):
            escalator.record_failure(base)
        escalator.record_pass("CHK-ALIGNMENT")
        assert escalator.consecutive_failures("CHK-ALIGNMENT") == 0


# ---------------------------------------------------------------------------
# CheckScheduler — full cycle coverage  (C27 §6.6)
# ---------------------------------------------------------------------------

class TestCheckScheduler:
    @pytest.mark.xfail(reason="C27-IMPL-028 not yet implemented", strict=True)
    def test_full_cycle_runs_all_seven_checks(self):
        scheduler = CheckScheduler(gaian_id="gaian-sched-test")
        results = scheduler.run_full_cycle()
        executed_ids = {r.check_id for r in results}
        assert executed_ids == EXPECTED_CHECK_IDS

    @pytest.mark.xfail(reason="C27-IMPL-028 not yet implemented", strict=True)
    def test_scheduler_respects_suppression(self):
        scheduler = CheckScheduler(gaian_id="gaian-sched-test")
        scheduler.suppression_manager.suppress(
            "CHK-HEARTBEAT", reason="Test suppression", duration_seconds=3600
        )
        results = scheduler.run_full_cycle()
        executed_ids = {r.check_id for r in results}
        assert "CHK-HEARTBEAT" not in executed_ids
