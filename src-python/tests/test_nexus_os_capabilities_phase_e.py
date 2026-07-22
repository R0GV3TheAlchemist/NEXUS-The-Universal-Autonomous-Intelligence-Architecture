# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS OS — seL4 Capability Tokens — Phase E Test Suite
# Tests: CapabilityToken (immutability, allows, expiry), CNode (slot management,
#        lookup, delegation), CapabilityAuthority (mint, revoke, delegate, audit,
#        persistence, privilege escalation guard), NexusKernel (boot, spawn,
#        terminate, reap, mint, revoke, full lifecycle), Ledger integration.

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from nexus_os import (
    AuditRecord,
    CapabilityAuthority,
    CapabilityExpired,
    CapabilityNotFound,
    CapabilityRevoked,
    CapabilityToken,
    CNode,
    InvalidProcessState,
    KERNEL_PID,
    KernelAlreadyBooted,
    KernelNotBooted,
    NexusKernel,
    OPS_AFFECT,
    OPS_IPC,
    OPS_MANAGE,
    OPS_MEMORY,
    OPS_MEMORY_STORE,
    OPS_PROCESS,
    OPS_READ,
    OPS_READ_WRITE,
    OPS_SCHUMANN,
    OPS_WRITE,
    PrivilegeEscalationError,
    ProcessDescriptor,
    ProcessNotFound,
    ProcessNotTerminated,
    ProcessState,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth(tmp_path: Path) -> CapabilityAuthority:
    return CapabilityAuthority(db_path=tmp_path / "cap.db")


@pytest.fixture
def booted_kernel(tmp_path: Path) -> NexusKernel:
    auth = CapabilityAuthority(db_path=tmp_path / "cap.db")
    k = NexusKernel(authority=auth)
    k.boot()
    return k


# ---------------------------------------------------------------------------
# CapabilityToken unit tests
# ---------------------------------------------------------------------------

class TestCapabilityToken:
    def _make(self, ops=None, expiry=None):
        return CapabilityToken(
            token_id="t-001",
            object_id="schumann_sync",
            permitted_ops=frozenset(ops or ["read"]),
            issuer=KERNEL_PID,
            issued_at=datetime.now(timezone.utc),
            expiry=expiry,
        )

    def test_allows_permitted_op(self):
        t = self._make(["read", "write"])
        assert t.allows("read") is True
        assert t.allows("write") is True

    def test_denies_unpermitted_op(self):
        t = self._make(["read"])
        assert t.allows("write") is False

    def test_not_expired_by_default(self):
        assert self._make().is_expired() is False

    def test_expired_token(self):
        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert self._make(expiry=past).is_expired() is True

    def test_future_expiry_not_expired(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        assert self._make(expiry=future).is_expired() is False

    def test_frozen_immutable(self):
        t = self._make()
        with pytest.raises((AttributeError, TypeError)):
            t.token_id = "hacked"  # type: ignore

    def test_str_repr(self):
        t = self._make(["read"])
        assert "schumann_sync" in str(t)
        assert "read" in str(t)


# ---------------------------------------------------------------------------
# CNode tests
# ---------------------------------------------------------------------------

class TestCNode:
    def _token(self, obj="memory", ops=None, token_id=None):
        return CapabilityToken(
            token_id=token_id or str(__import__("uuid").uuid4()),
            object_id=obj,
            permitted_ops=frozenset(ops or ["read"]),
            issuer=KERNEL_PID,
            issued_at=datetime.now(timezone.utc),
        )

    def test_insert_and_lookup(self):
        cnode = CNode("pid-test")
        t = self._token(ops=["read", "write"])
        cnode.insert(t)
        found = cnode.lookup("memory", "read")
        assert found.token_id == t.token_id

    def test_lookup_missing_raises(self):
        cnode = CNode("pid-test")
        with pytest.raises(CapabilityNotFound):
            cnode.lookup("missing_object", "read")

    def test_has_returns_true(self):
        cnode = CNode("pid-test")
        cnode.insert(self._token(ops=["write"]))
        assert cnode.has("memory", "write") is True

    def test_has_returns_false_wrong_op(self):
        cnode = CNode("pid-test")
        cnode.insert(self._token(ops=["read"]))
        assert cnode.has("memory", "write") is False

    def test_delete_removes_token(self):
        cnode = CNode("pid-test")
        t = self._token()
        cnode.insert(t)
        cnode.delete(t.token_id)
        assert len(cnode) == 0

    def test_list_tokens(self):
        cnode = CNode("pid-test")
        for i in range(3):
            cnode.insert(self._token(obj=f"obj-{i}"))
        assert len(cnode.list_tokens()) == 3

    def test_expired_lookup_raises(self):
        cnode = CNode("pid-test")
        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        t = self._token(expiry=past)
        cnode.insert(t)
        with pytest.raises(CapabilityExpired):
            cnode.lookup("memory", "read")


# ---------------------------------------------------------------------------
# CapabilityAuthority tests
# ---------------------------------------------------------------------------

class TestCapabilityAuthority:
    def test_mint_returns_token(self, auth):
        t = auth.mint("schumann", OPS_SCHUMANN, KERNEL_PID)
        assert isinstance(t, CapabilityToken)
        assert "read" in t.permitted_ops

    def test_require_passes(self, auth):
        t = auth.mint("mem", OPS_READ, KERNEL_PID)
        found = auth.require(t.token_id, "read")
        assert found.token_id == t.token_id

    def test_require_wrong_op_raises(self, auth):
        t = auth.mint("mem", OPS_READ, KERNEL_PID)
        with pytest.raises(CapabilityNotFound):
            auth.require(t.token_id, "write")

    def test_revoke_raises_on_require(self, auth):
        t = auth.mint("mem", OPS_READ, KERNEL_PID)
        auth.revoke(t.token_id, KERNEL_PID)
        with pytest.raises(CapabilityRevoked):
            auth.require(t.token_id, "read")

    def test_revoke_idempotent(self, auth):
        t = auth.mint("mem", OPS_READ, KERNEL_PID)
        auth.revoke(t.token_id, KERNEL_PID)
        auth.revoke(t.token_id, KERNEL_PID)  # no error

    def test_delegate_subset(self, auth):
        source = auth.mint("ipc", OPS_READ_WRITE, KERNEL_PID)
        derived = auth.delegate(source, OPS_READ, delegate_pid="pid-child")
        assert "read" in derived.permitted_ops
        assert "write" not in derived.permitted_ops

    def test_delegate_escalation_blocked(self, auth):
        source = auth.mint("ipc", OPS_READ, KERNEL_PID)
        with pytest.raises(PrivilegeEscalationError):
            auth.delegate(source, OPS_READ_WRITE, delegate_pid="pid-evil")

    def test_delegate_revoked_source_blocked(self, auth):
        source = auth.mint("ipc", OPS_READ_WRITE, KERNEL_PID)
        auth.revoke(source.token_id, KERNEL_PID)
        with pytest.raises(CapabilityRevoked):
            auth.delegate(source, OPS_READ, delegate_pid="pid-x")

    def test_audit_log_populated(self, auth):
        auth.mint("obj", OPS_READ, KERNEL_PID)
        log = auth.get_audit_log()
        assert len(log) >= 1
        assert any(r.event_type == "mint" for r in log)

    def test_persist_across_restart(self, tmp_path):
        db = tmp_path / "persist.db"
        a1 = CapabilityAuthority(db_path=db)
        t = a1.mint("obj", OPS_READ, KERNEL_PID)
        a1.revoke(t.token_id, KERNEL_PID)
        a2 = CapabilityAuthority(db_path=db)
        with pytest.raises(CapabilityRevoked):
            a2.require(t.token_id, "read")

    def test_expired_token_raises_on_require(self, auth):
        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        t = auth.mint("obj", OPS_READ, KERNEL_PID, expiry=past)
        with pytest.raises(CapabilityExpired):
            auth.require(t.token_id, "read")

    def test_ledger_called_on_mint(self, tmp_path):
        mock_ledger = MagicMock()
        a = CapabilityAuthority(db_path=tmp_path / "c.db", ledger=mock_ledger)
        a.mint("obj", OPS_READ, KERNEL_PID)
        mock_ledger.append.assert_called_once()


# ---------------------------------------------------------------------------
# NexusKernel full lifecycle tests
# ---------------------------------------------------------------------------

class TestNexusKernel:
    def test_boot_sets_booted(self, booted_kernel):
        assert booted_kernel.booted is True

    def test_double_boot_raises(self, booted_kernel):
        with pytest.raises(KernelAlreadyBooted):
            booted_kernel.boot()

    def test_kernel_pid0_registered(self, booted_kernel):
        procs = booted_kernel.list_processes()
        pids = [p.pid for p in procs]
        assert NexusKernel.KERNEL_PID in pids

    def test_pid0_has_root_capabilities(self, booted_kernel):
        proc = booted_kernel.get_process(NexusKernel.KERNEL_PID)
        assert len(proc.tokens) > 0
        objects = {t.object_id for t in proc.tokens}
        assert "sovereign_memory" in objects
        assert "affect_engine" in objects
        assert "schumann_sync" in objects

    def test_spawn_creates_process(self, booted_kernel):
        proc = booted_kernel.spawn("test-agent", owner_id=NexusKernel.KERNEL_PID)
        assert proc.state == ProcessState.RUNNING
        assert proc.name == "test-agent"

    def test_spawn_with_initial_ops(self, booted_kernel):
        proc = booted_kernel.spawn(
            "affect-reader",
            owner_id=NexusKernel.KERNEL_PID,
            initial_ops={"affect_engine": OPS_READ},
        )
        assert proc.has_capability("affect_engine", "read")

    def test_mint_capability(self, booted_kernel):
        proc = booted_kernel.spawn("minter", owner_id=NexusKernel.KERNEL_PID)
        token = booted_kernel.mint_capability(
            object_id="sovereign_memory",
            permitted_ops=OPS_READ,
            issuer_pid=proc.pid,
        )
        assert token.allows("read")
        assert not token.allows("write")

    def test_mint_unknown_issuer_raises(self, booted_kernel):
        with pytest.raises(ProcessNotFound):
            booted_kernel.mint_capability(
                object_id="obj",
                permitted_ops=OPS_READ,
                issuer_pid="pid-does-not-exist",
            )

    def test_terminate_revokes_tokens(self, booted_kernel):
        proc = booted_kernel.spawn("doomed", owner_id=NexusKernel.KERNEL_PID)
        token = booted_kernel.mint_capability("obj", OPS_READ, proc.pid)
        booted_kernel.terminate(proc.pid, reason="test")
        assert proc.state == ProcessState.TERMINATED
        with pytest.raises(CapabilityRevoked):
            booted_kernel._authority.require(token.token_id, "read")

    def test_terminate_idempotent(self, booted_kernel):
        proc = booted_kernel.spawn("doomed2", owner_id=NexusKernel.KERNEL_PID)
        booted_kernel.terminate(proc.pid)
        booted_kernel.terminate(proc.pid)  # should not raise

    def test_reap_removes_process(self, booted_kernel):
        proc = booted_kernel.spawn("reaped", owner_id=NexusKernel.KERNEL_PID)
        booted_kernel.terminate(proc.pid)
        booted_kernel.reap(proc.pid)
        with pytest.raises(ProcessNotFound):
            booted_kernel.get_process(proc.pid)

    def test_reap_non_terminated_raises(self, booted_kernel):
        proc = booted_kernel.spawn("alive", owner_id=NexusKernel.KERNEL_PID)
        with pytest.raises(ProcessNotTerminated):
            booted_kernel.reap(proc.pid)

    def test_suspend_and_resume(self, booted_kernel):
        proc = booted_kernel.spawn("pausable", owner_id=NexusKernel.KERNEL_PID)
        booted_kernel.suspend(proc.pid, reason="test")
        assert proc.state == ProcessState.SUSPENDED
        booted_kernel.resume(proc.pid)
        assert proc.state == ProcessState.RUNNING

    def test_operations_before_boot_raise(self, tmp_path):
        k = NexusKernel(authority=CapabilityAuthority(db_path=tmp_path / "c.db"))
        with pytest.raises(KernelNotBooted):
            k.list_processes()

    def test_audit_log_has_boot_event(self, booted_kernel):
        log = booted_kernel.audit_log
        event_types = [r.event_type for r in log]
        assert "boot" in event_types or "mint" in event_types

    def test_concurrent_spawn_thread_safe(self, booted_kernel):
        errors: list[Exception] = []

        def do_spawn(i):
            try:
                booted_kernel.spawn(f"agent-{i}", owner_id=NexusKernel.KERNEL_PID)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=do_spawn, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []

    def test_ledger_wired_on_boot(self, tmp_path):
        mock_ledger = MagicMock()
        auth = CapabilityAuthority(db_path=tmp_path / "c.db", ledger=mock_ledger)
        k = NexusKernel(authority=auth, ledger=mock_ledger)
        k.boot()
        assert mock_ledger.append.call_count >= 7  # 7 root caps minted
