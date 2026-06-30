"""
GAIA Bootloader — sovereign boot sequence manager.

Boot sequence:
  1. UEFI firmware POST and device enumeration
  2. GAIA bootloader selected from EFI boot manager
  3. Bootloader probes hardware via HAL early-init
  4. Boot menu presented (GAIA primary + any guest OS chain-load entries)
  5. GAIA kernel loaded into memory
  6. Platform info block handed off to kernel entry point

Dual-boot strategy:
  GAIA installs a UEFI shim that chains to the original OS bootloader
  (Windows Boot Manager, GRUB, systemd-boot) without removing or modifying
  the existing OS. Non-destructive by design.

Secure Boot:
  GAIA will obtain Microsoft UEFI CA signing or operate under a user-enrolled
  MOK (Machine Owner Key) via shim — same mechanism as Ubuntu and Fedora.
  Automatic recovery: 3 consecutive boot failures trigger RECOVERY mode.
"""
from core.os_interface.bootloader.model import (
    BootMode,
    BootEntry,
    BootConfiguration,
    BootStage,
)
from core.os_interface.bootloader.manager import BootManager

__all__ = [
    "BootMode",
    "BootEntry",
    "BootConfiguration",
    "BootStage",
    "BootManager",
]
