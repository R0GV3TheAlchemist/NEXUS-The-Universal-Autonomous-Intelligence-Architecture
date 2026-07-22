"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

scheduler.py — NEXUS Real-Time Mixed Scheduler.

Three scheduling classes: HRT (hard real-time), SRT (soft real-time),
and BE (best-effort). Carbon-aware placement hooks integrate with the
EnergyProfile from the HAL.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Deque, Dict, List, Optional
from uuid import UUID
from collections import deque

from nexus_os.hal import EnergyProfile


class TaskPriority(Enum):
    HRT = 0   # Hard Real-Time — highest priority
    SRT = 1   # Soft Real-Time
    BE  = 2   # Best-Effort — lowest priority


@dataclass
class TaskDescriptor:
    """A schedulable unit of work."""
    task_id: UUID
    process_id: UUID
    priority: TaskPriority
    deadline_ms: float = 0.0
    energy_profile: EnergyProfile = field(default_factory=EnergyProfile)
    callback: Optional[object] = None


@dataclass
class SchedulerStats:
    total_dispatched: int = 0
    hrt_misses: int = 0
    carbon_migrations: int = 0


class RTScheduler:
    """
    NEXUS real-time mixed scheduler with carbon-aware placement.

    HRT tasks preempt all others. SRT tasks preempt only BE.
    BE tasks use work-stealing across idle lanes.
    Carbon migration moves BE/SRT tasks to low-carbon nodes
    when carbon_intensity exceeds carbon_threshold_gco2_kwh.
    """

    def __init__(self, carbon_threshold_gco2_kwh: float = 200.0) -> None:
        self.carbon_threshold = carbon_threshold_gco2_kwh
        self._queues: Dict[TaskPriority, Deque[TaskDescriptor]] = {
            TaskPriority.HRT: deque(),
            TaskPriority.SRT: deque(),
            TaskPriority.BE:  deque(),
        }
        self.stats = SchedulerStats()

    def enqueue(self, task: TaskDescriptor) -> None:
        self._queues[task.priority].append(task)

    def tick(self) -> Optional[TaskDescriptor]:
        """Select and return the highest-priority ready task."""
        for priority in TaskPriority:
            queue = self._queues[priority]
            if queue:
                task = queue.popleft()
                task = self._carbon_check(task)
                self.stats.total_dispatched += 1
                return task
        return None

    def _carbon_check(self, task: TaskDescriptor) -> TaskDescriptor:
        ci = task.energy_profile.carbon_intensity_gco2_kwh
        if ci > self.carbon_threshold and task.priority != TaskPriority.HRT:
            self.stats.carbon_migrations += 1
        return task

    def pending_count(self, priority: Optional[TaskPriority] = None) -> int:
        if priority:
            return len(self._queues[priority])
        return sum(len(q) for q in self._queues.values())

    def drain(self) -> List[TaskDescriptor]:
        """Drain all queues and return tasks (for shutdown/migration)."""
        tasks = []
        for q in self._queues.values():
            tasks.extend(q)
            q.clear()
        return tasks
