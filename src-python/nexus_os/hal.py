"""
nexus_os.hal — Hardware Abstraction Layer
==========================================

Defines the capability-driven hardware abstraction layer for the NEXUS
microkernel. Every physical or virtual device is represented as a
DeviceCapability. Drivers register against these capabilities via the
HALRegistry. No kernel component accesses hardware directly — all access
is mediated through registered HALDriver instances.

Design references:
  - Fuchsia Zircon driver framework (capability routing via component tree)
  - seL4 microkernel hardware device capability model
  - NEXUS_UNIVERSAL_OS.md § Domain 1.2 — Hardware Abstraction

Ethics reference:  ETHICS.md § Commitment 3 — Transparency of Operation
GAIAN law:         GAIAN_LAWS.md § Law I — Sovereignty of Self
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from typing import Protocol, runtime_checkable

logger = logging.getLogger("nexus_os.hal")


# ── Device Capability Enumeration ─────────────────────────────────────────────

class DeviceCapability(Enum):
    """
    Enumeration of all hardware capabilities the NEXUS HAL recognises.

    Each member represents a distinct device class. The HALRegistry maps
    these capabilities to registered driver instances. A capability token
    must name one of these members to access the corresponding hardware.

    Reference: NEXUS_UNIVERSAL_OS.md § Domain 1.2
    """
    CLOCK          = auto()  # Monotonic / wall-clock timekeeping
    STORAGE        = auto()  # Persistent block storage
    NETWORK        = auto()  # Network interface (IP stack)
    MESH_RADIO     = auto()  # LoRa / mesh radio transceiver
    ELF_SENSOR     = auto()  # Extremely Low Frequency magnetic sensor (Schumann)
    CRYPTO_ENGINE  = auto()  # Hardware security module / TPM
    GPU_COMPUTE    = auto()  # GPU compute plane (CUDA / ROCm / Metal)
    QUANTUM_COPR   = auto()  # Quantum co-processor interface
    POWER_MONITOR  = auto()  # Energy / power consumption telemetry
    DISPLAY        = auto()  # Display / framebuffer output
    AUDIO          = auto()  # Audio input/output
    SENSOR_ARRAY   = auto()  # Generic sensor array (temperature, pressure, etc.)


# ── HALDriver Protocol ────────────────────────────────────────────────────────

@runtime_checkable
class HALDriver(Protocol):
    """
    Structural protocol that all HAL drivers must satisfy.

    Drivers are registered with HALRegistry.register() and looked up via
    HALRegistry.get(). The protocol is intentionally minimal — drivers
    must be initializable and provide a probe() method that confirms
    hardware presence without side effects.

    Any object satisfying this protocol can serve as a HALDriver — no
    inheritance from a base class is required (structural subtyping).

    Reference: Fuchsia Zircon driver binding model.
    """

    @property
    def capability(self) -> DeviceCapability:
        """Return the DeviceCapability this driver satisfies."""
        ...

    def probe(self) -> bool:
        """
        Probe the underlying hardware to confirm availability.

        Returns True if the device is present and accessible.
        Returns False if the device is absent or in a fault state.
        Must not raise; must be side-effect-free.
        """
        ...

    def initialize(self) -> None:
        """
        Perform one-time hardware initialization.

        Called by HALRegistry.register() after probe() returns True.
        Raises RuntimeError if initialization fails.
        """
        ...

    def shutdown(self) -> None:
        """
        Gracefully shut down and release all hardware resources.

        Called by HALRegistry.deregister() or during kernel shutdown.
        Must not raise.
        """
        ...


# ── HALRegistry ───────────────────────────────────────────────────────────────

class HALRegistry:
    """
    Central registry mapping DeviceCapability → HALDriver.

    The registry is the sole source of truth for available hardware in the
    NEXUS OS. No component may acquire hardware access without first
    obtaining a CapabilityToken from NexusKernel, and no token can be
    minted for a capability not present in this registry.

    Thread-safety: The registry uses no internal locking. It is expected
    to be populated during kernel boot (single-threaded) and read-only
    thereafter. Hot-plug is not supported in v0.1.0.

    Reference: seL4 capability derivation tree; NEXUS_UNIVERSAL_OS.md § 1.2
    """

    def __init__(self) -> None:
        self._drivers: dict[DeviceCapability, HALDriver] = {}

    def register(self, driver: HALDriver) -> None:
        """
        Register a driver for its declared capability.

        Calls driver.probe() first. If probe returns False, registration
        is skipped and a warning is logged. If probe returns True,
        driver.initialize() is called and the driver is stored.

        Args:
            driver: Any object satisfying the HALDriver Protocol.

        Raises:
            TypeError: If driver does not satisfy the HALDriver Protocol.
            RuntimeError: If driver.initialize() raises.
        """
        if not isinstance(driver, HALDriver):
            raise TypeError(
                f"Object {driver!r} does not satisfy the HALDriver Protocol."
            )
        cap = driver.capability
        if not driver.probe():
            logger.warning(
                "HAL probe failed for capability %s — driver not registered.", cap.name
            )
            return
        driver.initialize()
        self._drivers[cap] = driver
        logger.info("HALDriver registered for capability: %s", cap.name)

    def deregister(self, capability: DeviceCapability) -> None:
        """
        Deregister and shut down the driver for a given capability.

        Args:
            capability: The DeviceCapability to remove.

        Raises:
            KeyError: If no driver is registered for this capability.
        """
        driver = self._drivers.pop(capability)
        driver.shutdown()
        logger.info("HALDriver deregistered for capability: %s", capability.name)

    def get(self, capability: DeviceCapability) -> HALDriver:
        """
        Look up the driver for a given capability.

        Args:
            capability: The DeviceCapability to look up.

        Returns:
            The registered HALDriver instance.

        Raises:
            KeyError: If no driver is registered for this capability.
        """
        try:
            return self._drivers[capability]
        except KeyError:
            raise KeyError(
                f"No HALDriver registered for capability: {capability.name}. "
                f"Available: {[c.name for c in self._drivers]}"
            )

    def available(self) -> list[DeviceCapability]:
        """Return a list of all currently registered capabilities."""
        return list(self._drivers.keys())

    def __repr__(self) -> str:
        caps = [c.name for c in self._drivers]
        return f"HALRegistry(registered={caps})"
