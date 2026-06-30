"""
GAIA Boot Manager — boot configuration lifecycle and stage progression.
"""
from __future__ import annotations

from typing import List, Optional

from core.os_interface.bootloader.model import (
    BootConfiguration,
    BootEntry,
    BootMode,
    BootStage,
)


class BootManager:
    def __init__(self, config: Optional[BootConfiguration] = None) -> None:
        self.config = config or BootConfiguration()

    def advance_stage(self, stage: BootStage) -> None:
        self.config.current_stage = stage

    def add_guest_os(
        self,
        label: str,
        loader_path: str,
        chain_loader_path: str = "",
        os_vendor: str = "",
        partition_guid: str = "",
    ) -> BootEntry:
        entry = BootEntry(
            label=label,
            loader_path=loader_path,
            is_gaia=False,
            os_vendor=os_vendor,
            partition_guid=partition_guid,
            chain_load=bool(chain_loader_path),
            chain_loader_path=chain_loader_path,
        )
        self.config.add_entry(entry)
        return entry

    def set_mode(self, mode: BootMode) -> None:
        self.config.mode = mode

    def register_failure(self) -> None:
        self.config.consecutive_failures += 1
        self.config.last_boot_successful = False
        if self.config.consecutive_failures >= 3:
            self.config.mode = BootMode.RECOVERY

    def register_success(self) -> None:
        self.config.last_boot_successful = True
        self.config.consecutive_failures = 0

    def boot_menu(self) -> List[dict]:
        return [
            {
                "entry_id": e.entry_id,
                "label": e.label,
                "is_gaia": e.is_gaia,
                "is_default": e.is_default,
                "os_vendor": e.os_vendor,
            }
            for e in self.config.entries
        ]

    def status(self) -> dict:
        return {
            "mode": self.config.mode.value,
            "stage": self.config.current_stage.value,
            "secure_boot": self.config.secure_boot_enabled,
            "tpm_measured_boot": self.config.tpm_measured_boot,
            "version": self.config.gaia_version,
            "channel": self.config.gaia_channel,
            "last_boot_ok": self.config.last_boot_successful,
            "entries": len(self.config.entries),
        }
