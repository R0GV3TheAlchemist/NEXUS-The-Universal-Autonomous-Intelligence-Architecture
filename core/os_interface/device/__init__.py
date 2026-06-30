"""
GAIA Device Manager & HAL Registry.

Every physical or virtual device that GAIA can touch is registered here.
No process, driver, or intelligence agent may access a device without a
capability grant issued by the Device Manager. Devices do not exist to
GAIA until they are registered — this is the ground truth of the hardware
universe as GAIA perceives it.

Design lineage:
  IOKit / DriverKit (XNU) — typed device tree, service matching, power mgmt
  seL4 Capability Model   — unforgeable device access tokens
  Linux sysfs / udev       — runtime enumeration & hotplug events
  eBPF XDP / GKE           — hook points for intelligent device intercept

GAIA extends these with:
  - DeviceKind taxonomy: 20+ typed device classes including NEURAL_ENGINE
  - DeviceCapabilityToken: unforgeable, revocable access grant per device
  - HALRegistry: the single source of truth for all hardware GAIA knows
  - DeviceManager: enumerate, register, bind, revoke, and query devices
  - HotplugEvent: device arrival/departure signaling for the event bus
"""
from core.os_interface.device.model import (
    DeviceKind,
    DeviceState,
    DevicePowerState,
    DeviceCapabilityToken,
    GAIADevice,
    HotplugEvent,
    HotplugAction,
)
from core.os_interface.device.registry import HALRegistry
from core.os_interface.device.manager import DeviceManager

__all__ = [
    "DeviceKind",
    "DeviceState",
    "DevicePowerState",
    "DeviceCapabilityToken",
    "GAIADevice",
    "HotplugEvent",
    "HotplugAction",
    "HALRegistry",
    "DeviceManager",
]
