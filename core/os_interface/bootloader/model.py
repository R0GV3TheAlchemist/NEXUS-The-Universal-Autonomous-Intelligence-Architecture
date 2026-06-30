"""
GAIA Boot Configuration Model.

Boot modes:
  GAIA_PRIMARY  — GAIA is the only OS on the machine
  DUAL_BOOT     — GAIA + one or more guest OSes (Windows, Ubuntu, etc.)
  GAIA_LAYER    — GAIA runs as a hypervisor layer over a host OS
  RECOVERY      — minimal recovery environment, triggered after 3 failures
  SAFE          — minimal kernel, intelligence runtime disabled
  PXE_NETWORK   — network boot for enterprise and cloud deployments
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class BootMode(str, Enum):
    GAIA_PRIMARY = "gaia_primary"
    DUAL_BOOT = "dual_boot"
    GAIA_LAYER = "gaia_layer"
    RECOVERY = "recovery"
    SAFE = "safe"
    PXE_NETWORK = "pxe_network"


class BootStage(str, Enum):
    FIRMWARE = "firmware"
    BOOTLOADER = "bootloader"
    KERNEL_LOAD = "kernel_load"
    HAL_INIT = "hal_init"
    SCHEDULER_INIT = "scheduler_init"
    INTELLIGENCE_INIT = "intelligence_init"
    SERVICES_INIT = "services_init"
    DESKTOP_INIT = "desktop_init"
    READY = "ready"


@dataclass
class BootEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    description: str = ""
    loader_path: str = ""
    is_gaia: bool = True
    is_default: bool = False
    os_vendor: str = "GAIA"
    partition_guid: str = ""
    chain_load: bool = False
    chain_loader_path: str = ""
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BootConfiguration:
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mode: BootMode = BootMode.GAIA_PRIMARY
    entries: List[BootEntry] = field(default_factory=list)
    timeout_seconds: int = 5
    secure_boot_enabled: bool = True
    tpm_measured_boot: bool = True
    current_stage: BootStage = BootStage.FIRMWARE
    gaia_version: str = "0.1.0"
    gaia_channel: str = "canary"
    kernel_params: str = ""
    last_boot_successful: bool = True
    consecutive_failures: int = 0

    def default_entry(self) -> Optional[BootEntry]:
        for entry in self.entries:
            if entry.is_default:
                return entry
        return self.entries[0] if self.entries else None

    def guest_entries(self) -> List[BootEntry]:
        return [e for e in self.entries if not e.is_gaia]

    def add_entry(self, entry: BootEntry) -> None:
        if entry.is_default:
            for e in self.entries:
                e.is_default = False
        self.entries.append(entry)
