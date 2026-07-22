"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  GAIA  — The Global Autonomous Intelligence Architecture

  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist (https://github.com/R0GV3TheAlchemist)
  Email    : xxkylesteenxx@outlook.com
  Project  : NEXUS / GAIA
  License  : All Rights Reserved © 2026 Kyle Steen
             Unauthorized use, reproduction, or distribution
             of this file or its contents is strictly prohibited.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

nexus_os — NEXUS Universal OS Kernel Package.

Provides the microkernel, HAL, real-time scheduler, IPC, and memory subsystems
for the NEXUS planetary-scale operating substrate.
"""

__version__ = "1.0.0"
__author__ = "Kyle Steen"
__all__ = [
    "NexusKernel",
    "HALRegistry",
    "RTScheduler",
    "Channel",
    "MemoryBroker",
]

from nexus_os.kernel import NexusKernel
from nexus_os.hal import HALRegistry
from nexus_os.scheduler import RTScheduler
from nexus_os.ipc import Channel
from nexus_os.memory import MemoryBroker
