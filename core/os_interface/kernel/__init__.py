"""
GAIA Kernel — Hardware Abstraction Layer and Core Kernel Architecture.

The GAIA kernel is a hybrid microkernel: a minimal privileged core that
manages hardware resources, scheduling, and memory, with all higher-order
services (drivers, filesystems, network stacks, intelligence subsystems)
running as isolated user-space servers that communicate via typed messages.

Key design principles:
  1. Physics-first: every abstraction maps to real hardware behavior.
  2. Edge-of-chaos criticality: the scheduler operates near the critical
     point between order and chaos for maximum computational efficiency.
  3. Universal portability: the HAL makes the kernel hardware-agnostic;
     only the HAL implementation changes per architecture.
  4. AI-native: the intelligence runtime is a first-class kernel citizen,
     not a user-space application.
  5. Sovereign boot: GAIA owns the boot sequence via its own bootloader
     and yields control to guest OSes as a hypervisor guest or co-equal partition.

Prior art studied:
  seL4   — formally verified capability-based microkernel (NICTA / CSIRO)
  XNU    — Apple hybrid kernel (Mach microkernel + BSD + IOKit)
  eBPF   — Linux in-kernel programmable bytecode VM for safe extensibility
"""
from core.os_interface.kernel.hal import (
    Architecture,
    HardwarePlatform,
    HALCapability,
    HardwareAbstractionLayer,
)
from core.os_interface.kernel.scheduler import (
    ProcessPriority,
    ProcessState,
    KernelProcess,
    CriticalityScheduler,
)
from core.os_interface.kernel.memory import (
    MemoryRegionKind,
    MemoryRegion,
    MemoryMap,
)

__all__ = [
    "Architecture",
    "HardwarePlatform",
    "HALCapability",
    "HardwareAbstractionLayer",
    "ProcessPriority",
    "ProcessState",
    "KernelProcess",
    "CriticalityScheduler",
    "MemoryRegionKind",
    "MemoryRegion",
    "MemoryMap",
]
