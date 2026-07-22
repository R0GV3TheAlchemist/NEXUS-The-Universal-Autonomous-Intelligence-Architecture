# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS OS — NexusKernel
# Phase E: All NotImplementedError stubs replaced with real, running code.
# seL4-inspired microkernel: capability minting, process lifecycle, audit log.
# Design: seL4 microkernel; NEXUS_UNIVERSAL_OS.md Domain 1.1
# Ethics: ETHICS.md Prohibition 6 — No Unaudited Privilege Escalation
# GAIAN Law III: No Silent Override

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, FrozenSet, Optional

logger = logging.getLogger("nexus_os.kernel")


# ---------------------------------------------------------------------------
# CapabilityToken — the unforgeable access token
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CapabilityToken:
    """
    An unforgeable, immutable token representing the right to perform a
    specific set of operations on a specific kernel object.

    Minted exclusively by NexusKernel / CapabilityAuthority.
    Possession of a token IS the permission — no separate ACL lookup.
    Reference: seL4 capability derivation; NEXUS_UNIVERSAL_OS.md 1.1
    """
    token_id:      str
    object_id:     str
    permitted_ops: FrozenSet[str]
    issuer:        str
    issued_at:     datetime
    expiry:        Optional[datetime] = None

    def allows(self, operation: str) -> bool:
        return operation in self.permitted_ops

    def is_expired(self) -> bool:
        if self.expiry is None:
            return False
        return datetime.now(timezone.utc) > self.expiry

    def __str__(self) -> str:
        return (
            f"CapabilityToken(object={self.object_id}, "
            f"ops={sorted(self.permitted_ops)}, issuer={self.issuer})"
        )


# ---------------------------------------------------------------------------
# Process model
# ---------------------------------------------------------------------------

class ProcessState(Enum):
    NASCENT    = auto()
    RUNNING    = auto()
    SUSPENDED  = auto()
    TERMINATED = auto()
    ZOMBIE     = auto()


@dataclass
class ProcessDescriptor:
    """
    Kernel-side descriptor for a running NEXUS OS process.
    Reference: NEXUS_UNIVERSAL_OS.md Domain 1.1 — Process Model
    """
    pid:        str            = field(default_factory=lambda: str(uuid.uuid4()))
    name:       str            = "unnamed-process"
    state:      ProcessState   = ProcessState.NASCENT
    owner_id:   str            = "nexus-kernel"
    created_at: datetime       = field(default_factory=lambda: datetime.now(timezone.utc))
    tokens:     list[CapabilityToken] = field(default_factory=list)

    def has_capability(self, object_id: str, operation: str) -> bool:
        return any(
            t.object_id == object_id and t.allows(operation) and not t.is_expired()
            for t in self.tokens
        )


# ---------------------------------------------------------------------------
# KernelError hierarchy
# ---------------------------------------------------------------------------

class KernelError(RuntimeError): ...
class KernelAlreadyBooted(KernelError): ...
class KernelNotBooted(KernelError): ...
class ProcessNotFound(KernelError): ...
class ProcessNotTerminated(KernelError): ...
class InvalidProcessState(KernelError): ...


# ---------------------------------------------------------------------------
# NexusKernel — Phase E: fully implemented
# ---------------------------------------------------------------------------

