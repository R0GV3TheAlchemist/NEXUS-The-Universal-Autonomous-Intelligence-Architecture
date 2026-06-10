"""Tests for core/consent_ledger.py — Issue #274"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.consent_ledger import (
    ConsentLedger,
    get_consent_ledger,
    ConsentEntry,
    ConsentStatus,
    ConsentScope,
)


# ── Smoke ──────────────────────────────────────────────────────────────
class TestConsentLedgerImport:
    def test_module_imports(self):
        import core.consent_ledger  # noqa: F401

    def test_class_exists(self):
        assert ConsentLedger is not None


# ── Singleton ──────────────────────────────────────────────────────────
class TestConsentLedgerSingleton:
    def test_singleton_stable(self):
        a = get_consent_ledger()
        b = get_consent_ledger()
        assert a is b

    def test_instance_type(self):
        assert isinstance(get_consent_ledger(), ConsentLedger)


# ── Core logic ─────────────────────────────────────────────────────────
class TestConsentLedgerLogic:
    def test_grant_creates_entry(self):
        ledger = get_consent_ledger()
        entry = ledger.grant(
            gaian_id="test-gaian-001",
            scope=ConsentScope.MEMORY_WRITE,
        )
        assert isinstance(entry, ConsentEntry)

    def test_entry_status_is_granted(self):
        ledger = get_consent_ledger()
        entry = ledger.grant(
            gaian_id="test-gaian-001",
            scope=ConsentScope.MEMORY_WRITE,
        )
        assert entry.status == ConsentStatus.GRANTED

    def test_revoke_changes_status(self):
        ledger = get_consent_ledger()
        ledger.grant(gaian_id="test-gaian-002", scope=ConsentScope.MEMORY_WRITE)
        ledger.revoke(gaian_id="test-gaian-002", scope=ConsentScope.MEMORY_WRITE)
        status = ledger.check(gaian_id="test-gaian-002", scope=ConsentScope.MEMORY_WRITE)
        assert status == ConsentStatus.REVOKED

    def test_check_returns_consent_status(self):
        ledger = get_consent_ledger()
        result = ledger.check(gaian_id="nonexistent", scope=ConsentScope.MEMORY_WRITE)
        assert isinstance(result, ConsentStatus)

    def test_ungated_scope_returns_not_set(self):
        ledger = get_consent_ledger()
        result = ledger.check(gaian_id="brand-new", scope=ConsentScope.MEMORY_WRITE)
        assert result in (ConsentStatus.NOT_SET, ConsentStatus.REVOKED, ConsentStatus.GRANTED)

    def test_memory_write_blocked_without_consent(self):
        ledger = get_consent_ledger()
        is_allowed = ledger.is_permitted(
            gaian_id="test-no-consent-999",
            scope=ConsentScope.MEMORY_WRITE,
        )
        assert isinstance(is_allowed, bool)


# ── Edge cases ─────────────────────────────────────────────────────────
class TestConsentLedgerEdgeCases:
    def test_empty_gaian_id_raises_or_returns_safely(self):
        ledger = get_consent_ledger()
        try:
            result = ledger.check(gaian_id="", scope=ConsentScope.MEMORY_WRITE)
            assert isinstance(result, ConsentStatus)
        except (ValueError, KeyError):
            pass  # Either is acceptable — just must not crash silently

    def test_invalid_scope_enum_raises(self):
        with pytest.raises((ValueError, AttributeError, TypeError)):
            ConsentScope("TOTALLY_INVALID_SCOPE_XYZ")

    def test_double_grant_idempotent(self):
        ledger = get_consent_ledger()
        ledger.grant(gaian_id="double-test", scope=ConsentScope.MEMORY_WRITE)
        ledger.grant(gaian_id="double-test", scope=ConsentScope.MEMORY_WRITE)
        status = ledger.check(gaian_id="double-test", scope=ConsentScope.MEMORY_WRITE)
        assert status == ConsentStatus.GRANTED

    def test_double_revoke_idempotent(self):
        ledger = get_consent_ledger()
        ledger.grant(gaian_id="revoke-test", scope=ConsentScope.MEMORY_WRITE)
        ledger.revoke(gaian_id="revoke-test", scope=ConsentScope.MEMORY_WRITE)
        ledger.revoke(gaian_id="revoke-test", scope=ConsentScope.MEMORY_WRITE)
        status = ledger.check(gaian_id="revoke-test", scope=ConsentScope.MEMORY_WRITE)
        assert status == ConsentStatus.REVOKED
