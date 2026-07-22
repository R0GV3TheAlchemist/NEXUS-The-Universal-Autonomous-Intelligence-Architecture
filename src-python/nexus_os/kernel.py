"""
nexus_os.kernel — NEXUS Microkernel
=====================================

The NexusKernel is the minimal, formally-inspired microkernel at the root
of all NEXUS OS instances. Its sole responsibilities are:

  1. Capability minting and revocation
  2. Process lifecycle (spawn, terminate, reap)
  3. Delegation to RTScheduler and MemoryBroker
  4. Kernel-level audit logging of all privileged operations

No policy is encoded here. Policy lives in userspace servers and in the
governance layer (GOVERNANCE.md). The kernel provides mechanisms only.

Design references:
  - seL4 microkernel: capability-based access control, formal verification
  - MINIX 3: reincarnation server pattern for process recovery
  - NEXUS_UNIVERSAL_OS.md § Domain 1.1 — Kernel Design Principles

Ethics reference:  ETHICS.md § Prohibition 6 — No Unaudited Privilege Escalation
GAIAN law:         GAIAN_LAWS.md § Law III — No Silent Override
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import FrozenSet, Optional

logger = logging.getLogger("nexus_os.kernel")


# ── CapabilityToken ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CapabilityToken:
    """
    An unforgeable, immutable token representing the right to perform a
    specific set of operations on a specific kernel object.

    CapabilityTokens are never constructed directly by callers. They are
    minted exclusively by NexusKernel.mint_capability() and are bound to
    a single object_id. Possession of a token IS the permission — no
    separate ACL lookup is required.

    Immutability is enforced by frozen=True. Tokens can be passed between
    processes only via explicit kernel-mediated delegation.

    Reference: seL4 capability derivation; NEXUS_UNIVERSAL_OS.md § 1.1
    """
    token_id:      str
    object_id:     str
    permitted_ops: FrozenSet[str]
    issuer:        str
    issued_at:     datetime
    expiry:        Optional[datetime] = None

    def allows(self, operation: str) -> bool:
        """Return True if this token permits the named operation."""
        return operation in self.permitted_ops

    def is_expired(self) -> bool:
        """Return True if this token has passed its expiry time."""
        if self.expiry is None:
            return False
        return datetime.now(timezone.utc) > self.expiry

    def __str__(self) -> str:
        return (
            f"CapabilityToken(object={self.object_id}, "
            f"ops={sorted(self.permitted_ops)}, "
            f"issuer={self.issuer})"
        )


# ── ProcessDescriptor ─────────────────────────────────────────────────────────

class ProcessState(Enum):
    """Lifecycle states for a NEXUS OS process."""
    NASCENT    = auto()
    RUNNING    = auto()
    SUSPENDED  = auto()
    TERMINATED = auto()
    ZOMBIE     = auto()


@dataclass
class ProcessDescriptor:
    """
    Kernel-side descriptor for a running NEXUS OS process.

    Each process is identified by a unique pid (UUID4 string). The kernel
    maintains a registry of all ProcessDescriptors. No process can acquire
    capabilities without a valid ProcessDescriptor in the kernel registry.

    Reference: NEXUS_UNIVERSAL_OS.md § Domain 1.1 — Process Model
    """
    pid:        str              = field(default_factory=lambda: str(uuid.uuid4()))
    name:       str              = "unnamed-process"
    state:      ProcessState     = ProcessState.NASCENT
    owner_id:   str              = "nexus-kernel"
    created_at: datetime         = field(default_factory=lambda: datetime.now(timezone.utc))
    tokens:     list[CapabilityToken] = field(default_factory=list)

    def has_capability(self, object_id: str, operation: str) -> bool:
        """Check whether this process holds a valid, non-expired capability token."""
        for token in self.tokens:
            if (
                token.object_id == object_id
                and token.allows(operation)
                and not token.is_expired()
            ):
                return True
        return False


# ── NexusKernel ──────────────────────────────────────────────────────────────

class NexusKernel:
    """
    The NEXUS Universal Operating System microkernel.

    Provides minimal privileged services:
      - Capability minting and revocation
      - Process spawn, suspend, terminate, and reap
      - Audit logging of all privileged operations

    The kernel does NOT implement scheduling, memory allocation, or IPC
    directly. These are delegated to RTScheduler, MemoryBroker, and the
    Channel/Message IPC system respectively.

    Reference: seL4 design philosophy; NEXUS_UNIVERSAL_OS.md § Domain 1
    """

    def __init__(self) -> None:
        self._processes: dict[str, ProcessDescriptor] = {}
        self._booted: bool = False
        logger.info("NexusKernel instance created (not yet booted).")

    def boot(self) -> None:
        """
        Execute the NEXUS kernel boot sequence.

        Raises:
            RuntimeError: If boot() is called more than once.

        Reference: NEXUS_UNIVERSAL_OS.md § Domain 1 — Boot Sequence
        """
        raise NotImplementedError(
            "NexusKernel.boot() — kernel boot sequence not yet implemented. "
            "Reference: NEXUS_UNIVERSAL_OS.md § Domain 1 — Boot Sequence. "
            "Expected: initialize process registry, register PID-0 (kernel process), "
            "confirm HALRegistry populated, and set self._booted = True."
        )

    def mint_capability(
        self,
        object_id: str,
        permitted_ops: FrozenSet[str],
        issuer_pid: str,
        expiry: Optional[datetime] = None,
    ) -> CapabilityToken:
        """
        Mint a new CapabilityToken for the given object and operations.

        Reference: seL4 CNode.Mint; NEXUS_UNIVERSAL_OS.md § 1.1
        """
        raise NotImplementedError(
            "NexusKernel.mint_capability() — capability minting not yet implemented. "
            "Expected: validate issuer_pid is in process registry, construct "
            "CapabilityToken(token_id=uuid4(), ...), log audit event, return token."
        )

    def spawn(self, name: str, owner_id: str) -> ProcessDescriptor:
        """
        Spawn a new NEXUS OS process and register it with the kernel.

        Reference: NEXUS_UNIVERSAL_OS.md § Domain 1.1 — Process Lifecycle
        """
        raise NotImplementedError(
            "NexusKernel.spawn() — process spawning not yet implemented. "
            "Expected: cre