class NexusKernel:
    """
    The NEXUS Universal Operating System microkernel.

    Minimal privileged services:
      1. Capability minting and revocation (via CapabilityAuthority)
      2. Process lifecycle: spawn, terminate, reap
      3. Audit logging of ALL privileged operations

    No policy. Mechanisms only. Policy lives in userspace servers.
    Reference: seL4 design; NEXUS_UNIVERSAL_OS.md Domain 1

    Usage::

        kernel = NexusKernel()
        kernel.boot()
        proc = kernel.spawn("affect-engine", owner_id=KERNEL_PID)
        token = kernel.mint_capability(
            object_id="affect_state",
            permitted_ops=frozenset({"read", "write"}),
            issuer_pid=proc.pid,
        )
        assert token.allows("read")
        kernel.terminate(proc.pid, reason="test-complete")
        kernel.reap(proc.pid)
    """

    KERNEL_PID = "pid-0:nexus-kernel"

    def __init__(
        self,
        authority: Any | None = None,
        ledger: Any | None = None,
        session_id: str | None = None,
    ) -> None:
        self._processes: dict[str, ProcessDescriptor] = {}
        self._lock = threading.Lock()
        self._ledger = ledger
        self._session_id = session_id
        self._authority = authority  # injected or lazily created in boot()
        self.booted: bool = False
        logger.info("NexusKernel instance created — not yet booted.")

    # ------------------------------------------------------------------
    # Boot
    # ------------------------------------------------------------------

    def boot(self) -> None:
        """
        Execute the NEXUS kernel boot sequence.
        - Registers PID-0 (the kernel itself)
        - Initialises CapabilityAuthority if not injected
        - Mints root capabilities for all system objects
        - Sets self.booted = True
        Raises KernelAlreadyBooted if called more than once.
        """
        if self.booted:
            raise KernelAlreadyBooted("NexusKernel.boot called more than once")

        # Initialise authority
        if self._authority is None:
            from nexus_os.capability import CapabilityAuthority
            self._authority = CapabilityAuthority(ledger=self._ledger, session_id=self._session_id)

        # Register PID-0
        kernel_proc = ProcessDescriptor(
            pid      = self.KERNEL_PID,
            name     = "nexus-kernel",
            state    = ProcessState.RUNNING,
            owner_id = self.KERNEL_PID,
        )
        with self._lock:
            self._processes[self.KERNEL_PID] = kernel_proc

        # Mint root capabilities for all system objects
        from nexus_os.capability import (
            OPS_MANAGE, OPS_MEMORY, OPS_IPC, OPS_PROCESS,
            OPS_SCHUMANN, OPS_AFFECT, OPS_MEMORY_STORE,
        )
        root_objects = [
            ("sovereign_memory",  OPS_MEMORY_STORE),
            ("affect_engine",     OPS_AFFECT),
            ("schumann_sync",     OPS_SCHUMANN),
            ("planetary_ledger",  OPS_MANAGE),
            ("kernel_process",    OPS_PROCESS),
            ("kernel_memory",     OPS_MEMORY),
            ("kernel_ipc",        OPS_IPC),
        ]
        for obj_id, ops in root_objects:
            token = self._authority.mint(
                object_id=obj_id,
                permitted_ops=ops,
                issuer_pid=self.KERNEL_PID,
                note=f"root capability minted at boot for {obj_id}",
            )
            kernel_proc.tokens.append(token)

        self.booted = True
        self._audit("boot", self.KERNEL_PID, "nexus-kernel", note="NEXUS OS kernel boot complete")
        logger.info("NexusKernel booted. PID-0 registered. %d root capabilities minted.", len(root_objects))

    # ------------------------------------------------------------------
    # Capability minting
    # ------------------------------------------------------------------

    def mint_capability(
        self,
        object_id: str,
        permitted_ops: FrozenSet[str],
        issuer_pid: str,
        expiry: Optional[datetime] = None,
    ) -> CapabilityToken:
        """
        Mint a new CapabilityToken via the CapabilityAuthority.
        Validates issuer_pid is registered. Logs audit event.
        Reference: seL4 CNode.Mint; NEXUS_UNIVERSAL_OS.md 1.1
        """
        self._require_booted()
        self._require_process(issuer_pid)
        token = self._authority.mint(
            object_id=object_id,
            permitted_ops=frozenset(permitted_ops),
            issuer_pid=issuer_pid,
            expiry=expiry,
        )
        # Attach token to issuer's descriptor
        with self._lock:
            self._processes[issuer_pid].tokens.append(token)
        logger.debug("kernel.mint_capability object=%s issuer=%s", object_id, issuer_pid)
        return token

    def revoke_capability(self, token_id: str, revoker_pid: str) -> None:
        """Revoke a capability token. Audited."""
        self._require_booted()
        self._require_process(revoker_pid)
        self._authority.revoke(token_id, revoker_pid=revoker_pid)

    # ------------------------------------------------------------------
    # Process lifecycle
    # ------------------------------------------------------------------

    def spawn(
        self,
        name: str,
        owner_id: str,
        initial_ops: dict[str, FrozenSet[str]] | None = None,
    ) -> ProcessDescriptor:
        """
        Spawn a new NEXUS OS process and register it with the kernel.
        Optionally mints initial capability tokens: {object_id: ops}.
        Reference: NEXUS_UNIVERSAL_OS.md Domain 1.1 — Process Lifecycle
        """
        self._require_booted()
        proc = ProcessDescriptor(
            pid      = str(uuid.uuid4()),
            name     = name,
            state    = ProcessState.RUNNING,
            owner_id = owner_id,
        )
        with self._lock:
            self._processes[proc.pid] = proc

        if initial_ops:
            for obj_id, ops in initial_ops.items():
                token = self._authority.mint(
                    object_id=obj_id,
                    permitted_ops=ops,
                    issuer_pid=owner_id,
                    note=f"initial capability for spawned process '{name}'",
                )
                proc.tokens.append(token)

        self._audit("spawn", owner_id, proc.pid, note=f"spawned process '{name}'")
        logger.info("kernel.spawn name=%s pid=%s", name, proc.pid)
        return proc

    def suspend(self, pid: str, reason: str = "requested") -> None:
        """Suspend a running process."""
        self._require_booted()
        proc = self._require_process(pid)
        if proc.state != ProcessState.RUNNING:
            raise InvalidProcessState(f"Cannot suspend process in state {proc.state}")
        proc.state = ProcessState.SUSPENDED
        self._audit("suspend", self.KERNEL_PID, pid, note=reason)
        logger.info("kernel.suspend pid=%s reason=%s", pid, reason)

    def resume(self, pid: str) -> None:
        """Resume a suspended process."""
        self._require_booted()
        proc = self._require_process(pid)
        if proc.state != ProcessState.SUSPENDED:
            raise InvalidProcessState(f"Cannot resume process in state {proc.state}")
        proc.state = ProcessState.RUNNING
        self._audit("resume", self.KERNEL_PID, pid)
        logger.info("kernel.resume pid=%s", pid)

    def terminate(self, pid: str, reason: str = "requested") -> None:
        """
        Terminate a running process. Revokes all its capability tokens.
        Reference: GAIAN_LAWS.md Law III — No Silent Override
        """
        self._require_booted()
        proc = self._require_process(pid)
        if proc.state == ProcessState.TERMINATED:
            return  # idempotent
        # Revoke all tokens held by this process
        for token in proc.tokens:
            try:
                self._authority.revoke(token.token_id, revoker_pid=self.KERNEL_PID, note=f"process {pid} terminated")
            except Exception:
                pass  # already revoked is fine
        proc.state = ProcessState.TERMINATED
        self._audit("terminate", self.KERNEL_PID, pid, note=reason)
        logger.info("kernel.terminate pid=%s reason=%s", pid, reason)

    def reap(self, pid: str) -> ProcessDescriptor:
        """
        Remove a TERMINATED process descriptor from the kernel registry.
        Returns the reaped descriptor.
        """
        self._require_booted()
        proc = self._require_process(pid)
        if proc.state != ProcessState.TERMINATED:
            raise ProcessNotTerminated(f"Process {pid} is not terminated (state={proc.state})")
        with self._lock:
            self._processes.pop(pid)
        self._audit("reap", self.KERNEL_PID, pid)
        logger.info("kernel.reap pid=%s", pid)
        return proc

    def list_processes(self) -> list[ProcessDescriptor]:
        """Return a snapshot of all currently registered process descriptors."""
        self._require_booted()
        with self._lock:
            return list(self._processes.values())

    def get_process(self, pid: str) -> ProcessDescriptor:
        self._require_booted()
        return self._require_process(pid)

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    @property
    def audit_log(self) -> list:
        """Return audit records from the CapabilityAuthority."""
        if self._authority is None:
            return []
        return self._authority.get_audit_log()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_booted(self) -> None:
        if not self.booted:
            raise KernelNotBooted("NexusKernel has not been booted. Call kernel.boot() first.")

    def _require_process(self, pid: str) -> ProcessDescriptor:
        with self._lock:
            proc = self._processes.get(pid)
        if proc is None:
            raise ProcessNotFound(f"No process with pid='{pid}' in kernel registry")
        return proc

    def _audit(self, event_type: str, actor: str, obj: str, note: str = "") -> None:
        if self._authority is not None:
            from nexus_os.capability import AuditRecord
            rec = AuditRecord.new(event_type, actor, obj, note=note)
            self._authority._persist_audit(rec)
