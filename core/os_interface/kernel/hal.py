"""
GAIA Hardware Abstraction Layer (HAL).

The HAL is the only kernel component that is architecture-specific.
Everything above the HAL is portable. The HAL exposes a uniform API
for CPU topology, memory layout, interrupt routing, timer access,
I/O bus enumeration, and power management.

Supported architectures (research phase):
  x86_64   — Intel/AMD, UEFI, PCIe, APIC
  ARM64    — Apple Silicon, Qualcomm Snapdragon, ARM Cortex-A
  RISC-V   — open ISA, forward compatibility
  WASM     — browser/sandbox runtime (GAIA in a tab)
  QUANTUM  — placeholder for quantum co-processor integration

Prior art:
  seL4 HAL — minimal platform layer, verified C, no dynamic allocation
  XNU HAL  — IOKit device tree, platform expert pattern
  Linux    — ACPI, DeviceTree, SMBIOS probing patterns
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Architecture(str, Enum):
    X86_64 = "x86_64"
    ARM64 = "arm64"
    RISCV64 = "riscv64"
    WASM = "wasm"
    QUANTUM = "quantum"


class HALCapability(str, Enum):
    UEFI_BOOT = "uefi_boot"
    SECURE_BOOT = "secure_boot"
    TPM2 = "tpm2"
    IOMMU = "iommu"
    VIRTUALIZATION = "virtualization"
    NUMA = "numa"
    HETEROGENEOUS_CPU = "heterogeneous_cpu"
    NEURAL_ENGINE = "neural_engine"
    GPU_COMPUTE = "gpu_compute"
    TRUSTED_EXECUTION = "trusted_execution"
    POWER_MANAGEMENT = "power_management"
    HOT_PLUG = "hot_plug"
    PERSISTENT_MEMORY = "persistent_memory"
    QUANTUM_COPROCESSOR = "quantum_coprocessor"


@dataclass
class CPUTopology:
    architecture: Architecture = Architecture.X86_64
    physical_cores: int = 1
    logical_cores: int = 1
    performance_cores: int = 0
    efficiency_cores: int = 0
    sockets: int = 1
    numa_nodes: int = 1
    base_freq_mhz: int = 0
    boost_freq_mhz: int = 0
    cache_l1_kb: int = 0
    cache_l2_kb: int = 0
    cache_l3_mb: int = 0
    features: List[str] = field(default_factory=list)


@dataclass
class HardwarePlatform:
    platform_id: str = ""
    vendor: str = ""
    model: str = ""
    firmware_version: str = ""
    cpu: CPUTopology = field(default_factory=CPUTopology)
    ram_total_gb: float = 0.0
    ram_speed_mhz: int = 0
    storage_devices: List[Dict[str, Any]] = field(default_factory=list)
    display_adapters: List[Dict[str, Any]] = field(default_factory=list)
    network_adapters: List[Dict[str, Any]] = field(default_factory=list)
    capabilities: List[HALCapability] = field(default_factory=list)
    pcie_devices: List[Dict[str, Any]] = field(default_factory=list)
    usb_controllers: List[Dict[str, Any]] = field(default_factory=list)
    neural_engine_tops: float = 0.0

    def has_capability(self, cap: HALCapability) -> bool:
        return cap in self.capabilities

    def is_ai_capable(self) -> bool:
        return self.neural_engine_tops > 0 or self.has_capability(HALCapability.GPU_COMPUTE)

    def supports_virtualization(self) -> bool:
        return self.has_capability(HALCapability.VIRTUALIZATION)


class HardwareAbstractionLayer:
    def __init__(self, architecture: Architecture = Architecture.X86_64) -> None:
        self.architecture = architecture
        self._platform: Optional[HardwarePlatform] = None

    def probe(self) -> HardwarePlatform:
        self._platform = self._do_probe()
        return self._platform

    def _do_probe(self) -> HardwarePlatform:
        return HardwarePlatform(
            platform_id="gaia-dev-0",
            vendor="GAIA Research",
            model="Development Platform",
            firmware_version="0.1.0",
            cpu=CPUTopology(
                architecture=self.architecture,
                physical_cores=8,
                logical_cores=16,
                performance_cores=6,
                efficiency_cores=2,
                base_freq_mhz=2400,
                boost_freq_mhz=5200,
                cache_l3_mb=32,
            ),
            ram_total_gb=32.0,
            ram_speed_mhz=6400,
            capabilities=[
                HALCapability.UEFI_BOOT,
                HALCapability.SECURE_BOOT,
                HALCapability.TPM2,
                HALCapability.VIRTUALIZATION,
                HALCapability.IOMMU,
                HALCapability.HETEROGENEOUS_CPU,
                HALCapability.NEURAL_ENGINE,
                HALCapability.GPU_COMPUTE,
                HALCapability.POWER_MANAGEMENT,
            ],
            neural_engine_tops=38.0,
        )

    @property
    def platform(self) -> Optional[HardwarePlatform]:
        return self._platform

    def read_timer_ns(self) -> int:
        import time
        return time.monotonic_ns()

    def set_interrupt_affinity(self, irq: int, cpu_mask: int) -> None:
        pass  # real impl writes /proc/irq/<n>/smp_affinity or APIC tables

    def power_state(self) -> str:
        return "S0"
