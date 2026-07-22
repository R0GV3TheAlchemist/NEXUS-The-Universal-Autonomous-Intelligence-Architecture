"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

kernel.py — NEXUS Microkernel.

Implements the capability-enforced syscall dispatch loop, process table,
and CapabilityToken issuance/validation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4
import time


class SyscallType(Enum):
    SPAWN = auto()
    KILL = auto()
    IPC_SEND = auto()
    IPC_RECV = auto()
    MEM_ALLOC = auto()
    MEM_FREE = auto()
    HAL_ACCESS = auto()
    SCHED_YIELD = auto()


@dataclass(frozen=True)
class CapabilityToken:
    """
    Unforgeable capability token issued by the kernel.
    Grants a specific syscall right to a specific process.
    """
    token_id: UUID
    process_id: UUID
    allowed_syscalls: frozenset
    expires_at: float

    def is_valid(self) -> bool:
        if self.expires_at == 0.0:
            return True
        return time.time() < self.expires_at

    def allows(self, syscall: SyscallType) -> bool:
        return syscall in self.allowed_syscalls and self.is_valid()


@dataclass
class ProcessDescriptor:
    """Descriptor for a process managed by the NEXUS kernel."""
    process_id: UUID = field(default_factory=uuid4)
    name: str = "unnamed"
    priority: int = 0
    tokens: List[CapabilityToken] = field(default_factory=list)
    state: str = "READY"  # READY | RUNNING | BLOCKED | ZOMBIE

    def has_capability(self, syscall: SyscallType) -> bool:
        return any(t.allows(syscall) for t in self.tokens)


class NexusKernel:
    """
    NEXUS Microkernel — capability-enforced syscall dispatcher.

    The kernel maintains a process table and dispatches syscalls only
    when the calling process holds a valid CapabilityToken for that call.
    """

    def __init__(self) -> None:
        self._processes: Dict[UUID, ProcessDescriptor] = {}
        self._handlers: Dict[SyscallType, Callable] = {}
        self._running = False

    def spawn(self, name: str, allowed_syscalls: Set[SyscallType],
              priority: int = 0) -> ProcessDescriptor:
        """Spawn a new process and issue its initial CapabilityToken."""
        proc = ProcessDescriptor(name=name, priority=priority)
        token = CapabilityToken(
            token_id=uuid4(),
            process_id=proc.process_id,
            allowed_syscalls=frozenset(allowed_syscalls),
            expires_at=0.0,
        )
        proc.tokens.append(token)
        self._processes[proc.process_id] = proc
        return proc

    def kill(self, process_id: UUID) -> None:
        proc = self._processes.get(process_id)
        if proc:
            proc.state = "ZOMBIE"
            self._processes.pop(process_id)

    def register_handler(self, syscall: SyscallType, handler: Callable) -> None:
        self._handlers[syscall] = handler

    def dispatch(self, process_id: UUID, syscall: SyscallType,
                 **kwargs) -> Optional[object]:
        """
        Validate CapabilityToken then invoke the registered handler.
        Raises PermissionError on capability violation.
        """
        proc = self._processes.get(process_id)
        if proc is None:
            raise LookupError(f"Unknown process: {process_id}")
        if not proc.has_capability(syscall):
            raise PermissionError(
                f"Process '{proc.name}' lacks capability for {syscall.name}")
        handler = self._handlers.get(syscall)
        if handler is None:
            raise NotImplementedError(f"No handler for {syscall.name}")
        return handler(process_id=process_id, **kwargs)

    def boot(self) -> None:
        self._running = True

    def halt(self) -> None:
        self._running = False
        self._processes.clear()

    @property
    def running(self) -> bool:
        return self._running

    def list_processes(self) -> List[ProcessDescriptor]:
        return list(self._processes.values())
