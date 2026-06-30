"""
GAIA Criticality Scheduler.

Design principle: edge-of-chaos criticality.
The scheduler maintains the system at the critical point between fully
ordered and fully chaotic scheduling regimes, maximising computational
information processing capacity.

Prior art:
  seL4  — capability-based scheduling, no priority inversion by construction
  XNU   — Mach thread scheduling, importance donation, QoS classes
  Linux — CFS (Completely Fair Scheduler), cgroups, real-time FIFO/RR

GAIA extends these with a dynamic criticality float per process that
integrates with the system-wide criticality_monitor.py score.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProcessPriority(IntEnum):
    IDLE = 0
    LOW = 10
    NORMAL = 20
    HIGH = 30
    SYSTEM = 40
    REALTIME = 50


class ProcessState(str, Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    SLEEPING = "sleeping"
    ZOMBIE = "zombie"
    TERMINATED = "terminated"


@dataclass
class KernelProcess:
    name: str
    pid: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: ProcessPriority = ProcessPriority.NORMAL
    state: ProcessState = ProcessState.CREATED
    criticality: float = 0.5
    cpu_affinity_mask: int = 0xFFFF
    time_slice_ms: int = 10
    total_cpu_ms: int = 0
    memory_pages: int = 0
    owner_id: str = ""
    created_at: str = field(default_factory=_utcnow)
    metadata: Dict = field(default_factory=dict)

    def effective_priority(self) -> float:
        return self.priority.value + (self.criticality * 10.0)


class CriticalityScheduler:
    def __init__(self) -> None:
        self._processes: Dict[str, KernelProcess] = {}
        self._run_queue: List[str] = []
        self._system_criticality: float = 0.5

    def register(self, process: KernelProcess) -> None:
        self._processes[process.pid] = process
        process.state = ProcessState.READY
        self._enqueue(process.pid)

    def terminate(self, pid: str) -> None:
        process = self._processes.get(pid)
        if process:
            process.state = ProcessState.TERMINATED
            self._run_queue = [p for p in self._run_queue if p != pid]

    def tick(self) -> Optional[KernelProcess]:
        if not self._run_queue:
            return None
        pid = self._run_queue[0]
        process = self._processes[pid]
        if process.state == ProcessState.READY:
            process.state = ProcessState.RUNNING
            process.time_slice_ms = self._compute_slice(process)
        return process

    def complete_slice(self, pid: str, cpu_ms_used: int) -> None:
        process = self._processes.get(pid)
        if process:
            process.total_cpu_ms += cpu_ms_used
            process.state = ProcessState.READY
            self._run_queue = [p for p in self._run_queue if p != pid]
            self._enqueue(pid)

    def block(self, pid: str) -> None:
        process = self._processes.get(pid)
        if process:
            process.state = ProcessState.BLOCKED
            self._run_queue = [p for p in self._run_queue if p != pid]

    def unblock(self, pid: str) -> None:
        process = self._processes.get(pid)
        if process and process.state == ProcessState.BLOCKED:
            process.state = ProcessState.READY
            self._enqueue(pid)

    def set_system_criticality(self, value: float) -> None:
        self._system_criticality = max(0.0, min(1.0, value))
        self._resort()

    def _compute_slice(self, process: KernelProcess) -> int:
        base = 10
        factor = 1.0 - (self._system_criticality * 0.5)
        return max(1, int(base * factor * (1.0 + process.criticality)))

    def _enqueue(self, pid: str) -> None:
        self._run_queue.append(pid)
        self._resort()

    def _resort(self) -> None:
        self._run_queue.sort(
            key=lambda pid: self._processes[pid].effective_priority(),
            reverse=True,
        )

    def process_list(self) -> List[KernelProcess]:
        return list(self._processes.values())

    def ready_count(self) -> int:
        return sum(1 for p in self._processes.values() if p.state == ProcessState.READY)
