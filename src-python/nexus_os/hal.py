"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

hal.py — Hardware Abstraction Layer for NEXUS OS.

Defines DeviceCapability descriptors, HALDriver base class, and HALRegistry.
All hardware interaction in NEXUS passes through a registered HALDriver.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class DeviceType(Enum):
    CPU = auto()
    GPU = auto()
    ASIC = auto()
    QPU = auto()
    SENSOR = auto()
    ACTUATOR = auto()
    NETWORK = auto()
    STORAGE = auto()


@dataclass
class EnergyProfile:
    """Power draw envelope for a device."""
    idle_watts: float = 0.0
    peak_watts: float = 0.0
    renewable_fraction: float = 0.0
    carbon_intensity_gco2_kwh: float = 0.0


@dataclass
class DeviceCapability:
    """Capability descriptor registered by every device in the HAL."""
    device_type: DeviceType = DeviceType.CPU
    throughput_gbps: float = 0.0
    latency_us: float = 0.0
    pqc_support: bool = False
    energy_profile: EnergyProfile = field(default_factory=EnergyProfile)
    device_id: UUID = field(default_factory=uuid4)
    metadata: Dict[str, str] = field(default_factory=dict)


class HALDriver(ABC):
    """Abstract base for all hardware drivers registered in NEXUS OS."""

    def __init__(self, capability: DeviceCapability) -> None:
        self.capability = capability

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the hardware device. Returns True on success."""
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shut down the device."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if device is operational."""
        ...

    def get_capability(self) -> DeviceCapability:
        return self.capability


class HALRegistry:
    """
    Central registry for all HALDrivers known to the NEXUS OS.

    Drivers register on boot; kernel queries this registry before
    dispatching any hardware-touching syscall.
    """

    def __init__(self) -> None:
        self._drivers: Dict[UUID, HALDriver] = {}

    def register(self, driver: HALDriver) -> UUID:
        """Register a driver and return its device_id."""
        device_id = driver.capability.device_id
        self._drivers[device_id] = driver
        return device_id

    def deregister(self, device_id: UUID) -> None:
        self._drivers.pop(device_id, None)

    def get(self, device_id: UUID) -> Optional[HALDriver]:
        return self._drivers.get(device_id)

    def list_by_type(self, device_type: DeviceType) -> List[HALDriver]:
        return [d for d in self._drivers.values()
                if d.capability.device_type == device_type]

    def discover(self) -> List[DeviceCapability]:
        """Return all registered capabilities for scheduler/planner use."""
        return [d.capability for d in self._drivers.values()]
