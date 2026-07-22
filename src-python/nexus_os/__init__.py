"""
nexus_os — NEXUS Universal Operating System Kernel Package
===========================================================

Root package for the NEXUS OS microkernel layer. Provides the foundational
abstractions for hardware abstraction, process management, capability-based
security, real-time scheduling, inter-process communication, and memory
brokering.

Architecture reference: NEXUS_UNIVERSAL_OS.md § Domain 1 — Kernel & HAL
Ethics reference:       ETHICS.md § Commitment 1 — Sovereignty by Design
GAIAN law reference:    GAIAN_LAWS.md § Law III — No Silent Override

NEXUS version: 0.1.0
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "R0GV3TheAlchemist"
__license__ = "See LICENSE"

from nexus_os.hal import DeviceCapability, HALDriver, HALRegistry
from nexus_os.kernel import NexusKernel, ProcessDescriptor, CapabilityToken
from nexus_os.scheduler import RTScheduler, TaskPriority, EnergyProfile
from nexus_os.ipc import Channel, Message, DeliverySemantics
from nexus_os.memory import MemoryRegion, MemoryBroker

__all__ = [
    # HAL
    "DeviceCapability",
    "HALDriver",
    "HALRegistry",
    # Kernel
    "NexusKernel",
    "ProcessDescriptor",
    "CapabilityToken",
    # Scheduler
    "RTScheduler",
    "TaskPriority",
    "EnergyProfile",
    # IPC
    "Channel",
    "Message",
    "DeliverySemantics",
    # Memory
    "MemoryRegion",
    "MemoryBroker",
]
