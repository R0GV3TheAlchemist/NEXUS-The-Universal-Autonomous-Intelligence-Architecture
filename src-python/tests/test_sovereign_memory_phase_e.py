# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Sovereign Memory — Phase E operational test suite
# Tests: ConsentGate (grant/revoke/check/require/status/expiry/bootstrap),
#        SovereignMemory (all CRUD ops, consent enforcement, Ledger wiring,
#        persistence across restart, concurrent writes).

from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sovereign_memory import (
    BiometricSnapshot,
    ConsentDenied,
    ConsentGate,
    ConsentScope,
    EpisodicRecord,
    SemanticFact,
    SovereignMemory,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def gate(tmp_path: Path) -> ConsentGate:
    return ConsentGate(db_path=tmp_path / "consent.db")


@pytest.fixture
def mem(tmp_path: Path) -> SovereignMemory:
    g = ConsentGate(db_path=tmp_path / "consent.db")
    m = SovereignMemory(
        db_path=tmp_path / "memory.db",
        consent_gate=g,
    )
    m.open()
    yield m
    m.close()


# ---------------------------------------------------------------------------
# ConsentGate tests
# ---------------------------------------------------------------------------

class TestConsentGate:
    def test_bootstrap_grants_all(self, gate):
        assert gate.check(ConsentScope.EPISODIC_WRITE) is True
        assert gate.check(ConsentScope.BIOMETRIC_READ) is True

    def test_grant_specific_scope(self, tmp_path):
        g = ConsentGate(db_path=tmp_path / "c2.db")
        g.revoke(ConsentScope.ALL)
        g.grant(ConsentScope.EPISODIC_WRITE, granted_by="owner")
        assert g.check(ConsentScope.EPISODIC_WRITE) is True
        assert g.check(ConsentScope.SEMANTIC_WRITE) is False

    def test_revoke_removes_access(self, gate):
        gate.revoke(ConsentScope.ALL)
        assert gate.check(ConsentScope.EPISODIC_WRITE) is False

    def test_require_passes_when_granted(self, gate):
        gate.require(ConsentScope.EPISODIC_WRITE)  # should not raise

    def test_require_raises_when_revoked(self, gate):
        gate.revoke(ConsentScope.ALL)
        with pytest.raises(ConsentDenied) as exc_info:
            gate.require(ConsentScope.EPISODIC_WRITE)
        assert "episodic_write" in str(exc_info.value)

    def test_omnibus_all_covers_any_scope(self, tmp_path):
        g = ConsentGate(db_path=tmp_path / "c3.db")
        g.revoke(ConsentScope.ALL)
        g.grant(ConsentScope.ALL)
        assert g.check(ConsentScope.BIOMETRIC_WRITE) is True
        assert g.check(ConsentScope.LEDGER_WRITE) is True

    def test_status_returns_all_active(self, gate):
        s = gate.status()
        assert "all" in s
        assert s["all"] == "active"

    def test_consent_persists_across_restart(self, tmp_path):
        db = tmp_path / "persist.db"
        g1 = ConsentGate(db_path=db)
        g1.revoke(ConsentScope.ALL)
        g1.grant(ConsentScope.EPISODIC_WRITE)
        # Simulate restart
        g2 = ConsentGate(db_path=db)
        assert g2.check(ConsentScope.EPISODIC_WRITE) is True
        assert g2.check(ConsentScope.SEMANTIC_WRITE) is False

    def test_all_scopes_enumerated(self):
        scopes = list(ConsentScope)
        assert ConsentScope.ALL in scopes
        assert len(scopes) >= 7


# ---------------------------------------------------------------------------
# SovereignMemory — episodic tests
# ---------------------------------------------------------------------------

class TestEpisodicMemory:
    def test_store_and_retrieve(self, mem):
        rec = EpisodicRecord.new("NEXUS Phase E is live", affect_tag="focused")
        mem.store_episodic(rec)
        results = mem.retrieve_episodic(limit=10)
        assert any(r.record_id == rec.record_id for r in results)

    def test_retrieve_respects_limit(self, mem):
        for i in range(20):
            mem.store_episodic(EpisodicRecord.new(f"event {i}"))
        results = mem.retrieve_episodic(limit=5)
        assert len(results) == 5

    def test_retrieve_by_affect_tag(self, mem):
        mem.store_episodic(EpisodicRecord.new("calm moment", affect_tag="calm"))
        mem.store_episodic(EpisodicRecord.new("focused moment", affect_tag="focused"))
        results = mem.retrieve_episodic(affect_tag="calm")
        assert all(r.affect_tag == "calm" for r in results)

    def test_count_episodic(self, mem):
        mem.store_episodic(EpisodicRecord.new("a"))
        mem.store_episodic(EpisodicRecord.new("b"))
        assert mem.count_episodic() == 2

    def test_consent_denied_on_write(self, tmp_path):
        g = ConsentGate(db_path=tmp_path / "c.db")
        g.revoke(ConsentScope.ALL)
        m = SovereignMemory(db_path=tmp_path / "m.db", consent_gate=g)
        m.open()
        with pytest.raises(ConsentDenied):
            m.store_episodic(EpisodicRecord.new("blocked"))
        m.close()

    def test_consent_denied_on_read(self, tmp_path):
        g = ConsentGate(db_path=tmp_path / "c.db")
        g.revoke(ConsentScope.ALL)
        m = SovereignMemory(db_path=tmp_path / "m.db", consent_gate=g)
        m.open()
        with pytest.raises(ConsentDenied):
            m.retrieve_episodic()
        m.close()

    def test_metadata_round_trip(self, mem):
        rec = EpisodicRecord.new("meta test", session="s-001", importance=0.9)
        mem.store_episodic(rec)
        results = mem.retrieve_episodic(limit=1)
        assert results[0].metadata["session"] == "s-001"

    def test_persist_across_restart(self, tmp_path):
        g_path = tmp_path / "c.db"
        db = tmp_path / "m.db"
        m1 = SovereignMemory(db_path=db, consent_gate=ConsentGate(db_path=g_path))
        m1.open()
        m1.store_episodic(EpisodicRecord.new("persistent"))
        m1.close()
        m2 = SovereignMemory(db_path=db, consent_gate=ConsentGate(db_path=g_path))
        m2.open()
        assert m2.count_episodic() == 1
        m2.close()


# ---------------------------------------------------------------------------
# SovereignMemory — semantic tests
# ---------------------------------------------------------------------------

class TestSemanticMemory:
    def test_store_and_query(self, mem):
        fact = SemanticFact.new("NEXUS", "is_phase", "E")
        mem.store_fact(fact)
        results = mem.query_facts(subject="NEXUS")
        assert any(f.fact_id == fact.fact_id for f in results)

    def test_query_by_predicate(self, mem):
        mem.store_fact(SemanticFact.new("Kyle", "builds", "NEXUS"))
        mem.store_fact(SemanticFact.new("Kyle", "loves", "alchemy"))
        results = mem.query_facts(predicate="builds")
        assert all(f.predicate == "builds" for f in results)

    def test_count_facts(self, mem):
        mem.store_fact(SemanticFact.new("A", "rel", "B"))
        mem.store_fact(SemanticFact.new("C", "rel", "D"))
        assert mem.count_facts() == 2

    def test_consent_denied_semantic_write(self, tmp_path):
        g = ConsentGate(db_path=tmp_path / "c.db")
        g.revoke(ConsentScope.ALL)
        m = SovereignMemory(db_path=tmp_path / "m.db", consent_gate=g)
        m.open()
        with pytest.raises(ConsentDenied):
            m.store_fact(SemanticFact.new("X", "y", "Z"))
        m.close()


# ---------------------------------------------------------------------------
# SovereignMemory — biometric tests
# ---------------------------------------------------------------------------

class TestBiometricMemory:
    def test_store_and_retrieve(self, mem):
        snap = BiometricSnapshot.new(heart_rate=72.0, hrv=45.0)
        mem.store_biometric(snap)
        results = mem.retrieve_biometric(limit=5)
        assert any(r.snapshot_id == snap.snapshot_id for r in results)

    def test_consent_denied_biometric(self, tmp_path):
        g = ConsentGate(db_path=tmp_path / "c.db")
        g.revoke(ConsentScope.ALL)
        m = SovereignMemory(db_path=tmp_path / "m.db", consent_gate=g)
        m.open()
        with pytest.raises(ConsentDenied):
            m.store_biometric(BiometricSnapshot.new(heart_rate=60.0))
        m.close()

    def test_partial_biometric(self, mem):
        snap = BiometricSnapshot.new(heart_rate=68.0)
        mem.store_biometric(snap)
        results = mem.retrieve_biometric(limit=1)
        assert results[0].hrv is None
        assert results[0].heart_rate == 68.0


# ---------------------------------------------------------------------------
# Ledger integration
# ---------------------------------------------------------------------------

class TestLedgerIntegration:
    def test_ledger_called_on_episodic_write(self, tmp_path):
        mock_ledger = MagicMock()
        g = ConsentGate(db_path=tmp_path / "c.db")
        m = SovereignMemory(
            db_path=tmp_path / "m.db",
            consent_gate=g,
            ledger=mock_ledger,
        )
        m.open()
        m.store_episodic(EpisodicRecord.new("ledger test"))
        mock_ledger.append.assert_called_once()
        m.close()

    def test_ledger_event_type_is_memory_commit(self, tmp_path):
        from planetary_ledger import EventType
        mock_ledger = MagicMock()
        g = ConsentGate(db_path=tmp_path / "c.db")
        m = SovereignMemory(
            db_path=tmp_path / "m.db",
            consent_gate=g,
            ledger=mock_ledger,
        )
        m.open()
        m.store_fact(SemanticFact.new("K", "is", "Alchemist"))
        call_kwargs = mock_ledger.append.call_args.kwargs
        assert call_kwargs["event_type"] == EventType.MEMORY_COMMIT
        m.close()

    def test_no_ledger_runs_cleanly(self, mem):
        # mem fixture has no ledger — should not raise
        mem.store_episodic(EpisodicRecord.new("no ledger"))
        assert mem.count_episodic() == 1


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------

class TestConcurrency:
    def test_concurrent_writes_thread_safe(self, mem):
        errors: list[Exception] = []

        def write(i: int) -> None:
            try:
                mem.store_episodic(EpisodicRecord.new(f"concurrent {i}"))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert mem.count_episodic() == 20
