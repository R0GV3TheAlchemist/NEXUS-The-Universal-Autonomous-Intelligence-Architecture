"""
GAIA Device Model — typed devices, power states, and capability tokens.

Every piece of hardware or virtual device is represented as a GAIADevice.
Access to a device is granted exclusively through a DeviceCapabilityToken —
an unforgeable, revocable, scoped access credential issued by the Device
Manager. No process holds a raw device handle; it holds a token.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class DeviceKind(str, Enum):
    # Compute
    CPU = "cpu"
    GPU = "gpu"
    NEURAL_ENGINE = "neural_engine"      # Apple ANE, Google TPU, Qualcomm NPU
    QUANTUM_PROCESSOR = "quantum_processor"
    FPGA = "fpga"
    DSP = "dsp"

    # Memory
    RAM = "ram"
    NVRAM = "nvram"                      # non-volatile: NVMe, Optane
    STORAGE = "storage"                  # block device: SSD, HDD
    REMOVABLE_STORAGE = "removable_storage"  # USB, SD card

    # Display & Output
    DISPLAY = "display"
    AUDIO_OUTPUT = "audio_output"
    HAPTIC = "haptic"
    SPATIAL_DISPLAY = "spatial_display"  # visionOS / XR headset

    # Input
    KEYBOARD = "keyboard"
    POINTER = "pointer"                  # mouse, trackpad, stylus
    TOUCH = "touch"
    BIOMETRIC = "biometric"              # fingerprint, Face ID
    CAMERA = "camera"
    MICROPHONE = "microphone"
    SENSOR = "sensor"                    # accelerometer, gyro, lidar, etc.

    # Network & Radio
    NETWORK_ETHERNET = "network_ethernet"
    NETWORK_WIFI = "network_wifi"
    NETWORK_CELLULAR = "network_cellular"
    NETWORK_BLUETOOTH = "network_bluetooth"
    NETWORK_UWB = "network_uwb"          # ultra-wideband spatial
    NETWORK_NEURAL_MESH = "network_neural_mesh"  # GAIA distributed mesh

    # Bus & Peripheral
    USB = "usb"
    THUNDERBOLT = "thunderbolt"
    PCIE = "pcie"
    I2C = "i2c"
    SPI = "spi"
    UART = "uart"

    # Virtual & Synthetic
    VIRTUAL = "virtual"                  # software-defined device
    LOOPBACK = "loopback"
    EMULATED = "emulated"                # guest OS emulated device


class DeviceState(str, Enum):
    DETECTED = "detected"        # physically present, not yet initialized
    INITIALIZING = "initializing"
    READY = "ready"              # fully operational
    BUSY = "busy"                # serving an active request
    SUSPENDED = "suspended"      # low-power, can resume
    FAULTED = "faulted"          # error state
    REMOVED = "removed"          # hotplug removal
    VIRTUAL = "virtual"          # synthetic / always-ready


class DevicePowerState(str, Enum):
    ACTIVE = "active"            # full power
    IDLE = "idle"                # clocks reduced
    SLEEP = "sleep"              # context preserved, power cut
    HIBERNATE = "hibernate"      # context to disk, power off
    OFF = "off"


class HotplugAction(str, Enum):
    ATTACHED = "attached"
    DETACHED = "detached"
    STATE_CHANGED = "state_changed"
    FAULTED = "faulted"


@dataclass
class DeviceCapabilityToken:
    """
    An unforgeable, scoped access credential for a specific device.

    A process must hold a token to legally access a device. Tokens can be
    revoked by the Device Manager at any time. Delegation is opt-in and
    must be explicitly permitted by the issuing authority.
    """
    token_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str = ""
    holder_pid: str = ""            # process holding this token
    read: bool = True
    write: bool = False
    exclusive: bool = False          # holder has sole access
    delegate: bool = False           # may sub-grant to children
    revoked: bool = False
    issued_at: str = field(default_factory=_utcnow)
    issued_by: str = ""              # device manager pid or "kernel"
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_active(self) -> bool:
        return not self.revoked


@dataclass
class GAIADevice:
    """
    A registered hardware or virtual device in the GAIA device universe.

    Physical devices are discovered via HAL enumeration or hotplug events.
    Virtual devices are registered programmatically. Both kinds exist equally
    in the registry and are accessed identically through capability tokens.
    """
    name: str
    kind: DeviceKind
    device_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vendor: str = ""
    model: str = ""
    firmware_version: str = ""
    bus_path: str = ""               # e.g. PCI:00:1f.0, USB:2-1.3
    driver_pid: Optional[str] = None # pid of driver process serving this device
    state: DeviceState = DeviceState.DETECTED
    power_state: DevicePowerState = DevicePowerState.ACTIVE
    capabilities: List[str] = field(default_factory=list)  # e.g. ["dma", "interrupt", "mmio"]
    properties: Dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=_utcnow)
    last_state_change: str = field(default_factory=_utcnow)

    def transition(self, new_state: DeviceState) -> None:
        self.state = new_state
        self.last_state_change = _utcnow()

    def power_transition(self, new_power: DevicePowerState) -> None:
        self.power_state = new_power
        self.last_state_change = _utcnow()

    def is_accessible(self) -> bool:
        return self.state in (DeviceState.READY, DeviceState.BUSY, DeviceState.VIRTUAL)

    def summary(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "kind": self.kind.value,
            "vendor": self.vendor,
            "model": self.model,
            "bus_path": self.bus_path,
            "state": self.state.value,
            "power_state": self.power_state.value,
            "driver_pid": self.driver_pid,
            "accessible": self.is_accessible(),
        }


@dataclass
class HotplugEvent:
    """Signals a device arrival, departure, or state change to the event bus."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: HotplugAction = HotplugAction.ATTACHED
    device_id: str = ""
    device_kind: DeviceKind = DeviceKind.VIRTUAL
    device_name: str = ""
    previous_state: Optional[DeviceState] = None
    new_state: Optional[DeviceState] = None
    timestamp: str = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
